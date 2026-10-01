"""Measure published AndroidLM data with independent SQL, without rival code reuse."""
import fcntl,hashlib,json,math,pathlib,sqlite3,time
from common import atomic_json,norm
from oracle import Oracle
from search import distance,R
D=pathlib.Path('/home/isa/PocketLore-control/scale-workers/places/data');E=pathlib.Path('docs/evidence/scale/places');slot=(D.parent/'second-compute.lock').open('a');fcntl.flock(slot,fcntl.LOCK_EX);start=time.time();db=sqlite3.connect('file:'+str(D/'androidlm-places.db')+'?mode=ro',uri=True);db.execute('PRAGMA cache_size=-65536');db.execute('PRAGMA temp_store=FILE');db.create_function('name_norm',1,norm,deterministic=True)
kinds={r[0]:{'name':r[1],'parents':r[2].split(',')} for r in db.execute('SELECT * FROM kinds')};metadata=dict(db.execute('SELECT * FROM meta'))
base=json.loads((E/'androidlm-aggregate.json').read_text());assert base['receipt']['sha256']==json.loads((E/'androidlm-places.receipt.json').read_text())['sha256'];fill=base['nonempty_field_counts']
# Validate the inferred latitude row range of the published spatial-cell index.
# Rounding coordinates to 1e-5 degrees can move them by one 0.05-degree grid row.
wrong=db.execute('SELECT count(*) FROM places WHERE abs(cell/7200 - CAST((lat5/100000.0+90)*20 AS INTEGER))>1').fetchone()[0];assert wrong==0
objects=json.loads((E/'overture-objects.json').read_text());oracle=Oracle([D/pathlib.Path(o['Key']).name for o in objects]);rows=[]
frozen=hashlib.sha256((E/'queries-frozen.json').read_bytes()).hexdigest();assert frozen==(E/'queries-frozen.sha256').read_text().split()[0]
for q in json.loads((E/'queries-frozen.json').read_text())['queries']:
 if q['kind'] not in ('distance','category','absence'):continue
 lat,lon,radius=q['lat'],q['lon'],q['radius_km'];dy=math.degrees(radius/R);y0=max(0,math.floor((lat-dy+90)*20)-1);y1=min(3600,math.floor((lat+dy+90)*20)+1);found={};category=q['category']
 for identity,a,b,name,kind in db.execute('SELECT id,lat5,lon5,name,kind FROM places WHERE cell BETWEEN ? AND ?',(y0*7200,(y1+1)*7200-1)):
  if category and category!=kinds[kind]['name'] and category not in kinds[kind]['parents']:continue
  if q['name'] and norm(name)!=norm(q['name']):continue
  if distance(lat,lon,a/100000,b/100000)>radius:continue
  key=(norm(name),a,b,kind);found[key]=min(identity,found.get(key,identity))
 original=oracle.search(lat,lon,radius,category,q['name'],None,limit=1000000);assert len(original)<1000000,'Explicit comparison cap reached; count cannot be accepted'
 rows.append({'query':q['id'],'city':q['city'],'kind':q['kind'],'overture_exact_source_groups':len(original),'androidlm_exact_quantized_groups':len(found),'androidlm_category':category});print(q['id'],q['city'],len(original),len(found),flush=True)
oracle.close();db.close();atomic_json(E/'androidlm-city-coverage.json',{'queries':rows,'frozen_sha256':frozen,'baseline_latitude_grid_rows_outside_one_cell_tolerance':wrong,'seconds':time.time()-start,'scope':'independent data-only coverage queries; native coordinate precision; no application latency claim'})
