"""Acquire dated primary redirect table and title index; at most two HTTP requests."""
import concurrent.futures,hashlib,json,pathlib
from acquire import download,atomic
LANE=pathlib.Path('/home/isa/PocketLore-control/scale-workers/wiki');pin=json.loads(pathlib.Path('docs/evidence/scale/wiki/redirect-source-pin.json').read_text());items=[]
for job in ['redirecttable','articlesmultistreamdumprecombine']:
 for name,meta in pin['files'][job].items():items.append((name,meta))
def get(item):
 name,meta=item;path=LANE/'bulk'/name;url='https://dumps.wikimedia.org'+meta['url'];sha=download(url,path,size=meta['size']);h=hashlib.sha1()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 if h.hexdigest()!=meta['sha1']:raise RuntimeError('Primary SHA-1 mismatch: '+name)
 atomic(LANE/'receipts'/(name+'.verified.json'),{'url':url,'snapshot':pin['snapshot'],'sha1':h.hexdigest(),'sha256':sha,'bytes':path.stat().st_size});print(name,sha,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(get,items))
