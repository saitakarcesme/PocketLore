#!/usr/bin/env python3
"""Bounded original-wikitext inspection. No rendering or source admission API."""
import argparse,base64,bz2,datetime,hashlib,json,os,pathlib,re,resource,signal,sqlite3,sys,time,xml.parsers.expat as expat,zlib
FORMAT='pocketlore-original-wikitext-v1';URI='http://www.mediawiki.org/xml/export-0.11/'
LIMITS={'compressed':16*1024**2,'decoded':64*1024**2,'pages':256,'page':4*1024**2,'text':2*1024**2,'token':1024**2,'depth':32,'revisions':8,'retained':40*1024**2,'output':64*1024**2,'seconds':90,'chunk':16384}
class Refused(Exception):pass
class PrefixStop(Exception):pass
def need(ok,guard):
 if not ok:raise Refused(guard)
def canonical(d):return json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def version(p):
 s=os.stat(p);return dict(device=s.st_dev,inode=s.st_ino,size=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns)
def filehash(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(65536),b''):h.update(b)
 return h.hexdigest()
def atomic(p,d):
 p=pathlib.Path(p);tmp=p.with_name(p.name+'.tmp');tmp.write_bytes(canonical(d)+b'\n');os.replace(tmp,p)
def units(s):return len(s.encode('utf-16-le'))//2
def text_decode(raw):
 s=raw.decode('utf-8','strict');out=[]
 for part in re.split(r'(<!\[CDATA\[.*?\]\]>)',s,flags=re.S):
  if part.startswith('<![CDATA['):out.append(part[9:-3]);continue
  need('<' not in part,'text-markup')
  def entity(m):
   key=m[1];fixed={'amp':'&','lt':'<','gt':'>','quot':'"','apos':"'"}
   if key in fixed:return fixed[key]
   try:n=int(key[2:],16) if key.startswith('#x') else int(key[1:]) if key.startswith('#') else -1
   except ValueError:raise Refused('text-entity')
   need(n in [9,10,13] or 32<=n<=0xD7FF or 0xE000<=n<=0xFFFD or 0x10000<=n<=0x10FFFF,'text-entity');return chr(n)
  need(not re.search(r'&(?![^&;\s]+;)',part),'text-entity')
  out.append(re.sub(r'&([^&;\s]+);',entity,part))
 return ''.join(out)
def inflate(blob):
 d=zlib.decompressobj();b=d.decompress(blob,LIMITS['page']+1);need(len(b)<=LIMITS['page'] and d.eof and not d.unconsumed_tail and not d.unused_data,'capsule');return b

def sample(phase,fd=None):
 p=pathlib.Path('/proc/self');cg=(p/'cgroup').read_text();g=pathlib.Path('/sys/fs/cgroup')/cg.split('0::')[1].strip().lstrip('/');st=g.stat()
 d={'phase':phase,'monotonic_ns':time.monotonic_ns(),'pid':os.getpid(),'stat':(p/'stat').read_text(),'status':(p/'status').read_text(),'smaps_rollup':(p/'smaps_rollup').read_text(),'namespaces':{n:os.readlink(p/'ns'/n) for n in ['mnt','pid','user']},'cgroup':cg,'group_identity':{'path':str(g),'device':st.st_dev,'inode':st.st_ino},'kernel':{n:(g/n).read_text() for n in ['memory.current','memory.peak','memory.events','memory.swap.current','memory.max','memory.swap.max','cpu.max','cpu.stat','pids.max']},'cpu_seconds':time.process_time()}
 if fd is not None:d.update(fd=fd,fd_stat=version(p/'fd'/str(fd)),fdinfo=(p/'fdinfo'/str(fd)).read_text(),mountinfo=(p/'mountinfo').read_text())
 return d
class Guard:
 def __init__(self,seconds,cancel=lambda:False):self.start=time.monotonic();self.deadline=self.start+seconds;self.cancel=cancel
 def check(self):
  need(not self.cancel(),'cancelled');need(time.monotonic()<self.deadline,'deadline')
 def sql(self):
  try:self.check();return 0
  except Refused:return 1

def tag_end(data,pos):
 quote=None
 for i in range(pos,min(len(data),pos+8193)):
  c=data[i]
  if quote:
   if c==quote:quote=None
  elif c in [34,39]:quote=c
  elif c==62:return i+1
 raise Refused('start-tag-bound')

class Parser:
 def __init__(self,sink,guard,limits):
  self.sink=sink;self.guard=guard;self.limits=limits;self.buffer=b'';self.base=0;self.fed=0;self.stack=[];self.frames=[];self.page=None;self.revision=None;self.pages=0;self.last_complete=0;self.root=False;self.finished=False;self.site={}
  self.p=expat.ParserCreate(namespace_separator='|');self.p.StartElementHandler=self.start;self.p.EndElementHandler=self.end;self.p.CharacterDataHandler=self.chars
  self.p.StartDoctypeDeclHandler=lambda *a:(_ for _ in ()).throw(Refused('doctype'))
  self.p.EntityDeclHandler=lambda *a:(_ for _ in ()).throw(Refused('entity-declaration'))
  self.p.ExternalEntityRefHandler=lambda *a:(_ for _ in ()).throw(Refused('external-entity'))
  self.p.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
 def start(self,qualified,attrs):
  self.guard.check();need(qualified.startswith(URI+'|'),'xml-namespace');name=qualified.split('|')[-1]
  need(len(self.stack)<self.limits['depth'],'xml-depth');need(len(canonical(attrs))<=8192,'attributes')
  parent=self.stack[-1] if self.stack else None
  if self.page is not None:
   allowed={'page':{'title','ns','id','redirect','restrictions','revision'},'revision':{'id','parentid','timestamp','contributor','minor','comment','model','format','text','sha1','origin'},'contributor':{'username','id','ip'}}
   need(parent in allowed and name in allowed[parent],'unsupported-page-layout')
  self.stack.append(name);self.frames.append({'name':name,'attrs':attrs,'value':[],'size':0})
  if parent is None:need(name=='mediawiki' and attrs.get('version')=='0.11' and not self.root,'xml-schema');self.root=True
  if name=='page':
   need(parent=='mediawiki' and self.page is None,'page-nesting');self.page={'start':self.p.CurrentByteIndex,'fields':{},'revisions':[],'redirect':None}
  if self.page is not None:
   need(self.p.CurrentByteIndex-self.page['start']<=self.limits['page'],'page-bound')
   if name=='revision':
    need(parent=='page' and self.revision is None and len(self.page['revisions'])<self.limits['revisions'],'revision-bound');self.revision={'fields':{},'contributor':{},'text':None,'text_attrs':None,'start':self.p.CurrentByteIndex}
   if name=='redirect' and parent=='page':
    need(self.page['redirect'] is None,'duplicate-redirect');self.page['redirect']=dict(attrs)
   if name=='contributor' and self.revision is not None:
    need('contributor_attrs' not in self.revision,'duplicate-contributor');self.revision['contributor_attrs']=dict(attrs)
   if name=='text' and self.revision is not None:
    need(parent=='revision','unsupported-text-layout');need(self.revision['text_attrs'] is None,'duplicate-text')
    start=self.p.CurrentByteIndex;end=tag_end(self.buffer,start-self.base)+self.base
    self.revision.update(text_start=end,text_selfclosing=self.buffer[end-self.base-2:end-self.base]==b'/>',text_attrs=dict(attrs))
 def chars(self,s):
  self.guard.check()
  if not self.frames:return
  f=self.frames[-1];f['size']+=len(s.encode())
  need(f['size']<=(self.limits['text'] if f['name']=='text' else 65536),'field-bound')
  if f['name']!='text':f['value'].append(s)
 def end(self,qualified):
  self.guard.check();name=qualified.split('|')[-1];f=self.frames.pop();need(self.stack.pop()==name,'xml-stack');parent=self.stack[-1] if self.stack else None;value=''.join(f['value'])
  if self.page is not None:
   need(self.p.CurrentByteIndex-self.page['start']<=self.limits['page'],'page-bound')
   if name=='text' and self.revision is not None:
    rev=self.revision;a=rev['text_start'];b=a if rev['text_selfclosing'] else self.p.CurrentByteIndex
    need(0<=a-self.base<=b-self.base<=len(self.buffer),'text-byte-range');lexical=self.buffer[a-self.base:b-self.base];need(len(lexical)<=self.limits['page'],'text-lexical-bound')
    body=text_decode(lexical);need(len(body.encode())<=self.limits['text'],'text-bound');rev.update(text=lexical,text_range=[a,b],body=body)
   elif parent=='contributor' and self.revision is not None:
    need(name not in self.revision['contributor'],'duplicate-contributor-field');self.revision['contributor'][name]={'value':value,'attrs':f['attrs']}
   elif parent=='revision' and self.revision is not None and name not in ['text','contributor']:
    need(name not in self.revision['fields'],'duplicate-revision-field');self.revision['fields'][name]={'value':value,'attrs':f['attrs']}
   elif parent=='page' and name not in ['revision','redirect']:
    need(name not in self.page['fields'],'duplicate-page-field');self.page['fields'][name]={'value':value,'attrs':f['attrs']}
   if name=='revision':self.page['revisions'].append(self.revision);self.revision=None
   if name=='page':
    end=self.p.CurrentByteIndex+len('</page>') # qualified closing token can have a prefix
    end=tag_end(self.buffer,self.p.CurrentByteIndex-self.base)+self.base
    self.page['end']=end;self.sink(self.page);self.pages+=1;self.last_complete=end;self.page=None
    if self.pages>=self.limits['pages']:raise PrefixStop('page-limit')
  elif parent=='siteinfo' and name in ['sitename','dbname','base','generator','case']:self.site[name]=value
  if name=='mediawiki':self.finished=True
 def feed(self,b,final=False):
  self.buffer+=b;self.fed+=len(b);self.p.Parse(b,final)
  keep=self.page['start'] if self.page else self.p.CurrentByteIndex
  need(self.fed-keep<=self.limits['page']+self.limits['chunk']*4,'parser-carry')
  need(self.fed-self.p.CurrentByteIndex<=self.limits['token'],'xml-token-bound')
  drop=keep-self.base;self.buffer=self.buffer[drop:];self.base=keep

SCHEMA='''
PRAGMA user_version=541;
CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE records(id INTEGER PRIMARY KEY,stable_id TEXT UNIQUE NOT NULL,page INTEGER NOT NULL,revision INTEGER NOT NULL,title TEXT NOT NULL,namespace INTEGER NOT NULL,metadata TEXT NOT NULL,lexical BLOB,text_sha TEXT,lexical_sha TEXT,bytes INTEGER,utf16 INTEGER,disposition TEXT NOT NULL,UNIQUE(page,revision));
CREATE INDEX source_page_revision ON records(page,revision);
CREATE INDEX source_title ON records(title,id);
CREATE TABLE ledger(sequence INTEGER PRIMARY KEY,page INTEGER,revision INTEGER,disposition TEXT NOT NULL,binding TEXT NOT NULL);
'''
def positive_int(s):need(bool(re.fullmatch('[1-9][0-9]{0,18}',s)) and int(s)<2**63,'numeric-id');return int(s)
def value(fields,k):need(k in fields,'missing-'+k);return fields[k]['value']
def build(source,out,source_id,limits=None,provisional=False,expected=None,cancel=lambda:False):
 lim=dict(LIMITS);lim.update(limits or {});need(all(0<v<=LIMITS[k] for k,v in lim.items()),'limits');need(bool(re.fullmatch('[0-9a-f]{64}',source_id)),'source-id')
 out=pathlib.Path(out);need(not out.exists(),'output-exists');out.mkdir(parents=True);guard=Guard(lim['seconds'],cancel)
 report={'format':FORMAT,'status':'FAILED','source_id':source_id,'admission':False,'rights':'unknown-unreviewed','source_format':'mediawiki-xml-wikitext','limits':lim,'start_ns':time.monotonic_ns(),'samples':[],'compressed_read_bytes':0,'decoded_bytes':0,'pages':0,'records':0,'ledger':0,'retained_lexical_bytes':0,'errors':[],'provisional_requested':provisional}
 fd=None;db=None;parser=None;compressed_hash=hashlib.sha256();phase='preflight'
 def checkpoint(label):
  guard.check();report['samples'].append(sample(label,fd));need(sum(len(canonical(s)) for s in report['samples'])<=4*1024**2,'sample-bound');need(sum(p.stat().st_size for p in out.iterdir() if p.is_file())<=lim['output'],'output-bound')
 try:
  checkpoint(phase);before=version(source);report['source_before']=before
  if expected:need(all(before[k]==v for k,v in expected.items()),'archive-identity')
  fd=os.open(source,os.O_RDONLY|os.O_NOFOLLOW);report['fd_before']=version('/proc/self/fd/'+str(fd));need(report['fd_before']==before,'source-open-race');checkpoint('opened')
  db=sqlite3.connect(out/'staging.sqlite');db.execute('PRAGMA cache_size=-2048');db.execute('PRAGMA mmap_size=0');db.execute('PRAGMA temp_store=MEMORY');db.execute('PRAGMA max_page_count=12288');db.executescript(SCHEMA);db.execute('BEGIN IMMEDIATE');db.set_progress_handler(guard.sql,1000)
  def store(page):
   guard.check();fields=page['fields'];pid=positive_int(value(fields,'id'));title=value(fields,'title');ns=value(fields,'ns');need(re.fullmatch('-?[0-9]{1,5}',ns) and -32768<=int(ns)<=32767,'namespace-id');need(title and len(title.encode())<=8192,'title-bound');need(page['revisions'],'missing-revision')
   for rev in page['revisions']:
    rf=rev['fields'];rid=positive_int(value(rf,'id'));timestamp=value(rf,'timestamp');need(re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ',timestamp),'timestamp');datetime.datetime.fromisoformat(timestamp.replace('Z','+00:00'))
    model=rf.get('model',{}).get('value');fmt=rf.get('format',{}).get('value');available=rev['text'] is not None and 'deleted' not in (rev['text_attrs'] or {})
    disposition='inspection-only' if available and model=='wikitext' and fmt=='text/x-wiki' else 'unavailable-text' if not available else 'unsupported-content-model'
    lexical=rev['text'];body=rev.get('body','');text_bytes=body.encode();meta={'source_id':source_id,'source_format':'mediawiki-xml-wikitext','format':FORMAT,'page_fields':fields,'revision_fields':rf,'page':pid,'revision':rid,'title':title,'namespace':int(ns),'redirect':page['redirect'],'contributor':rev['contributor'],'contributor_attrs':rev.get('contributor_attrs',{}),'text_attributes':rev['text_attrs'],'text_available':available,'text_xml_range':rev.get('text_range'),'page_xml_range':[page['start'],page['end']],'coordinate_system':'decoded-original-wikitext-utf16-preserved-line-endings','publisher_sha1_verified':False,'rights':'unknown-unreviewed','admission':False}
    # Equal page/revision requires all source metadata AND exact lexical text.
    content_meta={k:v for k,v in meta.items() if k not in ['page_xml_range','text_xml_range']};binding=sha(canonical(content_meta)+(lexical or b''))
    old=db.execute('SELECT metadata,lexical_sha FROM records WHERE page=? AND revision=?',(pid,rid)).fetchone()
    if old:
     om=json.loads(old[0]);need(om['binding']==binding,'revision-conflict');outcome='duplicate-equivalent'
    else:
     meta['binding']=binding;ls=sha(lexical) if lexical is not None else None;ts=sha(text_bytes) if available else None
     report['retained_lexical_bytes']+=len(lexical or b'');need(report['retained_lexical_bytes']<=lim['retained'],'retained-bound')
     db.execute('INSERT INTO records(stable_id,page,revision,title,namespace,metadata,lexical,text_sha,lexical_sha,bytes,utf16,disposition) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(source_id+':'+str(pid)+':'+str(rid),pid,rid,title,int(ns),canonical(meta).decode(),zlib.compress(lexical) if lexical is not None else None,ts,ls,len(text_bytes) if available else None,units(body) if available else None,disposition));report['records']+=1;outcome=disposition
    report['ledger']+=1;db.execute('INSERT INTO ledger VALUES(?,?,?,?,?)',(report['ledger'],pid,rid,outcome,binding))
   report['pages']+=1
   if report['pages']%32==0:checkpoint('pages-'+str(report['pages']))
  parser=Parser(store,guard,lim);decoder=bz2.BZ2Decompressor();pending=b'';report['members_completed']=0;reason=None;eof=False;member_started=False
  while True:
   guard.check()
   if decoder.eof:
    report['members_completed']+=1;pending=decoder.unused_data;decoder=bz2.BZ2Decompressor();member_started=False
   if decoder.needs_input:
    if not pending:
     remaining=lim['compressed']-report['compressed_read_bytes']
     if not remaining:reason='compressed-bound';break
     pending=os.read(fd,min(lim['chunk'],remaining))
     if not pending:eof=True;break
     compressed_hash.update(pending);report['compressed_read_bytes']+=len(pending)
    data=pending;pending=b''
   else:data=b''
   remaining=lim['decoded']-report['decoded_bytes']
   if not remaining:reason='decoded-bound';break
   member_started=member_started or bool(data)
   decoded=decoder.decompress(data,max_length=min(65536,remaining));report['decoded_bytes']+=len(decoded)
   try:parser.feed(decoded)
   except PrefixStop as e:reason=str(e);break
  if eof:
   # A finished member has already been counted and replaced by an empty decoder.
   need(decoder.eof or (report['members_completed']>0 and not member_started and parser.finished),'truncated-bzip')
   parser.feed(b'',True);need(parser.finished,'truncated-xml');reason='complete-input'
  else:need(provisional,'prefix-not-authorized')
  report.update(stop_reason=reason,xml_parsed_bytes=parser.p.CurrentByteIndex,last_complete_xml_end=parser.last_complete,discarded_incomplete_pages=int(parser.page is not None),unparsed_decoded_bytes=report['decoded_bytes']-parser.p.CurrentByteIndex,siteinfo=parser.site,status='PROVISIONAL_PREFIX' if not eof else 'COMPLETE_ENGINEERING_INPUT')
  checkpoint('parsed');report['source_after']=version(source);report['fd_after']=version('/proc/self/fd/'+str(fd));need(before==report['source_after']==report['fd_after'],'source-mutated')
  for k,v in {'format':FORMAT,'source_id':source_id,'status':report['status'],'rights':'unknown-unreviewed','admission':False,'source_format':'mediawiki-xml-wikitext','search':'bounded-literal-original-scan-no-FTS','records':report['records']}.items():db.execute('INSERT INTO metadata VALUES(?,?)',(k,json.dumps(v)))
  db.commit();need(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','sqlite-integrity');db.close();db=None;os.rename(out/'staging.sqlite',out/'index.sqlite');report['output_sha256']=filehash(out/'index.sqlite');checkpoint('committed')
 except (Exception,KeyboardInterrupt) as e:
  report['status']='FAILED';report['errors'].append(type(e).__name__+': '+str(e))
  if db is not None:
   db.rollback();db.close();db=None
  if parser:report.update(discarded_incomplete_pages=int(parser.page is not None),xml_parsed_bytes=parser.p.CurrentByteIndex,last_complete_xml_end=parser.last_complete)
 finally:
  if fd is not None:
   try:
    report['fd_after']=version('/proc/self/fd/'+str(fd));report['source_after']=version(source)
   except OSError as e:report['status']='FAILED';report['errors'].append('final-source: '+str(e))
   finally:os.close(fd)
  report['compressed_prefix_sha256']=compressed_hash.hexdigest();report['end_ns']=time.monotonic_ns();report['samples'].append(sample('closed'));report['storage']={p.name:{'logical':p.stat().st_size,'allocated':p.stat().st_blocks*512} for p in out.iterdir() if p.is_file()};report['storage_definitions']={'FTS_bytes':0,'provider_staging_bytes':0,'archive_copy_bytes':0,'original_archive_is_host_only':True,'update_rollback':'New immutable output; prior successful outputs untouched; failure staging retained, no promotion API.'};atomic(out/'receipt.json',report)
 return report

def rmax(receipt):return receipt['decoded_bytes']

class Reader:
 def __init__(self,path,expected_source=None,cancel=lambda:False):
  self.path=pathlib.Path(path);self.guard=Guard(10,cancel);self.receipt=json.loads((self.path/'receipt.json').read_text());r=self.receipt
  need(r['status'] in ['COMPLETE_ENGINEERING_INPUT','PROVISIONAL_PREFIX'] and not r['errors'],'failed-artifact');need((self.path/'index.sqlite').stat().st_size<=LIMITS['output'],'output-bound');need(filehash(self.path/'index.sqlite')==r['output_sha256'],'output-hash');need(expected_source is None or r['source_id']==expected_source,'reader-source')
  self.db=sqlite3.connect('file:'+str((self.path/'index.sqlite').resolve())+'?mode=ro&immutable=1',uri=True);self.db.execute('PRAGMA query_only=ON');self.db.execute('PRAGMA cache_size=-2048');self.db.execute('PRAGMA mmap_size=0');self.db.set_progress_handler(self.guard.sql,1000)
  need(self.db.execute('PRAGMA user_version').fetchone()[0]==541,'schema');self.meta={k:json.loads(v) for k,v in self.db.execute('SELECT * FROM metadata')};need(self.meta['format']==FORMAT and self.meta['source_format']=='mediawiki-xml-wikitext','format');need(self.meta['admission'] is False and self.meta['rights']=='unknown-unreviewed','license-promotion');need(self.meta['source_id']==r['source_id'],'reader-source');need(self.db.execute('SELECT count(*) FROM records').fetchone()[0]==r['records']==self.meta['records'],'record-count')
 def close(self):self.db.close()
 def inspect(self,stable_id):
  self.guard.check();row=self.db.execute('SELECT title,metadata,lexical,text_sha,lexical_sha,bytes,utf16,disposition FROM records WHERE stable_id=?',(stable_id,)).fetchone();need(row is not None,'record-missing');title,raw,blob,ts,ls,n,u,disposition=row;meta=json.loads(raw)
  need(meta['source_id']==self.meta['source_id'] and stable_id==meta['source_id']+':'+str(meta['page'])+':'+str(meta['revision']) and title==meta['title'],'record-source')
  need(meta['source_format']=='mediawiki-xml-wikitext' and meta['format']==FORMAT,'record-format');need(meta['admission'] is False and meta['rights']=='unknown-unreviewed','record-rights')
  lexical=inflate(blob) if blob is not None else None;need(lexical is None or sha(lexical)==ls,'lexical-hash');body=text_decode(lexical) if lexical is not None else None
  cm={k:v for k,v in meta.items() if k not in ['page_xml_range','text_xml_range','binding']}
  need(sha(canonical(cm)+(lexical or b''))==meta['binding'],'record-binding')
  pr=meta['page_xml_range'];tr=meta['text_xml_range'];need(len(pr)==2 and all(type(x)==int for x in pr) and 0<=pr[0]<pr[1]<=rmax(self.receipt),'record-range')
  if lexical is not None:need(isinstance(tr,list) and len(tr)==2 and all(type(x)==int for x in tr) and pr[0]<=tr[0]<=tr[1]<=pr[1] and tr[1]-tr[0]==len(lexical),'record-range')
  if meta['text_available']:need(body is not None and sha(body.encode())==ts and len(body.encode())==n and units(body)==u,'text-hash')
  return {'id':stable_id,'title':title,'metadata':meta,'text':body,'text_sha256':ts,'lexical_sha256':ls,'disposition':disposition}
 def search(self,query,limit=20):
  need(isinstance(query,str) and 0<len(query)<=256 and 0<limit<=20,'query-bound');self.guard.check();hits=[]
  # Literal, case-sensitive full-source scanning within a <=64MiB engineering shard.
  # No token normalization, stripped markup, regex or unbounded corpus promises.
  for (ident,) in self.db.execute("SELECT stable_id FROM records WHERE disposition='inspection-only' ORDER BY page,revision"):
   self.guard.check();record=self.inspect(ident)
   for field in ['text','title']:
    s=record[field];at=s.find(query)
    if at<0:continue
    a=units(s[:at]);b=a+units(query);hits.append({'id':ident,'field':field,'start_utf16':a,'end_utf16':b,'quote':query,'quote_sha256':sha(query.encode()),'source_text_sha256':record['text_sha256'],'admission':False});break
   if len(hits)>=limit:break
  return hits
 def resolve(self,hit):
  record=self.inspect(hit['id']);need(hit['field'] in ['text','title'],'hit-field');s=record[hit['field']];a,b=hit['start_utf16'],hit['end_utf16'];need(type(a)==type(b)==int and 0<=a<b<=units(s),'hit-range')
  try:q=s.encode('utf-16-le')[a*2:b*2].decode('utf-16-le')
  except UnicodeError:raise Refused('hit-surrogate')
  need(q==hit['quote'] and sha(q.encode())==hit['quote_sha256'] and record['text_sha256']==hit['source_text_sha256'],'hit-binding');return record
 def export(self,ident,directory):
  r=self.inspect(ident);need(r['metadata']['text_available'] and r['text'] is not None,'text-unavailable');out=pathlib.Path(directory);need(not out.exists(),'export-exists');out.mkdir(parents=True);b=r['text'].encode();need(sha(b)==r['text_sha256'],'export-hash');(out/'original.wikitext').write_bytes(b);atomic(out/'metadata.json',{k:v for k,v in r.items() if k!='text'});return {'bytes':len(b),'sha256':sha(b),'files':['original.wikitext','metadata.json']}

def main():
 p=argparse.ArgumentParser();s=p.add_subparsers(dest='command',required=True)
 i=s.add_parser('ingest');i.add_argument('input');i.add_argument('output');i.add_argument('--source-id',required=True);i.add_argument('--provisional-prefix',action='store_true')
 for cmd in ['search','inspect','export']:
  q=s.add_parser(cmd);q.add_argument('capsule');q.add_argument('value')
  if cmd=='export':q.add_argument('output')
 a=p.parse_args()
 if a.command=='ingest':r=build(a.input,a.output,a.source_id,provisional=a.provisional_prefix);print(json.dumps(r));return int(r['status']=='FAILED')
 r=Reader(a.capsule)
 try:print(json.dumps(r.search(a.value) if a.command=='search' else r.inspect(a.value) if a.command=='inspect' else r.export(a.value,a.output),ensure_ascii=False))
 finally:r.close()
 return 0
if __name__=='__main__':raise SystemExit(main())
