"""Frozen dietary queries verify explicit tags and source lineage, never live status."""
import json,pathlib,sqlite3,time,zlib
from common import atomic_json
from enrich import osm_search
E=pathlib.Path('docs/evidence/scale/places');D=pathlib.Path('/home/isa/PocketLore-control/scale-workers/places/data');db=sqlite3.connect('file:'+str(D/'osm-geometry.sqlite')+'?mode=ro',uri=True)
checks=[]
for q in json.loads((E/'queries-frozen.json').read_text())['queries']:
 if q['kind']!='diet':continue
 start=time.perf_counter();rows=osm_search(D/'osm-geometry.sqlite',q['lat'],q['lon'],q['radius_km'],'vegan');elapsed=time.perf_counter()-start
 records=[]
 for row in rows:
  assert row['vegan'] in ('yes','only')
  raw,snapshot=db.execute('SELECT raw,snapshot FROM osm WHERE type=? AND id=?',(row['type'],row['id'])).fetchone();record=json.loads(zlib.decompress(raw));assert record['tags']['diet:vegan']==row['vegan'];assert record['version']==row['version'];assert db.execute('SELECT 1 FROM snapshot WHERE sha256=?',(snapshot,)).fetchone()
  records.append({'type':row['type'],'id':row['id'],'version':row['version'],'snapshot':snapshot,'vegan':row['vegan'],'coordinate_basis':record['coordinate_basis']})
 checks.append({'query':q['id'],'city':q['city'],'count':len(rows),'records':records,'host_ms':elapsed*1000,'source_lineage_checked':True,'missing_result_means':'unknown or no located matching source, not real-world absence'})
report={'queries':checks,'positive_cities':sum(bool(x['count']) for x in checks),'scope':'all planet diet/hours entities retained; exact node coordinates and complete-way bounding-box centers; relation coordinates unknown','runtime':'LLMRig host; no Android acceptance','source_check_limit':'tags checked against retained source objects; planet receipt pins original bulk file; no separate second decoder run'};atomic_json(E/'global-diet-checks.json',report);print(json.dumps(report,indent=2));db.close()
