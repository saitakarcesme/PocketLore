"""Resolve selected OSM way centers from all referenced planet nodes, on disk.
Relations remain unlocated. Centers are derived bounds, not entrances or exact POIs.
"""
import json,pathlib,sqlite3,sys,time,hashlib,zlib
import resource
import osmium
from common import file_sha256,atomic_json
def resolve(planet,source,dest,work):
 dest=pathlib.Path(dest);work=pathlib.Path(work)
 if dest.exists():raise RuntimeError('Immutable output exists')
 start=time.time();stage=dest.with_suffix('.building.sqlite');db=sqlite3.connect(stage)
 if not db.execute("SELECT 1 FROM sqlite_master WHERE name='osm'").fetchone():
  src=sqlite3.connect('file:'+str(pathlib.Path(source).resolve())+'?mode=ro',uri=True);src.backup(db);src.close()
 aux=sqlite3.connect(work);aux.executescript('PRAGMA journal_mode=WAL;PRAGMA synchronous=NORMAL;PRAGMA wal_autocheckpoint=0;PRAGMA cache_size=-131072;CREATE TABLE IF NOT EXISTS edge(way INTEGER,node INTEGER,PRIMARY KEY(way,node)) WITHOUT ROWID;CREATE TABLE IF NOT EXISTS node(id INTEGER PRIMARY KEY,lat REAL,lon REAL);CREATE TABLE IF NOT EXISTS progress(key TEXT PRIMARY KEY,value TEXT);')
 if not aux.execute("SELECT 1 FROM progress WHERE key='edges'").fetchone():
  count=0
  for identity,raw in db.execute("SELECT id,raw FROM osm WHERE type='way'"):
   refs=json.loads(zlib.decompress(raw) if isinstance(raw,bytes) else raw).get('nodes',[]);aux.executemany('INSERT OR IGNORE INTO edge VALUES(?,?)',((identity,n) for n in refs));count+=1
   if count%50000==0:aux.commit();print('ways',count,flush=True)
  aux.commit();aux.execute('CREATE INDEX IF NOT EXISTS edge_node ON edge(node)');aux.execute("INSERT INTO progress VALUES('edges','done')");aux.commit()
 total=aux.execute('SELECT count(DISTINCT node) FROM edge').fetchone()[0]
 if not aux.execute("SELECT 1 FROM progress WHERE key='nodes'").fetchone():
  # Stream at most ten million IDs into each C++ filter; no Python ID collection.
  last=-1
  while True:
   end=aux.execute('SELECT max(node) FROM (SELECT DISTINCT node FROM edge WHERE node>? ORDER BY node LIMIT 10000000)',(last,)).fetchone()[0]
   if end is None:break
   ids=(r[0] for r in aux.execute('SELECT DISTINCT node FROM edge WHERE node>? AND node<=? ORDER BY node',(last,end)))
   proc=osmium.FileProcessor(planet,entities=osmium.osm.NODE,thread_pool=osmium.io.ThreadPool(1,2)).with_filter(osmium.filter.IdFilter(ids));last=end;del ids
   n=0
   for obj in proc:
    if obj.location.valid():aux.execute('INSERT OR REPLACE INTO node VALUES(?,?,?)',(obj.id,obj.location.lat,obj.location.lon));n+=1
    if n%100000==0:aux.commit()
   aux.commit();print('node batch through',last,'found',n,flush=True)
  aux.execute("INSERT INTO progress VALUES('nodes','done')");aux.commit()
 aux.executescript('CREATE TABLE IF NOT EXISTS bounds AS SELECT e.way,count(*) expected,count(n.lat) found,min(n.lat) south,max(n.lat) north,min(n.lon) west,max(n.lon) east,min(CASE WHEN n.lon<0 THEN n.lon+360 ELSE n.lon END) west360,max(CASE WHEN n.lon<0 THEN n.lon+360 ELSE n.lon END) east360 FROM edge e LEFT JOIN node n ON n.id=e.node GROUP BY e.way;')
 count=0
 for way,expected,found,south,north,west,east,w360,e360 in aux.execute('SELECT * FROM bounds'):
  if expected!=found or not found:continue
  lon=(west+east)/2 if east-west<=180 else (w360+e360)/2
  if lon>180:lon-=360
  raw=db.execute("SELECT raw FROM osm WHERE type='way' AND id=?",(way,)).fetchone();r=json.loads(zlib.decompress(raw[0]) if isinstance(raw[0],bytes) else raw[0]);r['coordinate_basis']='derived bounding-box center of all referenced source nodes; not an entrance';r['bounds']=[south,west,north,east];r['longitude_wrap']=east-west>180;r['wrapped_bounds_longitude_0_360']=[w360,e360] if east-west>180 else None
  db.execute("UPDATE osm SET lat=?,lon=?,raw=? WHERE type='way' AND id=?",((south+north)/2,lon,zlib.compress(json.dumps(r,ensure_ascii=False,separators=(',',':')).encode(),6),way));count+=1
  if count%50000==0:db.commit()
 db.commit();bytes_before_vacuum=db.execute('PRAGMA page_count').fetchone()[0]*db.execute('PRAGMA page_size').fetchone()[0];db.execute('VACUUM');assert db.execute('PRAGMA quick_check').fetchone()[0]=='ok'
 records=db.execute('SELECT count(*) FROM osm').fetchone()[0];located=db.execute('SELECT count(lat) FROM osm').fetchone()[0];types=dict(db.execute('SELECT type,count(*) FROM osm GROUP BY type'))
 base_report=pathlib.Path(source).with_suffix('.report.json')
 base_metadata=json.loads(base_report.read_text()) if base_report.exists() else {}
 if base_metadata:assert records==base_metadata['records']
 db.execute('PRAGMA wal_checkpoint(TRUNCATE)');db.close();aux.close();stage.rename(dest);report={'logical_sqlite_bytes_before_vacuum':bytes_before_vacuum,'storage_compaction':'SQLite VACUUM only; no field or row pruning','source_sqlite_sha256':base_metadata.get('sha256'),'planet_sha256':base_metadata.get('source_sha256'),'license':'ODbL-1.0','attribution':'OpenStreetMap contributors','records':records,'located_entities':located,'types':types,'quick_check':'ok','records_preserved_from_base':True,'resolved_ways':count,'needed_unique_nodes':total,'relations':'coordinates unknown; retained','source':str(source),'planet':str(planet),'seconds':time.time()-start,'bytes':dest.stat().st_size,'sha256':file_sha256(dest),'id_filter_batch_max':10000000,'max_rss_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'decoder_threads':1,'decoder_queue':2};atomic_json(dest.with_suffix('.report.json'),report);print(report)
if __name__=='__main__':
 import fcntl
 slot=pathlib.Path('/home/isa/PocketLore-control/scale-workers/places/second-compute.lock').open('a');fcntl.flock(slot,fcntl.LOCK_EX)
 resolve(*sys.argv[1:])
