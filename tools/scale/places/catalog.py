"""Offline catalog facade, with source families kept explicitly separate."""
import json,math,pathlib,sqlite3,zlib
from search import distance
from compact_search import search,source,group_sources
from enrich import cities,osm_search,osm_candidates
class Catalog:
 def __init__(self,places,city_db,osm_db,travel_db):
  self.places=places;self.city_db=city_db;self.osm_db=osm_db;self.travel_db=travel_db
 def source_variants(self,row):return group_sources(self.places,row['name'],row['lat'],row['lon'],row['category'])
 def city_candidates(self,name):return cities(self.city_db,name)
 def nearby(self,lat,lon,radius_km=10,category=None,diet=None,limit=20):
  if diet:
   if category is not None:raise ValueError('Cross-taxonomy category+diet join is unconfirmed')
   return {'source_family':'OpenStreetMap','snapshot_results':osm_search(self.osm_db,lat,lon,radius_km,diet,limit),'live_status':None}
  rows=search(self.places,lat,lon,radius_km,category=category,limit=limit)
  for row in rows:row['osm_candidate_sources']=osm_candidates(self.osm_db,row['name'],row['lat'],row['lon'])
  return {'source_family':'Overture','snapshot_results':rows,'live_status':None,'enrichment_semantics':'OSM exact-name proximity candidates are unconfirmed identities; keep all conflicting tags and source objects'}
 def source(self,shard,block,ordinal,identity):return source(shard,block,ordinal,identity)
 def travel(self,title):
  db=sqlite3.connect('file:'+str(pathlib.Path(self.travel_db).resolve())+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
  rows=[dict(r) for r in db.execute('SELECT id,title,revision,timestamp,redirect FROM page WHERE title=? LIMIT 20',(title,))];db.close()
  for r in rows:r['source_url']='https://en.wikivoyage.org/w/index.php?oldid='+str(r['revision']);r['license']='CC-BY-SA-4.0'
  return rows

 def enrichment_candidates(self,name,lat,lon):
  return osm_candidates(self.osm_db,name,lat,lon)
 def travel_source(self,page_id):
  db=sqlite3.connect('file:'+str(pathlib.Path(self.travel_db).resolve())+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
  row=db.execute('SELECT * FROM page WHERE id=?',(page_id,)).fetchone()
  if row is None:db.close();return None
  result=dict(row);packed=result.pop('wikitext_zlib');decoder=zlib.decompressobj();raw=decoder.decompress(packed,16*1024*1024+1)
  if len(raw)>16*1024*1024 or not decoder.eof or decoder.unused_data:db.close();raise ValueError('Travel source exceeds reader bound or is corrupt')
  result['wikitext']=raw.decode();result['listings']=[dict(r) for r in db.execute('SELECT * FROM listing WHERE page=? ORDER BY ordinal',(page_id,))];result['source_url']='https://en.wikivoyage.org/w/index.php?oldid='+str(result['revision']);result['license']='CC-BY-SA-4.0';db.close();return result

 def travel_nearby(self,lat,lon,radius_km=10,limit=20):
  if not(math.isfinite(lat) and math.isfinite(lon) and math.isfinite(radius_km) and -90<=lat<=90 and -180<=lon<=180 and 0<radius_km<=100 and 1<=limit<=100):raise ValueError('Invalid bounded query')
  db=sqlite3.connect('file:'+str(pathlib.Path(self.travel_db).resolve())+'?mode=ro',uri=True);db.row_factory=sqlite3.Row;found=[]
  for row in db.execute('SELECT l.*,p.title,p.revision,p.timestamp FROM listing l JOIN page p ON p.id=l.page WHERE l.lat BETWEEN ? AND ?',(lat-radius_km/110,lat+radius_km/110)):
   r=dict(row)
   if r['lat'] is None or r['lon'] is None:continue
   d=distance(lat,lon,r['lat'],r['lon'])
   if d>radius_km:continue
   r.update(distance_km=d,source_url='https://en.wikivoyage.org/w/index.php?oldid='+str(r['revision']) if r['revision'] is not None else None,license='CC-BY-SA-4.0',live_status=None,identity_kind='article listing occurrence, not a proven unique place');found.append(r);found.sort(key=lambda x:(x['distance_km'],x['page'],x['ordinal']))
   if len(found)>limit:found.pop()
  db.close();return found
