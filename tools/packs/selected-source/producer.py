#!/usr/bin/env python3
"""Owned, bounded, provisional selected-source producer. No admission authority."""
import argparse,fcntl,hashlib,importlib.util,json,math,os,resource,signal,sqlite3,sys,time,uuid,zlib
from pathlib import Path
HERE=Path(__file__).resolve();sys.path.insert(0,str(HERE.parents[1]/'complete-source'))
import production as safety
spec=importlib.util.spec_from_file_location('structure',HERE.parents[1]/'source-structure/produce.py');structure=importlib.util.module_from_spec(spec);spec.loader.exec_module(structure)
CUTOFF=1791269964;RANK_SHA='2f1e6f9171154d2b315188ed421ee6370146a31d5c1aac768d5267c2f953261e';RANK_SIZE=2644783104
FORMAT='pocketlore-selected-structure-v2-provisional'
SCHEMA='''
CREATE TABLE progress(id INTEGER PRIMARY KEY CHECK(id=1),last INTEGER,chain TEXT);
INSERT INTO progress VALUES(1,-1,'');
CREATE TABLE originals(sequence INTEGER PRIMARY KEY,page INTEGER,revision INTEGER,member TEXT,offset INTEGER,bytes INTEGER,sha TEXT,license TEXT,title TEXT,error TEXT,binding TEXT,outcome TEXT);
CREATE TABLE revision_bindings(page INTEGER,revision INTEGER,sha TEXT,conflict INTEGER,PRIMARY KEY(page,revision));
CREATE TABLE latest(page INTEGER PRIMARY KEY,revision INTEGER,sequence INTEGER,sha TEXT,blocked INTEGER);
CREATE TABLE selected(position INTEGER PRIMARY KEY,page INTEGER UNIQUE,revision INTEGER,sequence INTEGER,sha TEXT,views INTEGER,outcome TEXT);
CREATE TABLE capsules(sha TEXT PRIMARY KEY,kind TEXT,bytes INTEGER,z BLOB);
CREATE TABLE pieces(page INTEGER,revision INTEGER,kind TEXT,part INTEGER,start INTEGER,end INTEGER,sha TEXT,PRIMARY KEY(page,revision,kind,part));
CREATE TABLE articles(page INTEGER,revision INTEGER,sequence INTEGER,original_sha TEXT,html_sha TEXT,metadata TEXT,nodes INTEGER,status TEXT,PRIMARY KEY(page,revision));
CREATE TABLE contexts(id INTEGER PRIMARY KEY,page INTEGER,revision INTEGER,node INTEGER,start INTEGER,end INTEGER,title TEXT,text TEXT,fragment_sha TEXT,scope TEXT,disposition TEXT);
CREATE INDEX context_article ON contexts(page,revision,node);
CREATE VIRTUAL TABLE search USING fts4(title,text,content=contexts,tokenize=unicode61);
CREATE TABLE receipts(sequence INTEGER PRIMARY KEY,sha TEXT,outcome TEXT,detail TEXT);
'''
def require(x,m):
 if not x:raise ValueError(m)
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def open_source(path):
 d=sqlite3.connect('file:'+str(Path(path).resolve())+'?mode=ro',uri=True,timeout=.5);d.execute('PRAGMA query_only=ON');d.execute('PRAGMA cache_size=-2048');d.execute('PRAGMA mmap_size=0');d.execute('PRAGMA temp_store=FILE');return d
def binding(row):return sha(canonical(list(row)))
def headers(stage,start,end,guard,limit=256):
 d=open_source(stage)
 try:
  d.set_progress_handler(guard.progress,1000)
  fields='sequence,page,revision,member,member_offset,raw_bytes,raw_sha256,license_json,title,metadata_error'
  # Refuse oversized metadata before materializing it; sequence remains represented.
  q="SELECT sequence,page,revision,CASE WHEN length(member)<=4096 THEN member ELSE '[oversized member]' END,member_offset,raw_bytes,raw_sha256,CASE WHEN length(license_json)<=65536 THEN license_json ELSE NULL END,CASE WHEN length(title)<=4096 THEN title ELSE NULL END,CASE WHEN metadata_error IS NULL OR length(metadata_error)<=4096 THEN metadata_error ELSE 'oversized metadata' END FROM records WHERE sequence>=? AND sequence<=?"
  args=[start,end]
  if d.execute("SELECT 1 FROM sqlite_master WHERE name='oversized'").fetchone():
   q+=" UNION ALL SELECT sequence,NULL,NULL,substr(member,1,4096),member_offset,raw_bytes,raw_sha256,NULL,NULL,'oversized original' FROM oversized WHERE sequence>=? AND sequence<=?";args += [start,end]
  q+=' ORDER BY sequence LIMIT ?';args.append(limit);rows=d.execute(q,args).fetchall();guard.check();return rows
 finally:d.close()
def ingest(db,rows):
 last,chain=db.execute('SELECT last,chain FROM progress').fetchone()
 for row in rows:
  seq,page,rev,member,offset,size,digest,license,title,error=row;require(seq==last+1,'Missing/duplicate disposition sequence')
  valid=isinstance(page,int) and page>0 and isinstance(rev,int) and rev>0 and isinstance(digest,str) and len(digest)==64 and license is not None and title is not None and not error
  outcome='metadata-indexed' if valid else 'metadata-unverified';b=binding(row)
  if isinstance(page,int) and isinstance(rev,int):
   seen=db.execute('SELECT sha,conflict FROM revision_bindings WHERE page=? AND revision=?',(page,rev)).fetchone()
   conflict=bool(seen and (seen[0]!=digest or seen[1]))
   if seen is None:db.execute('INSERT INTO revision_bindings VALUES(?,?,?,0)',(page,rev,digest))
   elif conflict:db.execute('UPDATE revision_bindings SET conflict=1 WHERE page=? AND revision=?',(page,rev));db.execute('UPDATE latest SET blocked=1 WHERE page=?',(page,))
   old=db.execute('SELECT revision,sequence,sha,blocked FROM latest WHERE page=?',(page,)).fetchone()
   if old is None or rev>old[0]:db.execute('INSERT OR REPLACE INTO latest VALUES(?,?,?,?,?)',(page,rev,seq,digest,int(not valid or conflict) or (old[3] if old else 0)))
   elif rev==old[0]:
    if digest==old[2]:outcome='duplicate-revision'
    else:outcome='conflicting-revision';db.execute('UPDATE latest SET blocked=1 WHERE page=?',(page,))
   else:outcome='conflicting-revision' if conflict else 'superseded-revision'
  db.execute('INSERT INTO originals VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(*row,b,outcome));last=seq;chain=sha(chain.encode()+b.encode())
 db.execute('UPDATE progress SET last=?,chain=? WHERE id=1',(last,chain));return last,chain

def body(stage,row,guard):
 # Exact sequence PK lookup, never a page scan. Admission precedes blob read/inflate.
 seq,page,rev,member,offset,size,digest,license,title,error=row
 require(not error and 0<size<=16000000,'original size/metadata refusal')
 d=open_source(stage)
 try:
  current=d.execute('SELECT sequence,page,revision,member,member_offset,raw_bytes,raw_sha256,license_json,title,metadata_error,length(original_zlib) FROM records WHERE sequence=?',(seq,)).fetchone();require(current is not None and tuple(current[:10])==tuple(row),'staged identity changed')
  require(0<current[10]<=16000000,'compressed record bound');guard.check();blob=d.execute('SELECT original_zlib FROM records WHERE sequence=?',(seq,)).fetchone()[0]
 finally:d.close()
 require(len(blob)==current[10],'compressed size changed');guard.check();z=zlib.decompressobj();raw=z.decompress(blob,size+1);require(len(raw)==size and z.eof and not z.unused_data and not z.unconsumed_tail and sha(raw)==digest,'original inflate/digest mismatch')
 data=json.loads(raw);require(data['identifier']==page and data['version']['identifier']==rev and data['license']==json.loads(license) and data['name']==title,'original/stage metadata mismatch');guard.check();return raw

def put_piece(db,page,revision,kind,part,start,end,raw,guard):
 require(len(raw)<=262144,'capsule chunk bound');guard.check();digest=sha(raw);blob=zlib.compress(raw,3);db.execute('INSERT OR IGNORE INTO capsules VALUES(?,?,?,?)',(digest,kind,len(raw),blob));db.execute('INSERT INTO pieces VALUES(?,?,?,?,?,?,?)',(page,revision,kind,part,start,end,digest))
def transform(db,row,raw,guard):
 page,rev,source,nodes,meta=structure.inspect(raw);guard.check();html=source.encode();meta['format']=FORMAT;meta['original_stage']={'sequence':row[0],'member':row[3],'member_offset':row[4],'raw_sha256':row[6]};meta['independently_eligible_contexts']=0
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
 # General context rules: preserve full enclosing structure, never strip qualifiers or approve facts.
 contexts=0;source16=source.encode('utf-16-le')
 for node in nodes:
  n,parent,tag,attrs,a,b,text,kind=node
  if kind!='element' or tag not in {'p','dd','dt','li','th','td','caption','math','blockquote','q','h1','h2','h3','h4','h5','h6'}:continue
  guard.check();desc=[];restricted=set();count=0
  # Original tree preorder: stop at end; do not scan entire article per context.
  for child in range(n,len(nodes)):
   sub=nodes[child]
   if sub[4]>=b:break
   if sub[5]>b:continue
   if sub[2] in {'math','table','blockquote','q','script','style','svg','img','sup','sub'}:restricted.add(sub[2])
   if sub[7] in ('literal','entity'):desc.append(sub[6]);count+=len(sub[6])
   if count>32768:break
  if count>32768:continue
  value=''.join(desc)
  if not value.strip():continue
  ancestor=parent;scope=[]
  while ancestor:
   up=nodes[ancestor-1];scope.append([up[0],up[2],up[4],up[5]]);ancestor=up[1]
  all_tags={tag}|{s[1] for s in scope}|restricted
  blocked=all_tags & {'table','td','th','math','blockquote','q','script','style','svg','sup','sub'}
  disposition='inspection-context:'+','.join(sorted(blocked)) if blocked else 'reconstructible-prose; independent rights/support review pending'
  fragment=source16[2*a:2*b].decode('utf-16-le').encode();db.execute('INSERT INTO contexts(page,revision,node,start,end,title,text,fragment_sha,scope,disposition) VALUES(?,?,?,?,?,?,?,?,?,?)',(page,rev,n,a,b,meta['name'],value,sha(fragment),canonical(scope).decode(),disposition));contexts+=1
 return {'nodes':len(nodes),'contexts':contexts,'independently_eligible_contexts':0,'license':meta['license'][0]['identifier']}

def file_hash(path,guard):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  while True:
   guard.check();b=f.read(1024*1024)
   if not b:return h.hexdigest()
   h.update(b)
def code_identity():return {str(p):sha(p.read_bytes()) for p in [HERE,Path(structure.__file__),Path(safety.__file__),Path(safety.c.__file__)]}
def receipt(out,state,guard,db=None):
 state['phase']=guard.phase;state['updated_epoch']=time.time();state['memory']=safety.process_memory();state['storage']=safety.disk_sample(out,db);state['source_admission_established']=False;state['distribution_ready']=False;safety.sync_json(out/'status.json',state)
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
 config={'code':code_identity(),'stage':str(Path(args.stage).resolve()),'ranking':str(Path(args.ranking).resolve()),'ranking_sha256':args.ranking_sha256,'through':args.through,'count':args.count,'mode':args.mode}
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
  guard.phase='metadata';last=db.execute('SELECT last FROM progress').fetchone()[0]
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
    raw=body(args.stage,row,guard);db.execute('SAVEPOINT article');detail=transform(db,row,raw,guard);outcome='inspection-only';db.execute('RELEASE article')
   except (ValueError,KeyError,TypeError,json.JSONDecodeError,UnicodeError) as e:
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
  require(file_hash(args.ranking,guard)==args.ranking_sha256,'Final ranking mutation');guard.phase='fts';receipt(out,state,guard,db);db.execute("INSERT INTO search(search) VALUES('rebuild')");db.commit();db.execute("INSERT INTO search(search) VALUES('integrity-check')");require(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity');db.commit()
  state['counts']={t:db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ('originals','latest','selected','articles','contexts','capsules','pieces','receipts')};state['outcomes']=dict(db.execute('SELECT outcome,count(*) FROM selected GROUP BY outcome'));state['context_dispositions']=dict(db.execute('SELECT disposition,count(*) FROM contexts GROUP BY disposition'));state['independently_eligible_full_articles']=0;state['independently_eligible_contexts']=0
  state['component_bytes']=dict(db.execute('SELECT name,sum(pgsize) FROM dbstat GROUP BY name'));state['source_chain']=db.execute('SELECT chain FROM progress').fetchone()[0];state['query_plan']={'metadata':None,'body':None,'priority':db.execute('EXPLAIN QUERY PLAN SELECT * FROM ranking.priority WHERE id=?',(1,)).fetchall()}
  src=open_source(args.stage)
  try:
   state['query_plan']['metadata']=src.execute('EXPLAIN QUERY PLAN SELECT sequence,page FROM records WHERE sequence>=? AND sequence<=? ORDER BY sequence LIMIT 256',(0,args.through)).fetchall();state['query_plan']['body']=src.execute('EXPLAIN QUERY PLAN SELECT original_zlib FROM records WHERE sequence=?',(0,)).fetchall()
  finally:src.close()
  db.close();db=None;guard.phase='hash';receipt(out,state,guard);state['index_sha256']=file_hash(out/'index.sqlite',guard);state['status']='PROVISIONAL_PREFIX_COMPLETE';state['phase']='complete';guard.phase='complete';state['whole_source_identity_verified']=False;state['original_expected']={'bytes':140267048582,'md5':'2276dbb8db3bc93eabc90a505117e373','date':'March2025; older than rival August2025'};receipt(out,state,guard);return state
 except BaseException as e:
  if db is not None:
   try:db.rollback()
   except Exception:pass
  state['status']='STOPPED_RETAINED';state['error']=type(e).__name__+': '+str(e);state['resume_allowed']=guard.phase in ('metadata','materialize');receipt(out,state,guard);raise
 finally:
  if db is not None:db.close()
  guard.close()
def main():
 p=argparse.ArgumentParser();p.add_argument('--mode',choices=['engineering','production'],required=True);p.add_argument('--stage',required=True);p.add_argument('--ranking',required=True);p.add_argument('--ranking-sha256',required=True);p.add_argument('--out',required=True);p.add_argument('--through',type=int,required=True);p.add_argument('--count',type=int,required=True);p.add_argument('--seconds',type=int,required=True);p.add_argument('--cutoff',type=float,required=True);p.add_argument('--resume',action='store_true');a=p.parse_args()
 try:print(json.dumps(run(a),indent=2));return 0
 except BaseException as e:print(type(e).__name__+': '+str(e),file=sys.stderr);return 1
if __name__=='__main__':sys.exit(main())
