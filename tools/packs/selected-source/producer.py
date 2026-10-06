#!/usr/bin/env python3
"""Owned, bounded, provisional selected-source producer. No admission authority."""
import argparse,traceback,fcntl,hashlib,importlib.util,json,math,os,resource,signal,sqlite3,sys,time,uuid,zlib,re
from pathlib import Path
HERE=Path(__file__).resolve();sys.path.insert(0,str(HERE.parents[1]/'complete-source'))
import production as safety
spec=importlib.util.spec_from_file_location('structure',HERE.parents[1]/'source-structure/produce.py');structure=importlib.util.module_from_spec(spec);spec.loader.exec_module(structure)
CUTOFF=1791269964;RANK_SHA='2f1e6f9171154d2b315188ed421ee6370146a31d5c1aac768d5267c2f953261e';RANK_SIZE=2644783104
FORMAT='pocketlore-selected-structure-v3-provisional'
SCHEMA='''
CREATE TABLE format(id INTEGER PRIMARY KEY CHECK(id=1),name TEXT NOT NULL);
INSERT INTO format VALUES(1,'pocketlore-selected-structure-v3-provisional');
CREATE TABLE progress(id INTEGER PRIMARY KEY CHECK(id=1),last INTEGER,chain TEXT);
INSERT INTO progress VALUES(1,-1,'');
CREATE TABLE originals(sequence INTEGER PRIMARY KEY,page INTEGER,revision INTEGER,member TEXT,offset INTEGER,bytes INTEGER,sha TEXT,license TEXT,title TEXT,error TEXT,binding TEXT,outcome TEXT);
CREATE INDEX original_revision ON originals(page,revision,sequence);
CREATE TABLE revision_bindings(page INTEGER,revision INTEGER,sha TEXT,equivalence TEXT,conflict INTEGER,invalid INTEGER,PRIMARY KEY(page,revision));
CREATE TABLE latest(page INTEGER PRIMARY KEY,revision INTEGER,sequence INTEGER,sha TEXT,blocked INTEGER);
CREATE TABLE selected(position INTEGER PRIMARY KEY,page INTEGER UNIQUE,revision INTEGER,sequence INTEGER,sha TEXT,views INTEGER,outcome TEXT);
CREATE TABLE capsules(sha TEXT PRIMARY KEY,kind TEXT,bytes INTEGER,z BLOB);
CREATE TABLE pieces(page INTEGER,revision INTEGER,kind TEXT,part INTEGER,start INTEGER,end INTEGER,sha TEXT,PRIMARY KEY(page,revision,kind,part));
CREATE TABLE articles(page INTEGER,revision INTEGER,sequence INTEGER,original_sha TEXT,html_sha TEXT,metadata TEXT,nodes INTEGER,status TEXT,PRIMARY KEY(page,revision));
CREATE TABLE contexts(id INTEGER PRIMARY KEY,page INTEGER,revision INTEGER,node INTEGER,parent INTEGER,start INTEGER,end INTEGER,fragment_sha TEXT,context_root INTEGER,heading INTEGER,disposition TEXT);
CREATE INDEX context_article ON contexts(page,revision,node);
CREATE TABLE texts(id INTEGER PRIMARY KEY,page INTEGER,revision INTEGER,node INTEGER,text TEXT);
CREATE INDEX text_article ON texts(page,revision,node);
CREATE TABLE query_contract(id INTEGER PRIMARY KEY CHECK(id=1),name TEXT NOT NULL);
INSERT INTO query_contract VALUES(1,'inline-units-v1');
CREATE TABLE query_units(id INTEGER PRIMARY KEY,page INTEGER,revision INTEGER,node INTEGER,kind TEXT,first_node INTEGER,last_node INTEGER,projection_sha TEXT);
CREATE INDEX query_article ON query_units(page,revision,id);
CREATE VIEW query_content AS SELECT q.id AS rowid,CASE WHEN q.kind='metadata-title' THEN json_extract(a.metadata,'$.name') ELSE (SELECT group_concat(text,'') FROM (SELECT text FROM texts WHERE page=q.page AND revision=q.revision AND node BETWEEN q.first_node AND q.last_node ORDER BY node)) END AS text FROM query_units q JOIN articles a ON a.page=q.page AND a.revision=q.revision;
CREATE VIRTUAL TABLE search USING fts4(text,content=query_content,tokenize=unicode61);
CREATE TABLE receipts(sequence INTEGER PRIMARY KEY,sha TEXT,outcome TEXT,detail TEXT);
'''
def require(x,m):
 if not x:raise ValueError(m)
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def open_source(path):
 d=sqlite3.connect('file:'+str(Path(path).resolve())+'?mode=ro',uri=True,timeout=.5);d.execute('PRAGMA query_only=ON');d.execute('PRAGMA cache_size=-2048');d.execute('PRAGMA mmap_size=0');d.execute('PRAGMA temp_store=FILE');return d
def metadata_value(value):
 if isinstance(value,bytes):return {'sqlite_blob_bytes':len(value),'sha256':sha(value)}
 return value
def binding(row):return sha(canonical([metadata_value(v) for v in row]))
def stage_identity(path):
 st=Path(path).stat();d=open_source(path)
 try:schema=d.execute("SELECT name,sql FROM sqlite_master WHERE name IN ('records','oversized') ORDER BY name").fetchall()
 finally:d.close()
 return {'device':st.st_dev,'inode':st.st_ino,'schema_sha256':sha(canonical(schema))}

def headers(stage,start,end,guard,limit=256):
 d=open_source(stage)
 try:
  d.set_progress_handler(guard.progress,1000)
  fields='sequence,page,revision,member,member_offset,raw_bytes,raw_sha256,license_json,title,metadata_error'
  # Refuse oversized metadata before materializing it; sequence remains represented.
  q="SELECT sequence,page,revision,CASE WHEN length(member)<=4096 THEN member ELSE '[oversized member]' END,member_offset,raw_bytes,CASE WHEN length(raw_sha256)<=64 THEN raw_sha256 ELSE '[oversized digest]' END,CASE WHEN length(license_json)<=65536 THEN license_json ELSE NULL END,CASE WHEN length(title)<=4096 THEN title ELSE NULL END,CASE WHEN metadata_error IS NULL OR length(metadata_error)<=4096 THEN metadata_error ELSE 'oversized metadata' END FROM records WHERE sequence>=? AND sequence<=?"
  args=[start,end]
  if d.execute("SELECT 1 FROM sqlite_master WHERE name='oversized'").fetchone():
   q+=" UNION ALL SELECT sequence,NULL,NULL,substr(member,1,4096),member_offset,raw_bytes,raw_sha256,NULL,NULL,'oversized original' FROM oversized WHERE sequence>=? AND sequence<=?";args += [start,end]
  q+=' ORDER BY sequence LIMIT ?';args.append(limit);rows=d.execute(q,args).fetchall();guard.check();return rows
 finally:d.close()
def metadata_valid(row):
 seq,page,rev,member,offset,size,digest,license,title,error=row
 if not (type(page) is int and page>0 and type(rev) is int and rev>0 and type(offset) is int and offset>=0 and type(size) is int and 0<size<=16000000):return False
 if not (isinstance(member,str) and 0<len(member)<=4096 and '\x00' not in member and isinstance(title,str) and 0<len(title)<=4096 and isinstance(license,str) and isinstance(digest,str) and re.fullmatch('[0-9a-f]{64}',digest) and error is None):return False
 try:
  lic=json.loads(license)
  return isinstance(lic,list) and len(lic)==1 and isinstance(lic[0],dict) and lic[0].get('identifier') in structure.LICENSES and lic[0].get('url')==structure.LICENSES[lic[0]['identifier']]
 except (TypeError,ValueError):return False

def equivalence(row):
 # Physical locations differ for duplicates; validate each and preserve every binding.
 return sha(canonical([metadata_value(row[i]) for i in (1,2,5,6,7,8,9)]))
def ingest(db,rows):
 last,chain=db.execute('SELECT last,chain FROM progress').fetchone()
 for row in rows:
  seq,page,rev,member,offset,size,digest,license,title,error=row;require(type(seq) is int and seq==last+1,'Missing/duplicate disposition sequence')
  valid=metadata_valid(row);outcome='metadata-indexed' if valid else 'metadata-unverified';b=binding(row)
  if type(page) is int and page>0 and type(rev) is int and rev>0:
   eq=equivalence(row);seen=db.execute('SELECT sha,equivalence,conflict,invalid FROM revision_bindings WHERE page=? AND revision=?',(page,rev)).fetchone()
   conflict=bool(seen and (seen[1]!=eq or seen[2]));invalid=not valid or bool(seen and seen[3])
   if seen is None:db.execute('INSERT INTO revision_bindings VALUES(?,?,?,?,0,?)',(page,rev,digest,eq,int(invalid)))
   else:db.execute('UPDATE revision_bindings SET conflict=?,invalid=? WHERE page=? AND revision=?',(int(conflict),int(invalid),page,rev))
   old=db.execute('SELECT revision,sequence,sha,blocked FROM latest WHERE page=?',(page,)).fetchone()
   if old is None or rev>old[0]:db.execute('INSERT OR REPLACE INTO latest VALUES(?,?,?,?,?)',(page,rev,seq,digest,int(invalid or conflict)))
   elif rev==old[0]:
    if seen and not conflict and valid:outcome='duplicate-revision'
    elif conflict:outcome='conflicting-revision'
    db.execute('UPDATE latest SET blocked=? WHERE page=?',(int(invalid or conflict),page))
   elif valid:outcome='conflicting-revision' if conflict else 'superseded-revision'
  db.execute('INSERT INTO originals VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(*row,b,outcome));last=seq;chain=sha(chain.encode()+b.encode())
 db.execute('UPDATE progress SET last=?,chain=? WHERE id=1',(last,chain));return last,chain

def body(stage,row,guard):
 # Exact sequence PK lookup, never a page scan. Admission precedes blob read/inflate.
 seq,page,rev,member,offset,size,digest,license,title,error=row
 require(metadata_valid(row),'original size/metadata refusal')
 d=open_source(stage)
 try:
  current=d.execute('SELECT sequence,page,revision,member,member_offset,raw_bytes,raw_sha256,license_json,title,metadata_error,length(original_zlib) FROM records WHERE sequence=?',(seq,)).fetchone();require(current is not None and tuple(current[:10])==tuple(row),'staged identity changed')
  require(0<current[10]<=16000000,'compressed record bound');guard.check();blob=d.execute('SELECT original_zlib FROM records WHERE sequence=?',(seq,)).fetchone()[0]
 finally:d.close()
 require(len(blob)==current[10],'compressed size changed');guard.check();z=zlib.decompressobj();raw=z.decompress(blob,size+1);require(len(raw)==size and z.eof and not z.unused_data and not z.unconsumed_tail and sha(raw)==digest,'original inflate/digest mismatch')
 data=json.loads(raw);require(type(data['identifier']) is int and type(data['version']['identifier']) is int and data['identifier']==page and data['version']['identifier']==rev and data['license']==json.loads(license) and data['name']==title,'original/stage metadata mismatch');guard.check();return raw

def put_piece(db,page,revision,kind,part,start,end,raw,guard):
 require(len(raw)<=262144,'capsule chunk bound');guard.check();digest=sha(raw);blob=zlib.compress(raw,3);db.execute('INSERT OR IGNORE INTO capsules VALUES(?,?,?,?)',(digest,kind,len(raw),blob));db.execute('INSERT INTO pieces VALUES(?,?,?,?,?,?,?)',(page,revision,kind,part,start,end,digest))
def query_units(db,page,rev,nodes,title,guard):
 # Disjoint inline runs reference canonical leaves, never copy ancestor bodies.
 # A semantic run is bounded by the existing 16MB original ceiling, not arbitrary leaf cuts.
 blocks={'body','div','section','article','aside','header','footer','nav','address','figure','figcaption','p','dd','dt','li','th','td','caption','pre','h1','h2','h3','h4','h5','h6'}
 current=[];owner=None;units=0;count=0
 def flush():
  nonlocal count
  if not current:return
  text=''.join(n[6] for n in current);require(len(text.encode())<=16000000,'Query unit exceeds original source bound')
  db.execute('INSERT INTO query_units(page,revision,node,kind,first_node,last_node,projection_sha) VALUES(?,?,?,?,?,?,?)',(page,rev,owner,'source-context',current[0][0],current[-1][0],sha(text.encode())))
  count+=1
 for n in nodes:
  guard.check()
  if n[7]=='omitted-unsafe' or n[2] in blocks | {'br','hr','img','image'}:
   flush();current=[];owner=None;units=0;continue
  if n[7] not in ('literal','entity') or not n[6]:continue
  ancestor=n[1];chosen=None
  while ancestor:
   up=nodes[ancestor-1]
   if up[2] in blocks:chosen=up[0];break
   ancestor=up[1]
  if chosen is None:chosen=n[1]
  width=structure.u16(n[6]);require(width<=4096,'Canonical leaf exceeds query bound')
  if current and owner!=chosen:
   flush();current=[];units=0
  owner=chosen;current.append(n);units+=width
 flush()
 db.execute('INSERT INTO query_units(page,revision,node,kind,first_node,last_node,projection_sha) VALUES(?,?,0,?,0,0,?)',(page,rev,'metadata-title',sha(title.encode())))
 return count+1

def transform(db,row,raw,guard):
 page,rev,source,nodes,meta=structure.inspect(raw);guard.check();html=source.encode();meta['format']=FORMAT;meta['original_stage']={'sequence':row[0],'member':row[3],'member_offset':row[4],'raw_sha256':row[6]};meta['context_policy']='v3 exact enclosing structure; independent rights/support required'
 db.execute('INSERT INTO articles VALUES(?,?,?,?,?,?,?,?)',(page,rev,row[0],sha(raw),sha(html),canonical(meta).decode(),len(nodes),'inspection-only'))
 for i in range(0,len(raw),32768):put_piece(db,page,rev,'original',i//32768,i,min(len(raw),i+32768),raw[i:i+32768],guard)
 offset=0
 for n,part in enumerate(structure.chunks(source,8192)):
  end=offset+structure.u16(part);put_piece(db,page,rev,'html',n,offset,end,part.encode(),guard);offset=end
 batch=[];size=0;chunk=0
 for node in nodes:
  b=canonical(node)
  if batch and (size+len(b)>131072 or len(batch)>=128):put_piece(db,page,rev,'structure',chunk,batch[0][0],batch[-1][0]+1,canonical(batch),guard);chunk+=1;batch=[];size=0
  batch.append(node);size+=len(b)
 if batch:put_piece(db,page,rev,'structure',chunk,batch[0][0],batch[-1][0]+1,canonical(batch),guard)
 # Canonical text is stored once per visible leaf. Contexts reference nodes/ranges.
 # Prefix sums avoid aggregating descendant strings for every nested candidate.
 source16=source.encode('utf-16-le');text_units=[0];unsafe=[0]
 for node in nodes:
  n,parent,tag,attrs,a,b,text,kind=node
  text_units.append(text_units[-1]+(structure.u16(text) if kind in ('literal','entity') else 0))
  unsafe.append(unsafe[-1]+int(kind=='omitted-unsafe' or tag in structure.Tree.UNSAFE or tag in {'img','image'}))
  if kind in ('literal','entity') and text:db.execute('INSERT INTO texts(page,revision,node,text) VALUES(?,?,?,?)',(page,rev,n,text))
 ends=[];stack=[]
 for i,node in enumerate(nodes):
  while stack and node[4]>=nodes[stack[-1]][5]:ends[stack.pop()]=i
  ends.append(len(nodes));stack.append(i)
 heading=0;contexts=0
 for node in nodes:
  n,parent,tag,attrs,a,b,text,kind=node
  if kind!='element':continue
  if tag in {'h1','h2','h3','h4','h5','h6'}:heading=n
  if tag not in {'body','div','section','article','aside','header','footer','nav','address','figure','figcaption','pre','p','dd','dt','li','th','td','caption','math','blockquote','q','h1','h2','h3','h4','h5','h6'}:continue
  guard.check();root=n;ancestor=parent;chain=[node]
  while ancestor:
   up=nodes[ancestor-1];chain.append(up);ancestor=up[1]
  tags={x[2] for x in chain}
  if tags & {'blockquote','q'}:
   # Reported speech needs attribution outside the quotation itself.
   root=next((x[0] for x in chain if x[2]=='section'),chain[-1][0])
  elif 'table' in tags:root=next(x[0] for x in reversed(chain) if x[2]=='table')
  elif 'math' in tags:
   root=next((x[0] for x in chain if x[2] in {'p','dd','dt','li','section'}),chain[-1][0])
  r=nodes[root-1];stop=ends[root-1];units=text_units[stop]-text_units[root-1]
  if not units:disposition='inspection-only:no-visible-text'
  elif unsafe[stop]>unsafe[root-1]:disposition='inspection-only:unsafe-or-image-context'
  elif r[5]-r[4]>65536 or units>32768:disposition='inspection-only:context-window-bound'
  else:disposition='structurally-bound:independent-rights-and-support-review-missing'
  fragment=source16[2*a:2*b].decode('utf-16-le').encode()
  db.execute('INSERT INTO contexts(page,revision,node,parent,start,end,fragment_sha,context_root,heading,disposition) VALUES(?,?,?,?,?,?,?,?,?,?)',(page,rev,n,parent,a,b,sha(fragment),root,heading,disposition));contexts+=1
 query_count=query_units(db,page,rev,nodes,meta['name'],guard)
 counts=dict(db.execute('SELECT disposition,count(*) FROM contexts WHERE page=? AND revision=? GROUP BY disposition',(page,rev)))
 return {'nodes':len(nodes),'contexts':contexts,'query_units':query_count,'context_dispositions':counts,'independently_eligible_contexts':counts.get('independently-reviewed-eligible',0),'license':meta['license'][0]['identifier']}

def file_hash(path,guard):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  while True:
   guard.check();b=f.read(1024*1024)
   if not b:return h.hexdigest()
   h.update(b)
def code_identity():return {str(p):sha(p.read_bytes()) for p in [HERE,Path(structure.__file__),Path(safety.__file__),Path(safety.c.__file__)]}
def receipt(out,state,guard,db=None):
 state['cgroup']=safety.cgroup_limits();state['phase']=guard.phase;state['updated_epoch']=time.time();state['memory']=safety.process_memory();state['storage']=safety.disk_sample(out,db);state['source_admission_established']=False;state['distribution_ready']=False;safety.sync_json(out/'status.json',state)
 with (out/'events.jsonl').open('ab') as f:f.write(canonical(state)+b'\n');f.flush();os.fsync(f.fileno())
def run(args):
 out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
 if not args.resume:out.mkdir() # Exclusive fresh creation; never overwrite a live output.
 require(out.is_dir(),'Resume output missing');fd=os.open(out/'.lock',os.O_CREAT|os.O_RDWR,0o600)
 try:
  try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise ValueError('Exclusive output owner active; no state changed')
  return owned(args,out)
 finally:os.close(fd)
def owned(args,out):
 require(0<args.seconds<=7200 and time.time()<args.cutoff<=CUTOFF,'finite cutoff policy');require(args.mode in ('engineering','production'),'mode');require(0<args.count<=3000000 and args.through>=0,'explicit prefix and selection count')
 limits=safety.apply_limits(args);guard=safety.Guard(args.seconds,args.cutoff,out);guard.install();db=None
 config={'code':code_identity(),'stage':str(Path(args.stage).resolve()),'stage_identity':stage_identity(args.stage),'ranking':str(Path(args.ranking).resolve()),'ranking_sha256':args.ranking_sha256,'through':args.through,'count':args.count,'mode':args.mode}
 previous=None
 if args.resume:
  previous=json.loads((out/'status.json').read_text());require(json.loads((out/'owner.json').read_text())==config,'Resume config/code mismatch');require(previous.get('resume_allowed') and previous['phase'] in ('metadata','materialize'),'Finalization replay denied')
 else:safety.sync_json(out/'owner.json',config)
 state={'run_id':uuid.uuid4().hex,'pid':os.getpid(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'start_ticks':Path('/proc/self/stat').read_text().split()[21],'status':'RUNNING','resume_allowed':True,'configuration':config,'limits':limits,'previous_run':previous.get('run_id') if previous else None,'workers':1}
 try:
  guard.phase='preflight';guard.check(write=True);state['cgroup']=safety.cgroup_limits();state['host_memory']={l.split(':')[0]:int(l.split()[1])*1024 for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith(('MemAvailable:','MemTotal:'))};require(state['host_memory']['MemAvailable']>=768*1024**2,'host memory reserve')
  if args.mode=='production':safety.verify_long_limits(state['cgroup']);require(args.ranking_sha256==RANK_SHA and Path(args.ranking).stat().st_size==RANK_SIZE,'production ranking pin')
  receipt(out,state,guard);require(file_hash(args.ranking,guard)==args.ranking_sha256,'ranking digest mismatch')
  db=sqlite3.connect(out/'index.sqlite',timeout=.5,uri=True);db.execute('PRAGMA cache_size=-2048');db.execute('PRAGMA mmap_size=0');db.execute('PRAGMA temp_store=FILE');db.execute('PRAGMA synchronous=FULL');db.set_progress_handler(guard.progress,1000)
  if not args.resume:db.executescript(SCHEMA);db.commit()
  guard.phase='metadata';last=db.execute('SELECT last FROM progress').fetchone()[0];receipt(out,state,guard,db)
  # Rebind all already committed metadata on explicit resume; snapshot handles remain short.
  if args.resume:
   for start in range(0,last+1,256):
    for row in headers(args.stage,start,min(last,start+255),guard):require(db.execute('SELECT binding FROM originals WHERE sequence=?',(row[0],)).fetchone()==(binding(row),),'resumed prefix changed')
  while last<args.through:
   rows=headers(args.stage,last+1,args.through,guard);require(rows,'Requested committed prefix incomplete');last,chain=ingest(db,rows);db.commit()
   if last%4096<256:state['committed_through']=last;receipt(out,state,guard,db)
  db.execute('ATTACH DATABASE ? AS ranking',('file:'+str(Path(args.ranking).resolve())+'?mode=ro',))
  if db.execute('SELECT count(*) FROM selected').fetchone()[0]==0:
   guard.phase='selection';state['resume_allowed']=False;receipt(out,state,guard,db)
   db.execute('INSERT INTO selected SELECT row_number() OVER (ORDER BY p.views DESC,l.page),l.page,l.revision,l.sequence,l.sha,p.views,\'pending\' FROM latest l JOIN ranking.priority p ON p.id=l.page WHERE l.blocked=0 AND p.full=1 ORDER BY p.views DESC,l.page LIMIT ?',(args.count,));db.commit()
  require(db.execute('SELECT count(*) FROM selected').fetchone()[0]==args.count,'Prefix lacks requested distinct selected originals; no filler')
  guard.phase='materialize';state['resume_allowed']=True;receipt(out,state,guard,db)
  for position in range(1,args.count+1):
   guard.check();chosen=db.execute('SELECT page,revision,sequence,sha,outcome FROM selected WHERE position=?',(position,)).fetchone()
   if chosen[4]!='pending':continue
   row=db.execute('SELECT sequence,page,revision,member,offset,bytes,sha,license,title,error FROM originals WHERE sequence=?',(chosen[2],)).fetchone()
   db.execute('BEGIN')
   try:
    raw=body(args.stage,row,guard)
    for duplicate in db.execute('SELECT sequence,page,revision,member,offset,bytes,sha,license,title,error FROM originals WHERE page=? AND revision=? AND sequence!=? ORDER BY sequence',(row[1],row[2],row[0])):
     guard.check();body(args.stage,duplicate,guard)
    db.execute('SAVEPOINT article');detail=transform(db,row,raw,guard);outcome='inspection-only';db.execute('RELEASE article')
   except (ValueError,KeyError,TypeError,json.JSONDecodeError,UnicodeError,zlib.error,RecursionError) as e:
    try:db.execute('ROLLBACK TO article');db.execute('RELEASE article')
    except sqlite3.OperationalError:pass
    detail={'error':str(e)};outcome='retained-refusal'
   db.execute('INSERT INTO receipts VALUES(?,?,?,?)',(row[0],row[6],outcome,canonical(detail).decode()));db.execute('UPDATE selected SET outcome=? WHERE position=?',(outcome,position));db.commit()
   if position%128==0:state['selected_processed']=position;receipt(out,state,guard,db)
  guard.phase='final-identity';state['resume_allowed']=False;receipt(out,state,guard,db)
  # Every disposition is rebound, not just successful selected articles.
  for start in range(0,args.through+1,256):
   rows=headers(args.stage,start,min(args.through,start+255),guard);require(len(rows)==min(256,args.through+1-start),'Final source coverage missing')
   for row in rows:require(db.execute('SELECT binding FROM originals WHERE sequence=?',(row[0],)).fetchone()==(binding(row),),'Final source metadata mutation')
  require(stage_identity(args.stage)==config['stage_identity'],'Final source file/schema identity changed');require(code_identity()==config['code'],'Final executed code identity changed');require(file_hash(args.ranking,guard)==args.ranking_sha256,'Final ranking mutation');guard.phase='fts';receipt(out,state,guard,db);db.execute("INSERT INTO search(search) VALUES('rebuild')");db.commit();db.execute("INSERT INTO search(search) VALUES('integrity-check')");require(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity');db.commit()
  state['counts']={t:db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ('originals','latest','selected','articles','contexts','texts','capsules','pieces','receipts')};state['outcomes']=dict(db.execute('SELECT outcome,count(*) FROM selected GROUP BY outcome'));state['context_dispositions']=dict(db.execute('SELECT disposition,count(*) FROM contexts GROUP BY disposition'));state['independently_eligible_full_articles']=db.execute("SELECT count(*) FROM articles WHERE status='independently-reviewed-full-original'").fetchone()[0];state['independently_eligible_contexts']=db.execute("SELECT count(*) FROM contexts WHERE disposition='independently-reviewed-eligible'").fetchone()[0];state['unresolved_original_identities']=db.execute("SELECT count(*) FROM originals WHERE page IS NULL OR revision IS NULL OR outcome='metadata-unverified'").fetchone()[0]
  state['component_bytes']=dict(db.execute('SELECT name,sum(pgsize) FROM dbstat GROUP BY name'));state['source_chain']=db.execute('SELECT chain FROM progress').fetchone()[0];state['query_plan']={'metadata':None,'body':None,'priority':db.execute('EXPLAIN QUERY PLAN SELECT * FROM ranking.priority WHERE id=?',(1,)).fetchall()}
  src=open_source(args.stage)
  try:
   state['query_plan']['metadata']=src.execute('EXPLAIN QUERY PLAN SELECT sequence,page FROM records WHERE sequence>=? AND sequence<=? ORDER BY sequence LIMIT 256',(0,args.through)).fetchall();state['query_plan']['body']=src.execute('EXPLAIN QUERY PLAN SELECT original_zlib FROM records WHERE sequence=?',(0,)).fetchall()
  finally:src.close()
  db.close();db=None;guard.phase='hash';receipt(out,state,guard);state['index_sha256']=file_hash(out/'index.sqlite',guard);state['status']='PROVISIONAL_PREFIX_COMPLETE';state['phase']='complete';guard.phase='complete';state['whole_source_identity_verified']=False;state['original_expected']={'bytes':140267048582,'md5':'2276dbb8db3bc93eabc90a505117e373','date':'March2025; older than rival August2025'};receipt(out,state,guard);return state
 except BaseException as e:
  if db is not None:
   try:db.set_progress_handler(None,0);db.rollback()
   except BaseException as cleanup_error:state['cleanup_error']=type(cleanup_error).__name__+': '+str(cleanup_error)
  state['status']='STOPPED_RETAINED';state['error']=type(e).__name__+': '+str(e);state['resume_allowed']=guard.phase in ('metadata','materialize');receipt(out,state,guard);raise
 finally:
  if db is not None:db.close()
  guard.close()
def main():
 p=argparse.ArgumentParser();p.add_argument('--mode',choices=['engineering','production'],required=True);p.add_argument('--stage',required=True);p.add_argument('--ranking',required=True);p.add_argument('--ranking-sha256',required=True);p.add_argument('--out',required=True);p.add_argument('--through',type=int,required=True);p.add_argument('--count',type=int,required=True);p.add_argument('--seconds',type=int,required=True);p.add_argument('--cutoff',type=float,required=True);p.add_argument('--resume',action='store_true');a=p.parse_args()
 try:print(json.dumps(run(a),indent=2));return 0
 except BaseException as e:traceback.print_exc();return 1
if __name__=='__main__':sys.exit(main())
