"""Offline bounded spatial search over SQLite shards, compatible with Android SQLite.
Snapshot status is never interpreted as live status; diet requires a separate source.
"""
import heapq,json,math,pathlib,sqlite3,uuid,zlib
from common import norm
R=6371.0088
def distance(lat,lon,a,b):
 p,q=math.radians(lat),math.radians(a);d=math.radians(a-lat);e=math.radians(b-lon)
 return 2*R*math.asin(min(1,math.sqrt(math.sin(d/2)**2+math.cos(p)*math.cos(q)*math.sin(e/2)**2)))
def search(paths,lat,lon,radius_km=10,category=None,name=None,diet=None,limit=20):
 if not(-90<=lat<=90 and -180<=lon<=180 and 0<radius_km<=100 and 1<=limit<=100):raise ValueError('Invalid bounded query')
 if diet is not None:return [] # Unknown is not dietary evidence; enrichments have a separate API.
 dy=math.degrees(radius_km/R);dl=180 if abs(lat)+dy>=90 else math.degrees(math.asin(min(1,math.sin(radius_km/R)/math.cos(math.radians(lat)))))
 low,high=lon-dl,lon+dl
 intervals=[(max(-180,low),min(180,high))]
 if low< -180:intervals.append((low+360,180))
 if high>180:intervals.append((-180,high-360))
 found={}
 for path in paths:
  db=sqlite3.connect('file:'+str(pathlib.Path(path).resolve())+'?mode=ro',uri=True);db.row_factory=sqlite3.Row;db.execute('PRAGMA cache_size=-8192')
  for left,right in intervals:
   sql='SELECT id,name,lat,lon,category,city,country,confidence,status,entity_key FROM place p WHERE gy BETWEEN ? AND ? AND gx BETWEEN ? AND ?'
   args=[math.floor((max(-90,lat-dy)+90)*100),math.floor((min(90,lat+dy)+90)*100),math.floor((left+180)*100),math.floor((right+180)*100)]
   if category:sql+=' AND EXISTS(SELECT 1 FROM category c WHERE c.place_id=p.id AND c.category=?)';args.append(category)
   if name:sql+=' AND name_key=?';args.append(norm(name))
   for row in db.execute(sql,args):
    d=distance(lat,lon,row['lat'],row['lon'])
    if d>radius_km:continue
    r=dict(row);key=r.pop('entity_key').hex();r['id']=str(uuid.UUID(bytes=r['id']));r.update(distance_km=d,shard=str(path),hours=None,diet=None,live_status=None)
    # Keep only bounded top candidates, merging exact entity groups deterministically.
    old=found.get(key)
    if old is None or r['id']<old['id']:found[key]=r
    if len(found)>limit*2:
     found=dict(sorted(found.items(),key=lambda x:(x[1]['distance_km'],x[1]['id']))[:limit])
  db.close()
 return sorted(found.values(),key=lambda r:(r['distance_km'],r['id']))[:limit]
def source(path,identity):
 db=sqlite3.connect('file:'+str(pathlib.Path(path).resolve())+'?mode=ro',uri=True)
 key=uuid.UUID(identity).bytes
 row=db.execute('SELECT detail,ordinal,entity_key FROM place WHERE id=?',(key,)).fetchone()
 if not row:db.close();return None
 meta={k:json.loads(v) for k,v in db.execute("SELECT key,value FROM progress WHERE key IN ('release','source','source_sha256','schema_version')")}
 meta['source_object_url']='https://overturemaps-us-west-2.s3.amazonaws.com/release/2026-09-23.1/theme=places/type=place/'+pathlib.Path(meta['source']).name
 siblings=[str(uuid.UUID(bytes=r[0])) for r in db.execute('SELECT id FROM place WHERE entity_key=? ORDER BY id LIMIT 100',(row[2],))]
 sibling_count=db.execute('SELECT count(*) FROM place WHERE entity_key=?',(row[2],)).fetchone()[0]
 conflicts=[{'row_ordinal':n,'record':json.loads(zlib.decompress(b))} for n,b in db.execute('SELECT ordinal,detail FROM conflict WHERE id=? ORDER BY ordinal LIMIT 20',(key,))]
 conflict_count=db.execute('SELECT count(*) FROM conflict WHERE id=?',(key,)).fetchone()[0];db.close()
 return {'record':json.loads(zlib.decompress(row[0])),'row_ordinal':row[1],'provenance':meta,'entity_sibling_ids':siblings,'entity_sibling_count':sibling_count,'id_conflicts':conflicts,'id_conflict_count':conflict_count}
