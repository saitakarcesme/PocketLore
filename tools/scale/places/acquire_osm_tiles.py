"""Finite global bulk tag acquisition by 30x60 degree tiles, not per place.
Failed tiles remain explicit gaps; no response containing a runtime remark is accepted.
"""
import hashlib,json,pathlib,time,requests
from common import atomic_json
ROOT=pathlib.Path('/home/isa/PocketLore-control/scale-workers/places');OUT=ROOT/'data/osm-tiles';OUT.mkdir(exist_ok=True)
url='https://overpass-api.de/api/interpreter';timestamp='2026-10-01T09:33:42Z';inventory=[]
for south in range(-90,90,30):
 for west in range(-180,180,60):
  bounds=[south,west,south+30,west+60];key=f'{south+90:03}-{west+180:03}';dest=OUT/(key+'.json');receipt=dest.with_suffix('.receipt.json')
  if receipt.exists():inventory.append(json.loads(receipt.read_text()));continue
  bbox=','.join(map(str,bounds));query=f'[out:json][timeout:180][maxsize:536870912][date:"{timestamp}"];(nwr({bbox})["diet:vegan"];nwr({bbox})["diet:vegetarian"];nwr({bbox})["opening_hours"];);out center meta;'
  meta={'bounds':bounds,'query':query,'url':url,'requested_snapshot':timestamp,'complete':False};start=time.time()
  try:
   with requests.post(url,data={'data':query},headers={'User-Agent':'PocketLoreResearch/1.0 (https://github.com/saitakarcesme/PocketLore)'},stream=True,timeout=(30,240)) as r:
    meta.update(status=r.status_code,headers=dict(r.headers))
    with dest.with_suffix('.partial').open('wb') as f:
     for b in r.iter_content(1024*1024):f.write(b)
    r.raise_for_status()
   from osm_global import elements
   count=0
   for kind,value in elements(dest.with_suffix('.partial')):
    if kind=='element':count+=1
   dest.with_suffix('.partial').rename(dest);meta.update(complete=True,records=count,bytes=dest.stat().st_size,sha256=hashlib.file_digest(dest.open('rb'),'sha256').hexdigest())
  except Exception as e:
   meta['error']=str(e)
  meta['seconds']=time.time()-start;atomic_json(receipt,meta);inventory.append(meta);atomic_json(OUT/'inventory.json',inventory);print(meta,flush=True)
  if meta.get('status')==429:time.sleep(60)
  # Stop rather than hammer an unavailable service; preserve completed and failed tiles.
  if not meta['complete']:raise RuntimeError('Bulk tile failed; changed scope or external source required before retry')
  time.sleep(2)
