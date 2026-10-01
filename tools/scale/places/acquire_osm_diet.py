"""One global bulk dietary-tag query; no per-place requests or inferred values."""
import hashlib,json,pathlib,time,requests
from common import atomic_json
ROOT=pathlib.Path('/home/isa/PocketLore-control/scale-workers/places');dest=ROOT/'data/osm-global-diet.json'
query='[out:json][timeout:180][maxsize:536870912];(nwr["diet:vegan"];nwr["diet:vegetarian"];);out center meta;'
if dest.exists():raise SystemExit('Immutable bulk snapshot already exists')
url='https://overpass-api.de/api/interpreter';started=time.time()
try:
 with requests.post(url,data={'data':query},headers={'User-Agent':'PocketLoreResearch/1.0 (https://github.com/saitakarcesme/PocketLore)'},timeout=(30,240),stream=True) as r:
  meta={'url':url,'query':query,'status':r.status_code,'headers':dict(r.headers)};atomic_json(ROOT/'osm-global-request.json',meta)
  with dest.with_suffix('.json.partial').open('wb') as f:
   for b in r.iter_content(1024*1024):f.write(b)
  r.raise_for_status()
 p=dest.with_suffix('.json.partial')
 # JSON parsing is deferred to a streaming importer; HTTP 200 is not proof of complete data.
 p.rename(dest);meta.update(bytes=dest.stat().st_size,sha256=hashlib.file_digest(dest.open('rb'),'sha256').hexdigest(),seconds=time.time()-started,complete=False,completeness_requires='inspect osm3s timestamp and absence of Overpass runtime remark')
 atomic_json(dest.with_suffix('.receipt.json'),meta);print(meta)
except Exception as e:
 atomic_json(ROOT/'osm-global-failure.json',{'url':url,'query':query,'error':str(e),'seconds':time.time()-started});raise
