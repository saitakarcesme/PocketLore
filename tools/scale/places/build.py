"""Bounded Arrow-to-SQLite shard build; preserves every eligible record and conflicts."""
import hashlib,json,math,pathlib,sqlite3,struct,sys,time,unicodedata,uuid,zlib
import resource
import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
pa.set_cpu_count(1);pa.set_io_thread_count(1)
def norm(s):return ' '.join(unicodedata.normalize('NFKC',s).casefold().split())
def atomic_json(path,obj):
 p=pathlib.Path(path);t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(obj,indent=2)+'\n');t.replace(p)
def build(source,dest,preview_groups=None):
 source=pathlib.Path(source);dest=pathlib.Path(dest);start=time.time()
 if dest.exists():raise RuntimeError('Immutable output already exists')
 stage=dest.with_suffix('.building.sqlite');db=sqlite3.connect(stage)
 db.executescript('''PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA wal_autocheckpoint=0; PRAGMA cache_size=-1048576; PRAGMA temp_store=FILE; PRAGMA threads=1;
 CREATE TABLE IF NOT EXISTS place(id BLOB,name TEXT NOT NULL,name_key TEXT NOT NULL,lat REAL NOT NULL,lon REAL NOT NULL,gx INTEGER NOT NULL,gy INTEGER NOT NULL,category TEXT,city TEXT,country TEXT,confidence REAL,status TEXT,entity_key BLOB NOT NULL,detail BLOB NOT NULL,ordinal INTEGER NOT NULL);
 CREATE TABLE IF NOT EXISTS category(place_id BLOB,category TEXT);
 CREATE TABLE IF NOT EXISTS rejected(ordinal INTEGER PRIMARY KEY,reason TEXT,record_json TEXT);
 CREATE TABLE IF NOT EXISTS progress(key TEXT PRIMARY KEY,value TEXT);
 CREATE TABLE IF NOT EXISTS conflict(id BLOB,ordinal INTEGER,detail BLOB);
 ''')
 prev=db.execute("SELECT value FROM progress WHERE key='ordinal'").fetchone();offset=int(prev[0]) if prev else 0
 ordinal=0;f=pq.ParquetFile(source);max_batch=0
 groups=range(min(preview_groups,f.num_row_groups)) if preview_groups else None
 if offset==f.metadata.num_rows:
  batches=[];ordinal=offset
 elif preview_groups:
  batches=f.iter_batches(batch_size=2048,row_groups=groups,use_threads=False)
 else:
  con=duckdb.connect(config={'threads':1,'memory_limit':'1GB','temp_directory':str(dest.parent/(dest.stem+'-duckdb-temp'))})
  fields=','.join('"'+n+'" := "'+n+'"' for n in f.schema_arrow.names if n!='geometry')
  query='SELECT id,geometry,names.primary AS name,taxonomy.primary AS category,basic_category,addresses[1].locality AS city,addresses[1].country AS country,confidence,operating_status,list_distinct(list_concat(taxonomy.hierarchy,taxonomy.alternates,[taxonomy.primary,basic_category])) AS categories,to_json(struct_pack('+fields+')) AS raw_json FROM read_parquet(?)'
  batches=con.execute(query,[str(source)]).fetch_record_batch(2048)
 for batch in batches:
  max_batch=max(max_batch,batch.nbytes)
  if batch.nbytes>2147483648:raise RuntimeError('Arrow batch limit exceeded')
  rows=[];cats=[];reject=[];conflicts=[]
  for r in batch.to_pylist():
   ordinal+=1
   if ordinal<=offset:continue
   try:
    geom=r['geometry'];order='<' if geom[0]==1 else '>';typ,lon,lat=struct.unpack(order+'Idd',geom[1:]);assert typ==1
    name=r.get('name') if 'raw_json' in r else (r['names'] or {}).get('primary');assert name and math.isfinite(lat) and math.isfinite(lon) and -90<=lat<=90 and -180<=lon<=180
    identity=uuid.UUID(r['id']).bytes
   except (AssertionError,ValueError,TypeError,struct.error,IndexError) as e:
    reject.append((ordinal,'missing name, invalid ID or point geometry',json.dumps(r,default=lambda v:v.hex() if isinstance(v,bytes) else str(v))));continue
   cat=r.get('category') if 'raw_json' in r else (r.get('taxonomy') or {}).get('primary') or r.get('basic_category');addr={'locality':r.get('city'),'country':r.get('country')} if 'raw_json' in r else (r.get('addresses') or [{}])[0];key=norm(name)
   entity=hashlib.sha256((key+'\0'+lat.hex()+'\0'+lon.hex()+'\0'+str(cat)).encode()).digest()[:16]
   detail=zlib.compress((r['raw_json'] if 'raw_json' in r else json.dumps({k:v for k,v in r.items() if k!='geometry'},ensure_ascii=False,separators=(',',':'))).encode(),1)
   rows.append((identity,name,key,lat,lon,math.floor((lon+180)*100),math.floor((lat+90)*100),cat,addr.get('locality'),addr.get('country'),r.get('confidence'),r.get('operating_status'),entity,detail,ordinal))
   categories=set(r.get('categories') or []) if 'raw_json' in r else set((r.get('taxonomy') or {}).get('hierarchy') or [])|set((r.get('taxonomy') or {}).get('alternates') or [])|{cat,r.get('basic_category')}
   cats.extend((identity,c) for c in categories if c)
  for row in rows:
   try:db.execute('INSERT INTO place VALUES('+','.join('?'*15)+')',row)
   except sqlite3.IntegrityError:conflicts.append((row[0],row[-1],row[-2]))
  db.executemany('INSERT OR IGNORE INTO category VALUES(?,?)',cats);db.executemany('INSERT INTO rejected VALUES(?,?,?)',reject);db.executemany('INSERT INTO conflict VALUES(?,?,?)',conflicts)
  db.execute("INSERT OR REPLACE INTO progress VALUES('ordinal',?)",(str(ordinal),))
  if ordinal%100000<2048:
   db.commit();print(ordinal,round(time.time()-start,2),flush=True)
 db.commit()
 db.executescript('CREATE INDEX IF NOT EXISTS place_id ON place(id);CREATE INDEX IF NOT EXISTS category_lookup ON category(category,place_id);')
 duplicates=db.execute('SELECT id,min(rowid),count(*) FROM place GROUP BY id HAVING count(*)>1').fetchall()
 for identity,keep,count in duplicates:
  db.execute('INSERT INTO conflict SELECT id,ordinal,detail FROM place WHERE id=? AND rowid<>?',(identity,keep))
  db.execute('DELETE FROM place WHERE id=? AND rowid<>?',(identity,keep))
 db.commit()
 db.executescript('''CREATE INDEX IF NOT EXISTS place_grid ON place(gy,gx);
 CREATE INDEX IF NOT EXISTS place_category_grid ON place(category,gy,gx);
 CREATE INDEX IF NOT EXISTS place_city ON place(city,country);
 CREATE INDEX IF NOT EXISTS place_name ON place(name_key);
 CREATE INDEX IF NOT EXISTS place_entity ON place(entity_key);''')
 metadata={'schema_version':1,'map_encoding':'JSON objects (DuckDB) or arrays of key/value pairs (Arrow preview); same source fields','release':'2026-09-23.1','source':str(source),'source_sha256':hashlib.file_digest(source.open('rb'),'sha256').hexdigest(),'preview':bool(preview_groups),'eligibility':'all named valid WKB points with UUID; no confidence or geographic cutoff','dedup':'ID uniqueness; exact NFKC casefold name + exact binary coordinates + category forms entity key; conflicting IDs retained separately','hours':None,'diet':None,'live_status':None}
 for k,v in metadata.items():db.execute('INSERT OR REPLACE INTO progress VALUES(?,?)',(k,json.dumps(v)))
 report={**metadata,'raw_rows':ordinal,'unique_ids':db.execute('SELECT count(*) FROM place').fetchone()[0],'exact_entities':db.execute('SELECT count(DISTINCT entity_key) FROM place').fetchone()[0],'rejected':db.execute('SELECT count(*) FROM rejected').fetchone()[0],'id_conflicts':db.execute('SELECT count(*) FROM conflict').fetchone()[0],'max_arrow_batch_bytes':max_batch,'fill':dict(db.execute('SELECT \'category\',count(category) FROM place UNION ALL SELECT \'city\',count(city) FROM place UNION ALL SELECT \'country\',count(country) FROM place UNION ALL SELECT \'snapshot_status\',count(status) FROM place')),'countries':dict(db.execute("SELECT coalesce(country,'unknown'),count(*) FROM place GROUP BY country"))}
 db.commit();assert db.execute('PRAGMA quick_check').fetchone()[0]=='ok';checkpoint=db.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone();assert checkpoint==(0,0,0),checkpoint;db.close();stage.rename(dest)
 report.update(sqlite_check='quick_check; exhaustive integrity scan not completed',resource_scope='current process attempt; prior attempts preserved separately',max_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,user_cpu_seconds=resource.getrusage(resource.RUSAGE_SELF).ru_utime,system_cpu_seconds=resource.getrusage(resource.RUSAGE_SELF).ru_stime,seconds_current_attempt=time.time()-start,bytes=dest.stat().st_size,sha256=hashlib.file_digest(dest.open('rb'),'sha256').hexdigest());atomic_json(dest.with_suffix('.report.json'),report);print(json.dumps(report),flush=True)
if __name__=='__main__':build(sys.argv[1],sys.argv[2],int(sys.argv[3]) if len(sys.argv)>3 else None)
