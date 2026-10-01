"""Pinned official OSM planet fallback after Overpass bulk failures; 16 MiB ranges."""
import hashlib,json,pathlib,time,requests
from common import atomic_json
ROOT=pathlib.Path('/home/isa/PocketLore-control/scale-workers/places');p=ROOT/'data/planet-260921.osm.pbf';part=p.with_suffix('.pbf.partial');url='https://planet.openstreetmap.org/pbf/planet-260921.osm.pbf';size=94983340321
if p.exists():raise SystemExit('Pinned complete planet already exists')
s=requests.Session();s.trust_env=False;start=time.time()
with part.open('ab') as f:
 offset=f.tell()
 while offset<size:
  end=min(size-1,offset+16*1024*1024-1)
  for attempt in range(3):
   try:
    r=s.get(url,headers={'Range':f'bytes={offset}-{end}','User-Agent':'PocketLoreResearch/1.0'},timeout=120);r.raise_for_status();assert r.status_code==206 and r.headers['Content-Range']==f'bytes {offset}-{end}/{size}';assert len(r.content)==end-offset+1
    f.write(r.content);f.flush();offset=end+1;print(offset,size,round(time.time()-start,2),flush=True);break
   except Exception as e:
    with (ROOT/'planet-failures.jsonl').open('a') as log:log.write(json.dumps({'offset':offset,'attempt':attempt,'error':str(e)})+'\n')
    if attempt==2:raise
    time.sleep(20*(attempt+1))
part.rename(p);atomic_json(p.with_suffix('.receipt.json'),{'url':url,'bytes':size,'sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),'retrieved_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'seconds':time.time()-start,'source_last_modified':'2026-09-24T19:07:31Z','source_version_id':'8jjxRIcMHOnnaHS.UE8R0oiyhSJc4hLK','license':'ODbL-1.0','attribution':'OpenStreetMap contributors'})
