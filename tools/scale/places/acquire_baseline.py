"""Acquire a pinned published comparison database; never reuse its implementation."""
import hashlib,json,pathlib,time,requests
from common import atomic_json
D=pathlib.Path('/home/isa/PocketLore-control/scale-workers/places/data');metadata=json.loads((D/'androidlm-dataset-api.json').read_text());rev=metadata['sha'];info=next(x for x in metadata['siblings'] if x['rfilename']=='places.db');url=f'https://huggingface.co/datasets/rammingaway/androidlm-places/resolve/{rev}/places.db';dest=D/'androidlm-places.db';partial=dest.with_suffix('.partial')
if dest.exists():raise RuntimeError('Immutable baseline already exists')
s=requests.Session();s.headers['User-Agent']='PocketLore-frozen-coverage-comparison/1.0';start=time.time()
for attempt in range(3):
 offset=partial.stat().st_size if partial.exists() else 0
 try:
  with s.get(url,headers={'Range':f'bytes={offset}-'} if offset else {},stream=True,timeout=(30,120)) as response:
   response.raise_for_status()
   if offset:assert response.status_code==206 and response.headers['Content-Range'].startswith(f'bytes {offset}-')
   with partial.open('ab' if offset else 'xb') as stream:
    for block in response.iter_content(16*1024*1024):stream.write(block)
  assert partial.stat().st_size==info['size'];break
 except Exception as exc:
  with (D/'androidlm-acquisition-failures.jsonl').open('a') as out:out.write(json.dumps({'attempt':attempt+1,'offset':offset,'error':str(exc),'utc':time.time()})+'\n')
  if attempt==2:raise
  time.sleep(5*(2**attempt))
with partial.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
assert sha==info['lfs']['sha256'];partial.rename(dest)
receipt={'url':url,'revision':rev,'upstream_last_modified':metadata['lastModified'],'bytes':dest.stat().st_size,'sha256':sha,'official_lfs_sha256_matched':True,'retrieved_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'seconds':time.time()-start,'license':'ODbL-1.0; see exact dataset card','use':'comparison only; no rival source code copied or run'};atomic_json(dest.with_suffix('.receipt.json'),receipt);atomic_json('docs/evidence/scale/places/androidlm-places.receipt.json',receipt)
r=s.get(f'https://huggingface.co/datasets/rammingaway/androidlm-places/resolve/{rev}/README.md',timeout=60);r.raise_for_status();(D/'androidlm-dataset-card.md').write_bytes(r.content);atomic_json('docs/evidence/scale/places/androidlm-dataset-card-receipt.json',{'url':r.request.url,'revision':rev,'bytes':len(r.content),'sha256':hashlib.sha256(r.content).hexdigest(),'path':str(D/'androidlm-dataset-card.md')});print(json.dumps(receipt,indent=2))
