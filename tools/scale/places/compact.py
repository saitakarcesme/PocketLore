"""Lossless source-field block storage with SQLite grid/category/city indexes.
All eligible records remain; exact point coordinates replace WKB serialization.
"""
import hashlib,json,math,pathlib,resource,sqlite3,struct,sys,time,uuid,zlib
import duckdb,pyarrow as pa,pyarrow.parquet as pq
from common import file_sha256,atomic_json,norm
pa.set_cpu_count(1);pa.set_io_thread_count(1)
MAX_BLOCK=32*1024*1024
def build(src,dest):
 src=pathlib.Path(src);dest=pathlib.Path(dest)
 if dest.exists():raise RuntimeError('Immutable compact output exists')
 start=time.time();stage=dest.with_suffix('.building.sqlite');db=sqlite3.connect(stage)
 db.executescript('''PRAGMA journal_mode=WAL;PRAGMA synchronous=NORMAL;PRAGMA wal_autocheckpoint=0;PRAGMA cache_size=-65536;
 CREATE TABLE IF NOT EXISTS block(id INTEGER PRIMARY KEY,records INTEGER,payload BLOB,sha256 TEXT);
 CREATE TABLE IF NOT EXISTS grid(gy INTEGER,gx INTEGER,block INTEGER);
 CREATE TABLE IF NOT EXISTS category(category TEXT,block INTEGER);
 CREATE TABLE IF NOT EXISTS city(city TEXT,block INTEGER);
 CREATE TABLE IF NOT EXISTS rejected(ordinal INTEGER PRIMARY KEY,reason TEXT,raw_json TEXT,geometry BLOB);
 CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT);''')
 old=db.execute("SELECT value FROM metadata WHERE key='processed'").fetchone();processed=int(old[0]) if old else 0
 block_id=db.execute('SELECT coalesce(max(id),0) FROM block').fetchone()[0];count=db.execute('SELECT coalesce(sum(records),0) FROM block').fetchone()[0]
 f=pq.ParquetFile(src);fields=','.join('"'+n+'" := "'+n+'"' for n in f.schema_arrow.names if n!='geometry')
 con=duckdb.connect(config={'threads':1,'memory_limit':'512MB','temp_directory':str(dest.parent/(dest.stem+'-duckdb-temp'))})
 query='SELECT file_row_number+1 AS ordinal,id,geometry,names.primary AS name,taxonomy.primary AS primary_category,basic_category,addresses[1].locality AS city,addresses[1].country AS country,operating_status AS status,list_distinct(list_concat(taxonomy.hierarchy,taxonomy.alternates,[taxonomy.primary,basic_category])) AS categories,to_json(struct_pack('+fields+')) AS raw_json FROM read_parquet(?,file_row_number=true)'
 batches=con.execute(query,[str(src)]).fetch_record_batch(2048);max_arrow=0;max_block=0
 key_schema=pa.schema([('id',pa.binary(16)),('entity_key',pa.binary(16)),('category',pa.string()),('city',pa.string()),('country',pa.string()),('status',pa.string())])
 key_stage=dest.with_suffix('.keys.building.parquet');key_final=dest.with_suffix('.keys.parquet')
 if key_stage.exists():key_stage.rename(key_stage.with_name(key_stage.name+'.abandoned-'+str(time.time_ns())))
 key_writer=pq.ParquetWriter(key_stage,key_schema,compression='zstd')
 def write(rows):
  nonlocal block_id,count,max_block
  if not rows:return
  data=('['+','.join(r[0] for r in rows)+']').encode()
  if len(data)>MAX_BLOCK:
   if len(rows)==1:raise RuntimeError('Single source record exceeds explicit reader bound')
   half=len(rows)//2;write(rows[:half]);write(rows[half:]);return
  payload=zlib.compress(data,6)
  if len(payload)>1048576:
   if len(rows)==1:raise RuntimeError('Single record exceeds Android SQLite compressed-row bound')
   half=len(rows)//2;write(rows[:half]);write(rows[half:]);return
  block_id+=1;count+=len(rows);max_block=max(max_block,len(data))
  db.execute('INSERT INTO block VALUES(?,?,?,?)',(block_id,len(rows),payload,hashlib.sha256(data).hexdigest()))
  cells={(math.floor((r[1]+90)*10),math.floor((r[2]+180)*10)) for r in rows}
  cats={c for r in rows for c in r[3] if c};cities={r[4] for r in rows if r[4]}
  db.executemany('INSERT INTO grid VALUES(?,?,?)',((gy,gx,block_id) for gy,gx in cells));db.executemany('INSERT INTO category VALUES(?,?)',((c,block_id) for c in cats));db.executemany('INSERT INTO city VALUES(?,?)',((c,block_id) for c in cities))
 for batch in batches:
  max_arrow=max(max_arrow,batch.nbytes)
  if batch.nbytes>2147483648:raise RuntimeError('Arrow batch exceeds 2 GiB')
  rows=[];key_rows=[];last=processed
  for r in batch.to_pylist():
   last=r['ordinal']
   try:
    geometry=r['geometry'];typ,lon,lat=struct.unpack(('<' if geometry[0]==1 else '>')+'Idd',geometry[1:]);assert typ==1 and r['name'] and math.isfinite(lat) and math.isfinite(lon) and -90<=lat<=90 and -180<=lon<=180;uuid.UUID(r['id'])
   except (AssertionError,ValueError,TypeError,IndexError,struct.error):
    
    if last>processed:db.execute('INSERT INTO rejected VALUES(?,?,?,?)',(last,'invalid name, UUID or point',r['raw_json'],r['geometry']))
    continue
   name_key=norm(r['name']);primary=r['primary_category'] or r['basic_category'];entity=hashlib.sha256((name_key+'\0'+lat.hex()+'\0'+lon.hex()+'\0'+str(primary)).encode()).digest()[:16]
   key_rows.append({'id':uuid.UUID(r['id']).bytes,'entity_key':entity,'category':primary,'city':r['city'],'country':r['country'],'status':r['status']})
   if last<=processed:continue
   prefix=json.dumps([last,lat,lon,norm(r['name'])],ensure_ascii=False,separators=(',',':'))[:-1]
   rows.append((prefix+','+r['raw_json']+']',lat,lon,r['categories'] or [],r['city']))
  if key_rows:key_writer.write_table(pa.Table.from_pylist(key_rows,schema=key_schema))
  write(rows)
  if last>processed:
   db.execute("INSERT OR REPLACE INTO metadata VALUES('processed',?)",(str(last),));processed=last
  if rows and block_id%50==0:db.commit();print(processed,count,block_id,round(time.time()-start,2),flush=True)
 key_writer.close()
 db.commit();db.executescript('CREATE INDEX IF NOT EXISTS grid_lookup ON grid(gy,gx,block);CREATE INDEX IF NOT EXISTS category_lookup ON category(category,block);CREATE INDEX IF NOT EXISTS city_lookup ON city(city,block);')
 receipt=json.loads(src.with_suffix(src.suffix+'.receipt.json').read_text());meta={'schema_version':2,'release':'2026-09-23.1','source_sha256':receipt['sha256'],'source_object_url':'https://overturemaps-us-west-2.s3.amazonaws.com/release/2026-09-23.1/theme=places/type=place/'+src.name,'layout':['source_ordinal','latitude','longitude','NFKC_casefold_name','original_non_geometry_record'],'block_codec':'zlib','max_inflated_block_bytes':MAX_BLOCK,'max_compressed_block_bytes':1048576,'field_retention':'all original non-geometry fields; exact decoded WKB point retained as doubles; no confidence or region cut'}
 for k,v in meta.items():db.execute('INSERT OR REPLACE INTO metadata VALUES(?,?)',(k,json.dumps(v)))
 report={**meta,'raw_records':processed,'eligible_records':count,'blocks':block_id,'rejected':db.execute('SELECT count(*) FROM rejected').fetchone()[0],'max_arrow_batch_bytes':max_arrow,'max_actual_inflated_block_bytes':max_block}
 db.commit();assert db.execute('PRAGMA quick_check').fetchone()[0]=='ok';checkpoint=db.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone();assert checkpoint==(0,0,0),checkpoint;db.close();con.close();stage.rename(dest);key_stage.rename(key_final)
 report.update(keys_path=str(key_final),keys_sha256=file_sha256(key_final),bytes=dest.stat().st_size,sha256=file_sha256(dest),seconds_current_attempt=time.time()-start,max_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);atomic_json(dest.with_suffix('.report.json'),report);print(json.dumps(report),flush=True)
if __name__=='__main__':build(*sys.argv[1:])
