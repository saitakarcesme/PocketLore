"""Lossless OSM source blocks with small spatial/name/diet lookup rows."""
import hashlib,json,pathlib,resource,sqlite3,sys,time,zlib
from common import atomic_json,file_sha256
MAX_RAW=32*1024*1024;MAX_PACKED=1048576
def build(source,dest):
 source=pathlib.Path(source);dest=pathlib.Path(dest)
 if dest.exists():raise RuntimeError('Immutable output exists')
 start=time.time();stage=dest.with_suffix('.building.sqlite')
 if stage.exists():raise RuntimeError('Incomplete candidate preserved; inspect before an explicit versioned retry')
 src=sqlite3.connect('file:'+str(source.resolve())+'?mode=ro',uri=True);src.row_factory=sqlite3.Row;src.execute('PRAGMA cache_size=-32768');snapshots=src.execute('SELECT * FROM snapshot').fetchall();assert len(snapshots)==1;sha=snapshots[0]['sha256'];assert src.execute('SELECT count(*) FROM osm WHERE snapshot IS NOT ?',(sha,)).fetchone()[0]==0
 db=sqlite3.connect(stage);db.executescript('''PRAGMA journal_mode=WAL;PRAGMA synchronous=NORMAL;PRAGMA wal_autocheckpoint=0;PRAGMA cache_size=-65536;
 CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);
 CREATE TABLE snapshot(sha256 TEXT PRIMARY KEY,url TEXT,retrieved TEXT,base_timestamp TEXT,copyright TEXT);
 CREATE TABLE block(id INTEGER PRIMARY KEY,records INTEGER,payload BLOB,sha256 TEXT);
 CREATE TABLE osm(type TEXT,id INTEGER,name_key TEXT,lat REAL,lon REAL,vegan TEXT,vegetarian TEXT,block INTEGER,slot INTEGER,PRIMARY KEY(type,id)) WITHOUT ROWID;''');db.execute('INSERT INTO snapshot VALUES(?,?,?,?,?)',tuple(snapshots[0]));block=0;total=0;max_raw=0;max_packed=0
 def write(rows):
  nonlocal block,total,max_raw,max_packed
  if not rows:return
  raw=('['+','.join(r[1] for r in rows)+']').encode();packed=zlib.compress(raw,6)
  if len(raw)>MAX_RAW or len(packed)>MAX_PACKED:
   if len(rows)==1:raise RuntimeError('Source object exceeds explicit reader bound')
   half=len(rows)//2;write(rows[:half]);write(rows[half:]);return
  block+=1;max_raw=max(max_raw,len(raw));max_packed=max(max_packed,len(packed));db.execute('INSERT INTO block VALUES(?,?,?,?)',(block,len(rows),packed,hashlib.sha256(raw).hexdigest()))
  db.executemany('INSERT INTO osm VALUES(?,?,?,?,?,?,?,?,?)',((r['type'],r['id'],r['name_key'],r['lat'],r['lon'],r['vegan'],r['vegetarian'],block,i) for i,(r,_) in enumerate(rows)));total+=len(rows)
 batch=[];batch_bytes=0
 for r in src.execute('SELECT * FROM osm ORDER BY type,id'):
  text=zlib.decompress(r['raw']).decode()
  if len(text.encode())>MAX_RAW:raise RuntimeError('Source object exceeds inflated reader bound')
  if batch and batch_bytes+len(text.encode())>8*1024*1024:write(batch);batch=[];batch_bytes=0
  batch_bytes+=len(text.encode());prefix=json.dumps([r['lat'],r['lon']],separators=(',',':'))[:-1];batch.append((r,prefix+','+text+']'))
  if len(batch)==1024:
   write(batch);batch=[];batch_bytes=0
   if total%102400==0:db.commit();print(total,round(time.time()-start,2),flush=True)
 write(batch);expected=src.execute('SELECT count(*) FROM osm').fetchone()[0];assert total==expected
 db.commit();db.executescript("CREATE INDEX osm_name_grid ON osm(name_key,lat,lon) WHERE name_key IS NOT NULL;CREATE INDEX osm_grid ON osm(lat,lon) WHERE lat IS NOT NULL;CREATE INDEX osm_vegan_grid ON osm(lat,lon) WHERE vegan IN ('yes','only');CREATE INDEX osm_vegetarian_grid ON osm(lat,lon) WHERE vegetarian IN ('yes','only');")
 meta={'schema_version':2,'snapshot_sha256':sha,'source_sqlite_sha256':json.loads(source.with_suffix('.report.json').read_text())['sha256'],'source_sqlite':str(source),'raw_codec':'zlib JSON arrays [latitude,longitude,complete source object]','max_inflated_block_bytes':MAX_RAW,'max_compressed_block_bytes':MAX_PACKED,'license':'ODbL-1.0','attribution':'OpenStreetMap contributors'}
 db.executemany('INSERT INTO metadata VALUES(?,?)',((k,json.dumps(v)) for k,v in meta.items()));db.commit();assert db.execute('PRAGMA quick_check').fetchone()[0]=='ok';assert db.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()==(0,0,0);db.close();src.close();stage.rename(dest)
 report={**meta,'records':total,'blocks':block,'max_actual_inflated_block_bytes':max_raw,'max_actual_compressed_block_bytes':max_packed,'bytes':dest.stat().st_size,'sha256':file_sha256(dest),'seconds':time.time()-start,'max_rss_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'field_or_row_pruning':False};atomic_json(dest.with_suffix('.report.json'),report);print(json.dumps(report,indent=2))
if __name__=='__main__':build(*sys.argv[1:])
