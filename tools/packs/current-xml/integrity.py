"""Source-bound engineering admission. Receipts are evidence, never authority.

The caller supplies independently retained source and index SHA256 anchors. An
admitted reader is an in-process capability; serialized receipts cannot mint one.
This verifies index completeness, not publisher authenticity or source rights.
"""
import hashlib,itertools,json,os,pathlib,time

def verify(reader,source,source_sha256,index_sha256,seconds=180):
 A=reader.api;source=pathlib.Path(source);guard=A.Guard(min(seconds,180),reader.cancel);started=time.monotonic_ns();original=None;fds=[]
 def filehash(path):
  h=hashlib.sha256()
  with open(path,'rb') as f:
   while True:
    guard.check();b=f.read(65536)
    if not b:break
    h.update(b)
  return h.hexdigest()
 paths=[source/'index.sqlite',source/'receipt.json',reader.path/'index.sqlite',reader.path/'receipt.json',reader.path/'index-receipt.json']
 before={str(p.resolve()):A.version(p) for p in paths};samples=[A.sample('admission-start')]
 try:
  for p in paths:
   guard.check();fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW);fds.append(fd);A.need(A.version('/proc/self/fd/'+str(fd))==before[str(p.resolve())],'admission-fd')
  A.need(len(source_sha256)==64 and filehash(paths[0])==source_sha256,'admission-source-identity');A.need(len(index_sha256)==64 and filehash(paths[2])==index_sha256==reader.output_hash,'admission-index-identity');A.need(reader.index_receipt['input_sha256']==source_sha256,'admission-parent-identity')
  original=A.Reader(source);original.guard=guard;original.db.set_progress_handler(guard.sql,1000);reader.guard=guard
  for table,order in [('records','id'),('ledger','sequence'),('metadata','key')]:
   for left,right in itertools.zip_longest(original.db.execute('SELECT * FROM '+table+' ORDER BY '+order),reader.db.execute('SELECT * FROM '+table+' ORDER BY '+order)):
    guard.check();A.need(left==right,'source-record-correspondence')
  count=0;postings=0;transcript=hashlib.sha256();record_hashes=[]
  for ordinal,(rid,ident) in enumerate(original.db.execute("SELECT id,stable_id FROM records WHERE disposition='inspection-only' ORDER BY page,revision"),1):
   guard.check();r=original.inspect(ident);A.need(reader.db.execute('SELECT record_id,stable_id FROM search_order WHERE ordinal=?',(ordinal,)).fetchone()==(rid,ident),'source-order-correspondence')
   # Independent enumeration from original decoded bytes, not index term tables.
   keys=set()
   for field in ('title','text'):
    value=r[field]
    for i in range(max(0,len(value)-2)):
     if i%4096==0:guard.check()
     keys.add(value[i:i+3].encode('utf-8'));A.need(len(keys)<=262144,'admission-gram-bound')
   for key in sorted(keys):
    guard.check();term=reader.db.execute('SELECT term FROM terms WHERE gram=?',(key,)).fetchone();A.need(term is not None,'source-missing-gram');A.need(reader.db.execute('SELECT 1 FROM postings WHERE term=? AND ordinal=?',(term[0],ordinal)).fetchone() is not None,'source-missing-posting');transcript.update(A.canonical([ordinal,key.hex()])+b'\n')
   count+=1;postings+=len(keys);record_hashes.append({'id':ident,'text_sha256':r['text_sha256'],'lexical_sha256':r['lexical_sha256'],'metadata_sha256':A.sha(A.canonical(r['metadata']))})
  A.need(reader.db.execute('SELECT count(*) FROM postings').fetchone()[0]==postings,'source-extra-posting');A.need(reader.db.execute('SELECT count(*) FROM terms WHERE frequency=0').fetchone()[0]==0,'source-extra-gram');A.need(reader.db.execute('SELECT count(*) FROM search_order').fetchone()[0]==count,'source-record-count');guard.check()
  hashes={str(p.resolve()):filehash(p) for p in paths};A.need(hashes[str(paths[0].resolve())]==source_sha256 and hashes[str(paths[2].resolve())]==index_sha256,'admission-content-changed')
  A.need(all(A.version(p)==before[str(p.resolve())] and A.version('/proc/self/fd/'+str(fd))==before[str(p.resolve())] for p,fd in zip(paths,fds)),'admission-version-changed');samples.append(A.sample('admission-complete',fds[0]));guard.check()
  # Only this successful verifier establishes a capability, tied to held FDs.
  reader._admission={'versions':before,'paths':paths,'fds':fds,'hashes':hashes};fds=[]
  return {'contract':'source-posting-completeness-v1','source_sha256':source_sha256,'index_sha256':index_sha256,'records':count,'postings':postings,'source_posting_sha256':transcript.hexdigest(),'record_hashes':record_hashes,'started_ns':started,'ended_ns':time.monotonic_ns(),'samples':samples,'versions':before,'hashes':hashes,'rights_admission':False}
 finally:
  if original is not None:original.close()
  for fd in fds:os.close(fd)

def expected_hits(A,rows,query,limit=20,after=0):
 """Independent full-source literal oracle; excluded from indexed query timing."""
 hits=[]
 for row in rows[after:]:
  for field in ('text','title'):
   at=row[field].find(query)
   if at<0:continue
   start=len(row[field][:at].encode('utf-16-le'))//2
   hits.append({'id':row['id'],'field':field,'start_utf16':start,'end_utf16':start+len(query.encode('utf-16-le'))//2,'quote':query,'quote_sha256':hashlib.sha256(query.encode()).hexdigest(),'source_text_sha256':hashlib.sha256(row['text'].encode()).hexdigest(),'admission':False});break
  if len(hits)==limit:break
 return hits

def validate_hits(A,hits,rows,query,limit=20,after=0):
 expected=expected_hits(A,rows,query,limit,after);A.need(len(hits)==len(expected),'hit-count')
 for h,e in zip(hits,expected):
  A.need(set(h)==set(e),'hit-shape')
  for key,guard in [('id','hit-source-id'),('field','hit-field'),('source_text_sha256','hit-source-hash'),('start_utf16','hit-original-range'),('end_utf16','hit-original-range'),('quote','hit-quote'),('quote_sha256','hit-quote'),('admission','hit-admission')]:A.need(h[key]==e[key],guard)
 return True
