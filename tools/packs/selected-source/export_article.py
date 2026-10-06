#!/usr/bin/env python3
"""Verified bounded v3-to-v1 inspection adapter; never grants source admission."""
import argparse,hashlib,importlib.util,json,pathlib,sys
HERE=pathlib.Path(__file__).resolve();sys.path.insert(0,str(HERE.parent))
from read import InspectionReader
spec=importlib.util.spec_from_file_location('structure',HERE.parents[1]/'source-structure/produce.py');structure=importlib.util.module_from_spec(spec);spec.loader.exec_module(structure)
def export(index,expected_sha,page,revision,out,cancelled=lambda:False):
 index=pathlib.Path(index)
 def file_identity():
  st=index.stat()
  if index.is_symlink() or any(pathlib.Path(str(index)+suffix).exists() for suffix in ('-wal','-journal')):raise ValueError('Unsealed source index or journal')
  return (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)
 def check_hash():
  h=hashlib.sha256()
  with index.open('rb') as f:
   while True:
    if cancelled():raise InterruptedError('Export cancelled')
    b=f.read(1048576)
    if not b:break
    h.update(b)
  if h.hexdigest()!=expected_sha:raise ValueError('Selected index identity mismatch')
 identity=file_identity();check_hash()
 reader=InspectionReader(index,cancelled);out=pathlib.Path(out)
 reader.db.execute('BEGIN')
 try:
  if file_identity()!=identity:raise ValueError('Selected index replaced before snapshot')
  if not reader.v3:raise ValueError('Adapter requires explicit v3 source')
  a=reader.db.execute('SELECT sequence,original_sha,html_sha,metadata,nodes FROM articles WHERE page=? AND revision=?',(page,revision)).fetchone()
  latest=reader.db.execute('SELECT revision,blocked FROM latest WHERE page=?',(page,)).fetchone()
  if not a or latest!=(revision,0):raise ValueError('Missing, stale or blocked article revision')
  raw=bytearray();part=0
  for p,start,end,digest,size,blob in reader.db.execute("SELECT p.part,p.start,p.end,c.sha,c.bytes,c.z FROM pieces p JOIN capsules c ON c.sha=p.sha WHERE p.page=? AND p.revision=? AND p.kind='original' ORDER BY p.part",(page,revision)):
   b=reader.inflate(digest,size,blob)
   if p!=part or start!=len(raw) or end!=start+len(b) or end>16000000:raise ValueError('Original range mismatch')
   raw.extend(b);part+=1
  if hashlib.sha256(raw).hexdigest()!=a[1]:raise ValueError('Original identity mismatch')
  pid,rev,html,nodes,meta=structure.inspect(bytes(raw));stored=json.loads(a[3])
  if (pid,rev)!=(page,revision) or hashlib.sha256(html.encode()).hexdigest()!=a[2] or len(nodes)!=a[4]:raise ValueError('Original article identity mismatch')
  for key,value in meta.items():
   if stored.get(key)!=value:raise ValueError('Article metadata mismatch: '+key)
  offset=0
  for chunk in structure.chunks(html,8192):
   end=offset+structure.u16(chunk)
   if reader.html_window(page,revision,offset,end)!=chunk:raise ValueError('HTML projection mismatch')
   offset=end
  for start in range(1,len(nodes)+1,128):
   if reader.nodes(page,revision,start,128)!=nodes[start-1:start+127]:raise ValueError('Structure mapping mismatch')
  reader.check();out.mkdir(parents=True,exist_ok=False);original=out/'verified-original.json';original.write_bytes(raw)
  # Existing exact v1 schema and cap, consumed by the real Android source import route.
  manifest=structure.build([(a[0],original)],out/'inspection-pack',cancelled)
  if manifest['articles']!=1:raise ValueError('Inspection packaging refused article')
  reader.check();check_hash()
  if file_identity()!=identity:raise ValueError('Selected index changed during export')
  receipt={'format':'verified-selected-v3-to-inspection-v1','input_index_sha256':expected_sha,'page':page,'revision':revision,'original_sha256':a[1],'html_sha256':a[2],'manifest':manifest,'source_admission_established':False,'android_execution':False}
  (out/'adapter.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt
 finally:reader.close()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('index');p.add_argument('sha256');p.add_argument('page',type=int);p.add_argument('revision',type=int);p.add_argument('out');a=p.parse_args();print(json.dumps(export(a.index,a.sha256,a.page,a.revision,a.out),indent=2))
