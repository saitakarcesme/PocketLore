"""Check every OSM source object and lookup row against preserved geometry staging."""
import json,pathlib,resource,sqlite3,time,zlib
from common import atomic_json
from compact_search import inflate
from enrich import osm_search
D=pathlib.Path('/home/isa/PocketLore-control/scale-workers/places/data');E=pathlib.Path('docs/evidence/scale/places');start=time.time();src=sqlite3.connect('file:'+str(D/'osm-geometry.sqlite')+'?mode=ro',uri=True);db=sqlite3.connect('file:'+str(D/'osm-compact.sqlite')+'?mode=ro',uri=True)
for conn in (src,db):conn.row_factory=sqlite3.Row;conn.execute('PRAGMA cache_size=-32768')
original=iter(src.execute('SELECT * FROM osm ORDER BY type,id'));index=iter(db.execute('SELECT * FROM osm ORDER BY type,id'));count=0
for block,payload,sha in db.execute('SELECT id,payload,sha256 FROM block ORDER BY id'):
 for slot,(lat,lon,raw) in enumerate(inflate(payload,sha)):
  a=next(original);b=next(index);assert b['block']==block and b['slot']==slot
  assert all(a[k]==b[k] for k in ['type','id','name_key','lat','lon','vegan','vegetarian']);assert (lat,lon)==(a['lat'],a['lon']);assert (raw['type'],raw['id'])==(a['type'],a['id'])
  assert json.dumps(raw,ensure_ascii=False,separators=(',',':')).encode()==zlib.decompress(a['raw']);assert a['version']==raw['version'];assert a['name']==raw['tags'].get('name');assert a['hours']==raw['tags'].get('opening_hours');count+=1
 if count%102400==0:print(count,round(time.time()-start,2),flush=True)
assert next(original,None) is None and next(index,None) is None;assert [tuple(r) for r in src.execute('SELECT * FROM snapshot')]==[tuple(r) for r in db.execute('SELECT * FROM snapshot')];src.close();db.close();queries=[]
for q in json.loads((E/'queries-frozen.json').read_text())['queries']:
 if q['kind']!='diet':continue
 expected=osm_search(D/'osm-geometry.sqlite',q['lat'],q['lon'],q['radius_km'],'vegan');t=time.perf_counter();actual=osm_search(D/'osm-compact.sqlite',q['lat'],q['lon'],q['radius_km'],'vegan');elapsed=time.perf_counter()-t;assert expected==actual
 queries.append({'query':q['id'],'city':q['city'],'records':len(actual),'source_ids':[str(r['type'])+'/'+str(r['id']) for r in actual],'compact_host_ms':elapsed*1000,'exact_fields_and_order_match':True})
report={'all_source_objects_checked':count,'lookup_fields_and_raw_source_bytes_equal':True,'snapshot_equal':True,'queries':queries,'positive_cities':sum(bool(q['records']) for q in queries),'seconds':time.time()-start,'max_rss_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'semantics':'all original source objects and coordinate values preserved; zero field or geographic pruning; object counts are not unique places','android_runtime_acceptance':False};atomic_json(E/'osm-compact-checks.json',report);print(json.dumps(report,indent=2))
