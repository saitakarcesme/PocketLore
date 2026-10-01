"""Offline schema-v2 block reader; bounded inflation, exact source fields and distance."""
import hashlib,json,math,pathlib,sqlite3,zlib
from common import norm
from search import distance,R
MAX_BLOCK=32*1024*1024
def connect(path):return sqlite3.connect('file:'+str(pathlib.Path(path).resolve())+'?mode=ro',uri=True)
def inflate(payload,sha):
 d=zlib.decompressobj();raw=d.decompress(payload,MAX_BLOCK+1)
 if len(raw)>MAX_BLOCK or not d.eof or d.unused_data:raise ValueError('Invalid or oversized block')
 if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('Block hash mismatch')
 return json.loads(raw)
def search(paths,lat,lon,radius_km=10,category=None,name=None,diet=None,limit=20,city=None):
 if not(-90<=lat<=90 and -180<=lon<=180 and 0<radius_km<=100 and 1<=limit<=100):raise ValueError('Invalid bounded query')
 if diet is not None:return []
 dy=math.degrees(radius_km/R);dx=180 if abs(lat)+dy>=90 else math.degrees(math.asin(min(1,math.sin(radius_km/R)/math.cos(math.radians(lat)))))
 lo,hi=lon-dx,lon+dx;spans=[(max(-180,lo),min(180,hi))]
 if lo< -180:spans.append((lo+360,180))
 if hi>180:spans.append((-180,hi-360))
 found={}
 for path in paths:
  db=connect(path);db.execute('PRAGMA cache_size=-8192');seen=set()
  for left,right in spans:
   sql='SELECT DISTINCT g.block FROM grid g WHERE g.gy BETWEEN ? AND ? AND g.gx BETWEEN ? AND ?';args=[math.floor((max(-90,lat-dy)+90)*10),math.floor((min(90,lat+dy)+90)*10),math.floor((left+180)*10),math.floor((right+180)*10)]
   if category:sql+=' AND EXISTS(SELECT 1 FROM category c WHERE c.category=? AND c.block=g.block)';args.append(category)
   if city:sql+=' AND EXISTS(SELECT 1 FROM city c WHERE c.city=? AND c.block=g.block)';args.append(city)
   for block, in db.execute(sql,args):
    if block in seen:continue
    seen.add(block);payload,sha=db.execute('SELECT payload,sha256 FROM block WHERE id=?',(block,)).fetchone()
    for ordinal,a,b,name_key,r in inflate(payload,sha):
     if name and name_key!=norm(name):continue
     tax=r.get('taxonomy') or {};primary=tax.get('primary') or r.get('basic_category');cats=set(tax.get('hierarchy') or [])|set(tax.get('alternates') or [])|{primary,r.get('basic_category')};address=(r.get('addresses') or [{}])[0]
     if category and category not in cats:continue
     if city and address.get('locality')!=city:continue
     d=distance(lat,lon,a,b)
     if d>radius_km:continue
     key=(name_key,float(a).hex(),float(b).hex(),primary)
     row={'id':r['id'],'name':r['names']['primary'],'lat':a,'lon':b,'category':primary,'city':address.get('locality'),'country':address.get('country'),'confidence':r.get('confidence'),'status':r.get('operating_status'),'distance_km':d,'shard':str(path),'block_id':block,'source_ordinal':ordinal,'hours':None,'diet':None,'live_status':None}
     old=found.get(key)
     if old is None or row['id']<old['id']:found[key]=row
     if len(found)>limit*2:found=dict(sorted(found.items(),key=lambda x:(x[1]['distance_km'],x[1]['id']))[:limit])
  db.close()
 return sorted(found.values(),key=lambda r:(r['distance_km'],r['id']))[:limit]
def source(path,block,ordinal,identity):
 db=connect(path);row=db.execute('SELECT payload,sha256 FROM block WHERE id=?',(block,)).fetchone();meta={k:json.loads(v) for k,v in db.execute("SELECT key,value FROM metadata WHERE key<>'processed'")};db.close()
 if row:
  for n,lat,lon,_,record in inflate(*row):
   if n==ordinal and record['id']==identity:return {'record':record,'latitude':lat,'longitude':lon,'row_ordinal':n,'provenance':meta}
 return None

def group_sources(paths,name,lat,lon,category):
 """Yield every source variant of one exact group; retain conflicting fields."""
 gy,gx=math.floor((lat+90)*10),math.floor((lon+180)*10);name_key=norm(name)
 for path in paths:
  db=connect(path)
  try:
   blocks=db.execute('SELECT DISTINCT block FROM grid WHERE gy=? AND gx=?',(gy,gx))
   for block, in blocks:
    payload,sha=db.execute('SELECT payload,sha256 FROM block WHERE id=?',(block,)).fetchone()
    for ordinal,a,b,key,record in inflate(payload,sha):
     primary=(record.get('taxonomy') or {}).get('primary') or record.get('basic_category')
     if key==name_key and float(a).hex()==float(lat).hex() and float(b).hex()==float(lon).hex() and primary==category:
      yield {'id':record['id'],'shard':str(path),'block_id':block,'source_ordinal':ordinal,'record':record,'latitude':a,'longitude':b,'identity_status':'same exact normalized-name/coordinate/category group; all original fields retained; real-world identity unconfirmed'}
  finally:db.close()
