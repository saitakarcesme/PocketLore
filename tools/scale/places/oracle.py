"""Direct pinned-Parquet query oracle for the frozen development checks.
Uses declared source boxes only for conservative candidate selection, then exact WKB.
"""
import math,pathlib,struct,uuid
import duckdb,pyarrow as pa,pyarrow.parquet as pq
from common import norm
from search import distance,R
pa.set_cpu_count(1);pa.set_io_thread_count(1)
class Oracle:
 def __init__(self,paths):
  self.paths=[str(p) for p in paths];self.db=duckdb.connect(config={'threads':1,'memory_limit':'1GB','temp_directory':'/home/isa/PocketLore-control/scale-workers/places/oracle-temp'});self.files={}
 def search(self,lat,lon,radius_km=10,category=None,name=None,diet=None,limit=20):
  if diet:return []
  dy=math.degrees(radius_km/R);dx=180 if abs(lat)+dy>=90 else math.degrees(math.asin(min(1,math.sin(radius_km/R)/math.cos(math.radians(lat)))))
  lo,hi=lon-dx,lon+dx;spans=[(max(-180,lo),min(180,hi))]
  if lo< -180:spans.append((lo+360,180))
  if hi>180:spans.append((-180,hi-360))
  found={}
  for left,right in spans:
   sql='SELECT filename,file_row_number+1 AS ordinal,id,geometry,names.primary AS name,taxonomy.primary AS category,basic_category FROM read_parquet(?,filename=true,file_row_number=true) WHERE bbox.ymax>=? AND bbox.ymin<=? AND bbox.xmax>=? AND bbox.xmin<=?'
   args=[self.paths,max(-90,lat-dy),min(90,lat+dy),left,right]
   if category:sql+=' AND (taxonomy.primary=? OR basic_category=? OR list_contains(taxonomy.hierarchy,?) OR list_contains(taxonomy.alternates,?))';args.extend([category]*4)
   for batch in self.db.execute(sql,args).fetch_record_batch(2048):
    for r in batch.to_pylist():
     try:
      geometry=r['geometry'];typ,b,a=struct.unpack(('<' if geometry[0]==1 else '>')+'Idd',geometry[1:]);assert typ==1 and r['name'] and math.isfinite(a) and math.isfinite(b) and -90<=a<=90 and -180<=b<=180;uuid.UUID(r['id'])
     except (AssertionError,ValueError,TypeError,IndexError,struct.error):continue
     key_name=norm(r['name'])
     if name and key_name!=norm(name):continue
     d=distance(lat,lon,a,b)
     if d>radius_km:continue
     key=(key_name,float(a).hex(),float(b).hex(),r['category'] or r['basic_category']);row={'id':r['id'],'lat':a,'lon':b,'distance_km':d,'file':r['filename'],'ordinal':r['ordinal']};old=found.get(key)
     if old is None or row['id']<old['id']:found[key]=row
     if len(found)>limit*2:found=dict(sorted(found.items(),key=lambda x:(x[1]['distance_km'],x[1]['id']))[:limit])
  return sorted(found.values(),key=lambda r:(r['distance_km'],r['id']))[:limit]
 def source(self,row):
  path=row['file']
  if path not in self.files:
   f=pq.ParquetFile(path);offsets=[];total=0
   for i in range(f.num_row_groups):offsets.append(total);total+=f.metadata.row_group(i).num_rows
   self.files[path]=(f,offsets)
  f,offsets=self.files[path];ordinal=row['ordinal'];group=max(i for i,o in enumerate(offsets) if o<ordinal)
  r=f.read_row_group(group,use_threads=False).slice(ordinal-offsets[group]-1,1).to_pylist(maps_as_pydicts='strict')[0];del r['geometry'];return r
 def close(self):self.db.close()
