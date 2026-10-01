"""Run the unchanged frozen queries against source Parquet and installed-format blocks."""
import hashlib,json,pathlib,statistics,time
from common import atomic_json
from oracle import Oracle
import compact_search as reader
E=pathlib.Path('docs/evidence/scale/places');D=pathlib.Path('/home/isa/PocketLore-control/scale-workers/places/data');qbytes=(E/'queries-frozen.json').read_bytes();frozen=hashlib.sha256(qbytes).hexdigest();assert frozen==(E/'queries-frozen.sha256').read_text().split()[0]
objects=json.loads((E/'overture-objects.json').read_text());oracle=Oracle([D/pathlib.Path(o['Key']).name for o in objects]);paths=[D/f'compact-{i:02}.sqlite' for i in range(16)]
def canonical(v):
 if isinstance(v,dict):return {k:canonical(x) for k,x in v.items()}
 if isinstance(v,list):
  if v and all(isinstance(x,(tuple,list)) and len(x)==2 and isinstance(x[0],str) for x in v):return {k:canonical(x) for k,x in v}
  return [canonical(x) for x in v]
 return v
results=[];source_checks=[]
for q in json.loads(qbytes)['queries']:
 args=(q['lat'],q['lon'],q['radius_km'],q['category'],q['name'],q['diet']);start=time.perf_counter();expected=oracle.search(*args);tsource=time.perf_counter()-start;start=time.perf_counter();actual=reader.search(paths,*args);treader=time.perf_counter()-start;errors=[]
 if [r['id'] for r in expected]!=[r['id'] for r in actual]:errors.append('source/result identity or ordering mismatch')
 if any(r['distance_km']>q['radius_km'] for r in actual):errors.append('distance boundary')
 if q['kind']=='source' and expected and actual:
  original=oracle.source(expected[0]);stored=reader.source(actual[0]['shard'],actual[0]['block_id'],actual[0]['source_ordinal'],actual[0]['id'])
  matched=canonical(original)==canonical(stored['record']) and expected[0]['ordinal']==stored['row_ordinal'] and (expected[0]['lat'],expected[0]['lon'])==(stored['latitude'],stored['longitude'])
  if not matched:errors.append('raw source field/coordinate/ordinal mismatch')
  source_checks.append({'query':q['id'],'id':actual[0]['id'],'file':expected[0]['file'],'ordinal':expected[0]['ordinal'],'source_sha256':stored['provenance']['source_sha256'],'passed':matched})
 results.append({'query':q['id'],'city':q['city'],'kind':q['kind'],'source_ids':[r['id'] for r in expected],'reader_ids':[r['id'] for r in actual],'source_ms':tsource*1000,'reader_ms':treader*1000,'errors':errors});print(q['id'],q['city'],len(actual),errors,flush=True)
oracle.close();report={'frozen_sha256':frozen,'queries':results,'raw_record_source_checks':source_checks,'semantic_invariants_passed':all(not r['errors'] for r in results),'cities_with_any_positive':sorted({r['city'] for r in results if r['reader_ids']}),'positive_query_count':sum(bool(r['reader_ids']) for r in results),'median_reader_ms':statistics.median(r['reader_ms'] for r in results),'measurement':'LLMRig host; uncontrolled OS cache; source oracle first; no Android or rival acceptance','source_oracle':'original official Parquet boxes select candidates, WKB points and exact source categories determine matches; original row fields inspected'};atomic_json(E/'global-checks.json',report);print(json.dumps({k:v for k,v in report.items() if k not in ('queries','raw_record_source_checks')},indent=2))
if not report['semantic_invariants_passed']:raise SystemExit(1)
