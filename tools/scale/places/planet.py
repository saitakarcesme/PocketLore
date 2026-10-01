"""Stream every diet/hours-tagged planet entity with a bounded decoder pool.
Nodes keep exact source coordinates; way and relation coordinates remain unknown.
No tag-bearing object is dropped for lacking a name or coordinate.
"""
import hashlib,json,pathlib,sqlite3,sys,time,zlib
import resource
import osmium
from common import file_sha256,atomic_json,norm
def build(src,dest):
 src=pathlib.Path(src);dest=pathlib.Path(dest)
 if dest.exists():raise RuntimeError('Immutable output exists')
 start=time.time();stage=dest.with_suffix('.building.sqlite');db=sqlite3.connect(stage)
 db.executescript('''PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA wal_autocheckpoint=0; PRAGMA cache_size=-131072;
 CREATE TABLE IF NOT EXISTS snapshot(sha256 TEXT PRIMARY KEY,url TEXT,retrieved TEXT,base_timestamp TEXT,copyright TEXT);
 CREATE TABLE IF NOT EXISTS osm(type TEXT,id INTEGER,version INTEGER,name TEXT,name_key TEXT,lat REAL,lon REAL,vegan TEXT,vegetarian TEXT,hours TEXT,raw BLOB,snapshot TEXT,PRIMARY KEY(type,id,snapshot));
 CREATE TABLE IF NOT EXISTS progress(key TEXT PRIMARY KEY,value TEXT);''')
 receipt=json.loads(src.with_suffix('.receipt.json').read_text());sha=receipt['sha256'];pool=osmium.io.ThreadPool(1,2)
 proc=osmium.FileProcessor(src,thread_pool=pool).with_filter(osmium.filter.KeyFilter('diet:vegan','diet:vegetarian','opening_hours'))
 timestamp=proc.header.get('osmosis_replication_timestamp');db.execute('INSERT OR IGNORE INTO snapshot VALUES(?,?,?,?,?)',(sha,receipt['url'],receipt['retrieved_utc'],timestamp,'OpenStreetMap contributors; ODbL-1.0'));db.commit();count=0;max_raw_bytes=0
 for o in proc:
  t=dict(o.tags);kind='node' if o.is_node() else 'way' if o.is_way() else 'relation';lat=lon=None
  if o.is_node() and o.location.valid():lat=o.location.lat;lon=o.location.lon
  raw={'type':kind,'id':o.id,'version':o.version,'timestamp':str(o.timestamp),'changeset':o.changeset,'tags':t,'coordinate_basis':'source node coordinate' if lat is not None else 'unknown; no center inferred'}
  if o.is_way():raw['nodes']=[n.ref for n in o.nodes]
  elif o.is_relation():raw['members']=[{'type':m.type,'ref':m.ref,'role':m.role} for m in o.members]
  else:raw.update(lat=lat,lon=lon)
  encoded=json.dumps(raw,ensure_ascii=False,separators=(',',':')).encode();max_raw_bytes=max(max_raw_bytes,len(encoded))
  if len(encoded)>2147483648:raise RuntimeError('Source object exceeds 2 GiB processing bound')
  name=t.get('name');db.execute('INSERT OR IGNORE INTO osm VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(kind,o.id,o.version,name,norm(name) if name else None,lat,lon,t.get('diet:vegan'),t.get('diet:vegetarian'),t.get('opening_hours'),zlib.compress(encoded,6),sha));count+=1
  if count%50000==0:db.execute("INSERT OR REPLACE INTO progress VALUES('processed',?)",(str(count),));db.commit();print(count,round(time.time()-start,2),flush=True)
 db.commit();db.executescript('CREATE INDEX IF NOT EXISTS osm_name_grid ON osm(name_key,lat,lon); CREATE INDEX IF NOT EXISTS osm_grid ON osm(lat,lon);')
 report={'source_sha256':sha,'source':str(src),'snapshot_timestamp':timestamp,'records':db.execute('SELECT count(*) FROM osm').fetchone()[0],'types':dict(db.execute('SELECT type,count(*) FROM osm GROUP BY type')),'located_nodes':db.execute('SELECT count(lat) FROM osm').fetchone()[0],'vegan_filled':db.execute('SELECT count(vegan) FROM osm').fetchone()[0],'vegetarian_filled':db.execute('SELECT count(vegetarian) FROM osm').fetchone()[0],'hours_filled':db.execute('SELECT count(hours) FROM osm').fetchone()[0],'all_planet_tags_processed':True,'raw_codec':'zlib UTF-8 JSON','max_raw_object_bytes':max_raw_bytes,'way_relation_geometry':'unknown; original node/member references retained for later geometry resolution','license':'ODbL-1.0','attribution':'OpenStreetMap contributors','decoder_threads':1,'decoder_queue':2,'coordinate_enrichment_complete':False}
 assert db.execute('PRAGMA quick_check').fetchone()[0]=='ok';checkpoint=db.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone();assert checkpoint==(0,0,0),checkpoint;db.close();stage.rename(dest);report.update(bytes=dest.stat().st_size,sha256=file_sha256(dest),seconds=time.time()-start,max_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);atomic_json(dest.with_suffix('.report.json'),report);print(report)
if __name__=='__main__':
 import fcntl
 slot=pathlib.Path('/home/isa/PocketLore-control/scale-workers/places/second-compute.lock').open('a');fcntl.flock(slot,fcntl.LOCK_EX)
 build(*sys.argv[1:])
