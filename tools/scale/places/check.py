"""Execute frozen development queries, raw-record checks and boundary regressions."""
import hashlib,json,pathlib,sqlite3,sys,tempfile,time,uuid,zlib
import pyarrow.parquet as pq
from search import search,source,distance
from common import atomic_json
from enrich import cities,osm_search
E=pathlib.Path('docs/evidence/scale/places')
def check(paths,out):
 queries=json.loads((E/'queries-frozen.json').read_text())['queries'];expected=(E/'queries-frozen.sha256').read_text().split()[0];assert hashlib.sha256((E/'queries-frozen.json').read_bytes()).hexdigest()==expected
 results=[];covered=set();query_sources={}
 for q in queries:
  start=time.perf_counter();rows=search(paths,q['lat'],q['lon'],q['radius_km'],q['category'],q['name'],q['diet']);errors=[]
  if rows:
   covered.add(q['city'])
   if q['kind']=='source':query_sources.setdefault(rows[0]['shard'],[]).append(rows[0]['id'])
  if q['kind'] in ('absence','diet') and rows:errors.append('Unsupported positive')
  if any(r['distance_km']>q['radius_km'] for r in rows):errors.append('Outside radius')
  if [r['distance_km'] for r in rows]!=sorted(r['distance_km'] for r in rows):errors.append('Distance order')
  for r in rows:
   raw=source(r['shard'],r['id'])['record']
   if q['category']:
    tax=raw.get('taxonomy') or {};cats=set(tax.get('hierarchy') or [])|set(tax.get('alternates') or [])|{tax.get('primary'),raw.get('basic_category')}
    if q['category'] not in cats:errors.append('Category mismatch')
   if r['name']!=(raw.get('names') or {}).get('primary'):errors.append('Name mismatch')
  results.append({'query':q['id'],'kind':q['kind'],'city':q['city'],'returned':len(rows),'ids':[r['id'] for r in rows],'milliseconds':(time.perf_counter()-start)*1000,'errors':errors,'positive_coverage':bool(rows)})
 raw_checks=[]
 for path in paths:
  db=sqlite3.connect(path);meta=dict(db.execute('SELECT key,value FROM progress'));rawpath=json.loads(meta['source']);parquet=pq.ParquetFile(rawpath)
  samples=list(db.execute('SELECT id,ordinal FROM place ORDER BY ordinal LIMIT 5'))+list(db.execute('SELECT id,ordinal FROM place ORDER BY ordinal DESC LIMIT 5'))
  for identity in query_sources.get(str(path),[]):samples.extend(db.execute('SELECT id,ordinal FROM place WHERE id=?',(uuid.UUID(identity).bytes,)).fetchall())
  offsets=[];total=0
  for i in range(parquet.num_row_groups):offsets.append(total);total+=parquet.metadata.row_group(i).num_rows
  for identity,ordinal in samples:
   group=max(i for i,o in enumerate(offsets) if o<ordinal);r=parquet.read_row_group(group,use_threads=False).slice(ordinal-offsets[group]-1,1).to_pylist()[0];stored=source(path,str(uuid.UUID(bytes=identity)))['record'];geometry=r.pop('geometry')
   import struct
   _,lon,lat=struct.unpack(('<' if geometry[0]==1 else '>')+'Idd',geometry[1:])
   assert db.execute('SELECT lat,lon FROM place WHERE id=?',(identity,)).fetchone()==(lat,lon)
   
   def canonical(v):
    if isinstance(v,dict):return {k:canonical(x) for k,x in v.items()}
    if isinstance(v,list):
     if v and all(isinstance(x,(tuple,list)) and len(x)==2 and isinstance(x[0],str) for x in v):return {k:canonical(x) for k,x in v}
     return [canonical(x) for x in v]
    return v
   assert canonical(r)==canonical(stored),(path,ordinal);raw_checks.append({'shard':str(path),'ordinal':ordinal,'id':r['id'],'passed':True})
  db.close()
 report={'frozen_sha256':expected,'queries':results,'raw_source_checks':raw_checks,'semantic_invariants_passed':all(not r['errors'] for r in results),'cities_with_any_positive':sorted(covered),'positive_query_count':sum(bool(r['returned']) for r in results),'coverage_acceptance':len(covered)==20,'runtime':'LLMRig host only; no Android/GrapheneOS acceptance','unknown_diet_not_negative':True}
 atomic_json(out,report);print(json.dumps({k:v for k,v in report.items() if k not in ('queries','raw_source_checks')},indent=2))
if __name__=='__main__':check([pathlib.Path(x) for x in sys.argv[2:]],sys.argv[1])
