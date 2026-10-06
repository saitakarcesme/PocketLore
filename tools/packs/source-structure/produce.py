#!/usr/bin/env python3
"""Separate inert, source-bound inspection format. Never grants research admission."""
import argparse, hashlib, html, json, sqlite3, sys, zipfile, time
from html.parser import HTMLParser
from pathlib import Path
FORMAT='pocketlore-structured-source-v1'
LICENSES={'CC-BY-SA-3.0':'https://creativecommons.org/licenses/by-sa/3.0/','CC-BY-SA-4.0':'https://creativecommons.org/licenses/by-sa/4.0/'}
SCHEMA=[
 'CREATE TABLE articles(id INTEGER PRIMARY KEY,title TEXT NOT NULL,metadata TEXT NOT NULL,original_sha TEXT NOT NULL,html_sha TEXT NOT NULL,original_bytes INTEGER NOT NULL,html_units INTEGER NOT NULL)',
 'CREATE TABLE nodes(id INTEGER PRIMARY KEY,article INTEGER NOT NULL,parent INTEGER NOT NULL,tag TEXT NOT NULL,attrs TEXT NOT NULL,start INTEGER NOT NULL,end INTEGER NOT NULL,text TEXT NOT NULL,kind TEXT NOT NULL)',
 'CREATE INDEX article_nodes ON nodes(article,id)',
 'CREATE INDEX parent_nodes ON nodes(article,parent,id)',
 'CREATE TABLE originals(article INTEGER NOT NULL,part INTEGER NOT NULL,bytes BLOB NOT NULL,sha TEXT NOT NULL,PRIMARY KEY(article,part))',
 'CREATE TABLE html_chunks(article INTEGER NOT NULL,start INTEGER NOT NULL,end INTEGER NOT NULL,text TEXT NOT NULL,sha TEXT NOT NULL,PRIMARY KEY(article,start))',
 'CREATE TABLE dispositions(sequence INTEGER PRIMARY KEY,page INTEGER,revision INTEGER,outcome TEXT NOT NULL,raw_sha TEXT NOT NULL)',
 'CREATE VIRTUAL TABLE search USING fts4(text,content=nodes,tokenize=unicode61)']
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def u16(s):return len(s.encode('utf-16-le'))//2
def require(b,m):
 if not b:raise ValueError(m)
def chunks(s,limit=4096):
 start=0;n=0
 for i,c in enumerate(s):
  width=2 if ord(c)>65535 else 1
  if n+width>limit:yield s[start:i];start=i;n=0
  n+=width
 if start<len(s):yield s[start:]
class Tree(HTMLParser):
 VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
 UNSAFE={'script','style','noscript','iframe','object','embed','svg','audio','video','head'}
 def __init__(self,source):
  super().__init__(convert_charrefs=False);self.source=source;self.lines=[0];self.units=[0];self.stack=[];self.rows=[];self.errors=[]
  for i,c in enumerate(source):
   self.units.append(self.units[-1]+(2 if ord(c)>65535 else 1))
   if c=='\n':self.lines.append(i+1)
 def pos(self):r,c=self.getpos();return self.lines[r-1]+c
 def add(self,tag,attrs,a,b,text,kind):
  require(len(self.rows)<100000,'node bound');require(len(canonical(attrs).encode())<=65536,'attribute bound')
  row=[len(self.rows)+1,self.stack[-1] if self.stack else 0,tag,canonical(attrs),self.units[a],self.units[b],text,kind];self.rows.append(row);return row[0]
 def handle_starttag(self,tag,attrs):
  p=self.pos();n=self.add(tag,dict(attrs),p,p+len(self.get_starttag_text()),'','element')
  if tag not in self.VOID:
   require(len(self.stack)<64,'depth bound');self.stack.append(n)
 def handle_startendtag(self,tag,attrs):
  self.handle_starttag(tag,attrs)
  if tag not in self.VOID:self.stack.pop()
 def handle_endtag(self,tag):
  p=self.pos();end=self.source.find('>',p);require(end>=p,'closing tag')
  if self.stack and self.rows[self.stack[-1]-1][2]==tag:self.rows[self.stack.pop()-1][5]=self.units[end+1]
  else:self.errors.append('unbalanced closing '+tag)
 def blocked(self):return any(self.rows[n-1][2] in self.UNSAFE for n in self.stack)
 def handle_data(self,data):
  p=self.pos()
  for part in chunks(data):
   self.add('#text',{},p,p+len(part),'' if self.blocked() else part,'omitted-unsafe' if self.blocked() else 'literal');p+=len(part)
 def entity(self,token):
  p=self.pos()
  if not self.source.startswith(token,p):token=token[:-1]
  require(self.source.startswith(token,p),'entity binding')
  self.add('#text',{},p,p+len(token),'' if self.blocked() else html.unescape(token),'omitted-unsafe' if self.blocked() else 'entity')
 def handle_entityref(self,n):self.entity('&'+n+';')
 def handle_charref(self,n):self.entity('&#'+n+';')
 def finish(self):
  self.feed(self.source);self.close()
  require(not self.stack and not self.errors,'unbalanced source markup')
  return self.rows

def inspect(raw):
 require(len(raw)<=16000000,'raw bound');d=json.loads(raw);lic=d.get('license',[])
 require(len(lic)==1 and lic[0].get('identifier') in LICENSES and lic[0].get('url')==LICENSES[lic[0]['identifier']],'exact license URI')
 require(d['namespace']['identifier']==0 and d['in_language']['identifier']=='en','namespace/language')
 source=d['article_body']['html'];require(len(source.encode())<=4000000,'HTML bound')
 page=int(d['identifier']);rev=int(d['version']['identifier']);require(page>0 and rev>0,'page/revision')
 require(str(rev) in source[:2048],'HTML revision missing')
 tree=Tree(source);rows=tree.finish()
 require(any(r[2]=='meta' and json.loads(r[3]).get('property')=='mw:pageId' and json.loads(r[3]).get('content')==str(page) for r in rows),'HTML page identity')
 require(any(r[2]=='html' and json.loads(r[3]).get('about','').endswith('/'+str(rev)) for r in rows),'HTML revision identity')
 meta={k:d[k] for k in ('name','identifier','date_modified','version','url','license')}
 meta.update(history=d['url']+'?action=history',revision_url='https://en.wikipedia.org/w/index.php?oldid='+str(rev),source_admission_established=False,warning='Original source inspection only. No independent rights, factual support or currentness clearance.',projection='Inert structure; original JSON and HTML available offline; unsafe content is not executed.')
 return page,rev,source,rows,meta

def build(inputs,out,cancelled=lambda:False):
 def check():
  if cancelled():raise InterruptedError('Source packaging cancelled')
 check()
 out=Path(out);require(not out.exists(),'immutable output already exists');out.mkdir(parents=True);db=sqlite3.connect(out/'index.sqlite');db.execute('PRAGMA user_version=523');db.execute('PRAGMA cache_size=-4096');db.execute('PRAGMA mmap_size=0')
 for sql in SCHEMA:db.execute(sql)
 try:
  dispositions=[];latest={}
  # Engineering inputs only: production latest/importance selection is a separate unqualified prerequisite.
  for seq,path in inputs:
   check()
   require(Path(path).stat().st_size<=16000000,'original file bound');raw=Path(path).read_bytes();page=rev=None
   try:
    d=json.loads(raw);page=int(d['identifier']);rev=int(d['version']['identifier'])
    old=latest.get(page)
    if old and rev<old[0]:outcome='superseded';dispositions.append((seq,page,rev,outcome,sha(raw)));continue
    if old and rev==old[0]:
     require(sha(raw)==old[1],'conflicting equal revision');dispositions.append((seq,page,rev,'duplicate',sha(raw)));continue
    if old:
     for table in ('nodes','originals','html_chunks'):db.execute('DELETE FROM '+table+' WHERE article=?',(page,))
     db.execute('DELETE FROM articles WHERE id=?',(page,))
    latest[page]=(rev,sha(raw))
    page,rev,source,rows,meta=inspect(raw)
    db.execute('INSERT INTO articles VALUES(?,?,?,?,?,?,?)',(page,meta['name'],canonical(meta),sha(raw),sha(source.encode()),len(raw),u16(source)))
    base=db.execute('SELECT coalesce(max(id),0) FROM nodes').fetchone()[0]
    for n,parent,tag,attrs,a,b,text,kind in rows:check();db.execute('INSERT INTO nodes VALUES(?,?,?,?,?,?,?,?,?)',(base+n,page,base+parent if parent else 0,tag,attrs,a,b,text,kind))
    for i in range(0,len(raw),32768):check();piece=raw[i:i+32768];db.execute('INSERT INTO originals VALUES(?,?,?,?)',(page,i//32768,piece,sha(piece)))
    offset=0
    for piece in chunks(source,8192):check();end=offset+u16(piece);db.execute('INSERT INTO html_chunks VALUES(?,?,?,?,?)',(page,offset,end,piece,sha(piece.encode())));offset=end
    outcome='inspection-only'
   except InterruptedError:db.close();raise
   except Exception as e:
    outcome='retained-refusal:'+str(e)
    if page is not None:
     for table in ('nodes','originals','html_chunks'):db.execute('DELETE FROM '+table+' WHERE article=?',(page,))
     db.execute('DELETE FROM articles WHERE id=?',(page,))
   dispositions.append((seq,page,rev,outcome,sha(raw)));db.execute('INSERT INTO dispositions VALUES(?,?,?,?,?)',dispositions[-1]);db.commit()
  check()
  db.set_progress_handler(lambda:1 if cancelled() else 0,1000)
  # Retain duplicate/superseded ledger rows too.
  for row in dispositions:db.execute('INSERT OR IGNORE INTO dispositions VALUES(?,?,?,?,?)',row)
  db.execute("INSERT INTO search(search) VALUES('rebuild')");db.commit();require(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','integrity')
  count=db.execute('SELECT count(*) FROM articles').fetchone()[0];nodes=db.execute('SELECT count(*) FROM nodes').fetchone()[0];schema=db.execute('SELECT name,sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY name').fetchall();db.close()
  require((out/'index.sqlite').stat().st_size<=67108864,'shard size bound; retained incomplete output');rawdb=(out/'index.sqlite').read_bytes();manifest={'format':FORMAT,'schema_version':523,'source_admission_established':False,'articles':count,'nodes':nodes,'db_bytes':len(rawdb),'db_sha256':sha(rawdb),'schema':schema,'input_records':len(inputs),'dispositions':dispositions,'license_policy':'Exact per-original URI retained; inspection-only, not independent rights clearance','limits':{'db_bytes':67108864,'node_units':4096,'html_window_units':8192,'depth':64},'producer_sha256':sha(Path(__file__).read_bytes()),'licenses':{k:sha((Path(__file__).resolve().parents[2]/'scale/wiki'/ (k+'.txt')).read_bytes()) for k in LICENSES}}
  (out/'manifest.json').write_text(canonical(manifest))
  with zipfile.ZipFile(out/'sources.plsource','w',compression=zipfile.ZIP_DEFLATED) as z:
   files=[(out/'manifest.json','manifest.json'),(out/'index.sqlite','index.sqlite')]+[(Path(__file__).resolve().parents[2]/'scale/wiki'/(k+'.txt'),k+'.txt') for k in LICENSES]
   for path,name in files:
    with path.open('rb') as source,z.open(name,'w') as target:
     while True:
      check();chunk=source.read(65536)
      if not chunk:break
      target.write(chunk)
  check();return manifest
 finally:db.close()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--packet',required=True);p.add_argument('--out',required=True);a=p.parse_args();packet=Path(a.packet);m=json.loads((packet/'manifest.json').read_text())
 for n,v in m.items():require(sha((packet/n).read_bytes())==v['sha256'],'input packet changed')
 print(canonical(build([(n,packet/f'original-{n}.json') for n in (2956,30000,100000,200000)],a.out)))
