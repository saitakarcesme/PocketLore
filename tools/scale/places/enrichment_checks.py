"""Exercise actual offline source-preserving candidate enrichment on frozen cities."""
import json,pathlib,sys,time
from catalog import Catalog
from common import atomic_json,norm
from search import distance
D=pathlib.Path('/home/isa/PocketLore-control/scale-workers/places/data');E=pathlib.Path('docs/evidence/scale/places');catalog=Catalog([D/f'compact-{i:02}.sqlite' for i in range(16)],D/'cities.sqlite',pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else D/'osm-geometry.sqlite',D/'wikivoyage.sqlite');checks=[]
for q in json.loads((E/'queries-frozen.json').read_text())['queries']:
 if q['kind']!='source':continue
 start=time.perf_counter();result=catalog.nearby(q['lat'],q['lon'],q['radius_km']);examples=[];matched=0;candidates=0
 for row in result['snapshot_results']:
  assert row['hours'] is None and row['diet'] is None and row['live_status'] is None
  if row['osm_candidate_sources']:matched+=1
  for candidate in row['osm_candidate_sources']:
   assert norm(candidate['name'])==norm(row['name']) and distance(row['lat'],row['lon'],candidate['lat'],candidate['lon'])<=.05;raw=json.loads(candidate['raw']);assert raw['tags'].get('opening_hours')==candidate['hours'];assert raw['tags'].get('diet:vegan')==candidate['vegan'];assert 'unconfirmed' in candidate['match_status'];candidates+=1
   if len(examples)<3:examples.append({'overture_id':row['id'],'osm_type':candidate['type'],'osm_id':candidate['id'],'osm_version':candidate['version'],'hours':candidate['hours'],'vegan':candidate['vegan'],'match_status':candidate['match_status']})
 travel=catalog.travel_nearby(q['lat'],q['lon'],q['radius_km'])
 if travel:
  original=catalog.travel_source(travel[0]['page']);assert travel[0]['raw'] in original['wikitext'];assert travel[0]['revision']==original['revision'];assert travel[0]['live_status'] is None
 checks.append({'travel_listing_occurrences':len(travel),'travel_first_source':{k:travel[0][k] for k in ['page','ordinal','revision','source_url']} if travel else None,'query':q['id'],'city':q['city'],'overture_results':len(result['snapshot_results']),'with_candidates':matched,'candidate_source_objects':candidates,'examples':examples,'host_ms':(time.perf_counter()-start)*1000});print(q['city'],matched,candidates,flush=True)
atomic_json(E/'enrichment-checks.json',{'checks':checks,'passed':True,'semantics':'on-demand offline SQLite candidate join; no per-record HTTP/LLM; source families never overwritten or summed as unique places; identity remains unconfirmed','android_runtime_acceptance':False})
