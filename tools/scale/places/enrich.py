"""Read separately licensed enrichments without asserting identity from proximity alone."""
import json,math,pathlib,sqlite3,zlib
from common import norm
from search import distance
from osm_read import is_compact,expand
def connect(path):
 return sqlite3.connect('file:'+str(pathlib.Path(path).resolve())+'?mode=ro',uri=True)
def cities(path,name):
 db=connect(path);db.row_factory=sqlite3.Row
 rows=db.execute('SELECT c.* FROM alias a JOIN city c ON c.id=a.city_id WHERE a.name_key=? ORDER BY c.population DESC,c.id LIMIT 100',(norm(name),)).fetchall();db.close();return [dict(r) for r in rows]
def osm_candidates(path,name,lat,lon):
 db=connect(path);db.row_factory=sqlite3.Row
 compact=is_compact(db);cache={}
 rows=[expand(db,r,compact,cache) for r in db.execute('SELECT * FROM osm WHERE name_key=? AND lat BETWEEN ? AND ?',(norm(name),lat-.001,lat+.001)) if r['lat'] is not None and r['lon'] is not None and distance(lat,lon,r['lat'],r['lon'])<=.05];db.close()
 # Even a sole exact-name candidate is a proposed match, not proven identity.
 for r in rows:
  if isinstance(r['raw'],bytes):r['raw']=zlib.decompress(r['raw']).decode()
  r['match_status']= 'candidate_exact_normalized_name_within_50m_unconfirmed'
 return rows
def osm_search(path,lat,lon,radius_km=10,diet=None,limit=20):
 if diet not in (None,'vegan','vegetarian'):raise ValueError('Unsupported diet')
 if not (math.isfinite(lat) and math.isfinite(lon) and math.isfinite(radius_km) and -90<=lat<=90 and -180<=lon<=180 and 0<radius_km<=100 and 1<=limit<=100):raise ValueError('Invalid bounded query')
 db=connect(path);db.row_factory=sqlite3.Row
 sql='SELECT * FROM osm WHERE lat BETWEEN ? AND ?';args=[lat-radius_km/110,lat+radius_km/110]
 if diet:sql+=' AND '+diet+" IN ('yes','only')"
 rows=[]
 for row in db.execute(sql,args):
  r=dict(row)
  if r['lat'] is None or r['lon'] is None:continue
  d=distance(lat,lon,r['lat'],r['lon'])
  if d<=radius_km:
   r['distance_km']=d;r['live_status']=None;rows.append(r)
   rows.sort(key=lambda r:(r['distance_km'],r['type'],r['id']))
   if len(rows)>limit:rows.pop()
 compact=is_compact(db);cache={};rows=[expand(db,r,compact,cache) for r in rows];db.close();return rows
