"""Run unchanged frozen questions against row and block readers, preserving mismatches."""
import hashlib,json,pathlib,statistics,time
from common import atomic_json
import search as row_reader
import compact_search as block_reader
E=pathlib.Path('docs/evidence/scale/places');D=pathlib.Path('/home/isa/PocketLore-control/scale-workers/places/data')
qbytes=(E/'queries-frozen.json').read_bytes();assert hashlib.sha256(qbytes).hexdigest()==(E/'queries-frozen.sha256').read_text().split()[0]
rows=[D/f'places-{i:02}.sqlite' for i in range(16)];blocks=[D/f'compact-{i:02}.sqlite' for i in range(16)]
def canonical(v):
 if isinstance(v,dict):return {k:canonical(x) for k,x in v.items()}
 if isinstance(v,list):
  if v and all(isinstance(x,(tuple,list)) and len(x)==2 and isinstance(x[0],str) for x in v):return {k:canonical(x) for k,x in v}
  return [canonical(x) for x in v]
 return v
results=[]
for q in json.loads(qbytes)['queries']:
 args=(q['lat'],q['lon'],q['radius_km'],q['category'],q['name'],q['diet']);start=time.perf_counter();a=row_reader.search(rows,*args);trow=time.perf_counter()-start;start=time.perf_counter();b=block_reader.search(blocks,*args);tblock=time.perf_counter()-start
 errors=[]
 if [r['id'] for r in a]!=[r['id'] for r in b]:errors.append('result identity/order mismatch')
 if q['kind']=='source' and a and b:
  x=row_reader.source(a[0]['shard'],a[0]['id']);y=block_reader.source(b[0]['shard'],b[0]['block_id'],b[0]['source_ordinal'],b[0]['id'])
  if canonical(x['record'])!=canonical(y['record']):errors.append('source field mismatch')
  if x['row_ordinal']!=y['row_ordinal'] or x['provenance']['source_sha256']!=y['provenance']['source_sha256']:errors.append('source provenance mismatch')
 results.append({'query':q['id'],'city':q['city'],'kind':q['kind'],'row_ids':[r['id'] for r in a],'compact_ids':[r['id'] for r in b],'row_ms':trow*1000,'compact_ms':tblock*1000,'errors':errors})
report={'frozen_sha256':hashlib.sha256(qbytes).hexdigest(),'queries':results,'passed':all(not x['errors'] for x in results),'row_median_ms':statistics.median(x['row_ms'] for x in results),'compact_median_ms':statistics.median(x['compact_ms'] for x in results),'measurement':'LLMRig host; uncontrolled OS cache; row reader always first; not phone or rival acceptance'};atomic_json(E/'compact-checks.json',report);print(json.dumps({k:v for k,v in report.items() if k!='queries'},indent=2))
if not report['passed']:raise SystemExit(1)
