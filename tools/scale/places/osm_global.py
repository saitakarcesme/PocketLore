"""Bounded incremental Overpass JSON import; reject runtime errors as incomplete."""
import hashlib,json,pathlib,re,sqlite3,sys,time
from common import atomic_json,norm
def elements(path):
 decoder=json.JSONDecoder()
 with open(path,encoding='utf-8') as f:
  buf=''
  while not (m:=re.search(r'"elements"\s*:\s*\[',buf)):
   b=f.read(65536)
   if not b or len(buf)>1048576:raise ValueError('Missing bounded elements header')
   buf+=b
  header=json.loads(buf[:m.start()].rstrip().rstrip(',')+'}')
  if header.get('remark'):raise ValueError(header['remark'])
  yield 'header',header;buf=buf[m.end():]
  while True:
   buf=buf.lstrip()
   if buf.startswith(','):buf=buf[1:].lstrip()
   if buf.startswith(']'):
    tail=buf[1:]+f.read(1048576)
    if f.read(1):raise ValueError('Oversized trailing metadata')
    end=json.loads('{'+tail.lstrip().lstrip(','))
    if end.get('remark'):raise ValueError(end['remark'])
    yield 'end',end;return
   try:obj,n=decoder.raw_decode(buf)
   except json.JSONDecodeError:
    b=f.read(65536)
    if not b:raise ValueError('Truncated element JSON')
    buf+=b
    if len(buf)>16777216:raise ValueError('Single element exceeds 16 MiB bound')
    continue
   if not isinstance(obj,dict):raise ValueError('Non-object element')
   yield 'element',obj;buf=buf[n:]
def build(src,dest):
 src=pathlib.Path(src);dest=pathlib.Path(dest)
 if dest.exists():raise RuntimeError('Immutable output exists')
 stage=dest.with_suffix('.building.sqlite');db=sqlite3.connect(stage);db.executescript('PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; CREATE TABLE snapshot(sha256 TEXT PRIMARY KEY,url TEXT,retrieved TEXT,base_timestamp TEXT,copyright TEXT); CREATE TABLE osm(type TEXT,id INTEGER,version INTEGER,name TEXT,name_key TEXT,lat REAL,lon REAL,vegan TEXT,vegetarian TEXT,hours TEXT,raw TEXT,snapshot TEXT,PRIMARY KEY(type,id,snapshot)); CREATE INDEX osm_name_grid ON osm(name_key,lat,lon);')
 sha=hashlib.file_digest(src.open('rb'),'sha256').hexdigest();count=0;complete=False
 for kind,r in elements(src):
  if kind=='header':
   meta=r.get('osm3s',{});timestamp=meta.get('timestamp_osm_base');assert timestamp
   db.execute('INSERT INTO snapshot VALUES(?,?,?,?,?)',(sha,'https://overpass-api.de/api/interpreter',time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),timestamp,meta.get('copyright')))
  elif kind=='end':complete=True
  else:
   t=r.get('tags',{});c=r.get('center',r);name=t.get('name');db.execute('INSERT INTO osm VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(r['type'],r['id'],r.get('version'),name,norm(name) if name else None,c.get('lat'),c.get('lon'),t.get('diet:vegan'),t.get('diet:vegetarian'),t.get('opening_hours'),json.dumps(r,ensure_ascii=False),sha));count+=1
   if count%5000==0:db.commit()
 if not complete:raise ValueError('Missing terminal JSON')
 db.commit();report={'records':count,'unique_osm_ids':db.execute('SELECT count(*) FROM (SELECT DISTINCT type,id FROM osm)').fetchone()[0],'snapshot_timestamp':timestamp,'source_sha256':sha,'vegan_filled':db.execute('SELECT count(vegan) FROM osm').fetchone()[0],'vegetarian_filled':db.execute('SELECT count(vegetarian) FROM osm').fetchone()[0],'hours_filled':db.execute('SELECT count(hours) FROM osm').fetchone()[0],'scope':'global records carrying diet:vegan or diet:vegetarian; hours on these records only','all_global_hours':False,'query_complete':True,'license':'ODbL-1.0','attribution':'OpenStreetMap contributors'};db.execute('PRAGMA wal_checkpoint(TRUNCATE)');db.close();stage.rename(dest);report.update(bytes=dest.stat().st_size,sha256=hashlib.file_digest(dest.open('rb'),'sha256').hexdigest());atomic_json(dest.with_suffix('.report.json'),report);print(report)
if __name__=='__main__':build(*sys.argv[1:])
