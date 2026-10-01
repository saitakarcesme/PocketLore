"""Retain explicit OpenStreetMap bulk snapshot tags in a separate ODbL database."""
import hashlib,json,pathlib,sqlite3,sys
from common import norm,atomic_json
def build(cache,dest):
 cache=pathlib.Path(cache);dest=pathlib.Path(dest)
 if dest.exists():raise RuntimeError('Immutable output exists')
 manifest=json.loads((cache/'manifest.json').read_text());db=sqlite3.connect(dest)
 db.executescript('CREATE TABLE snapshot(sha256 TEXT PRIMARY KEY,url TEXT,retrieved TEXT,base_timestamp TEXT,copyright TEXT); CREATE TABLE osm(type TEXT,id INTEGER,version INTEGER,name TEXT,name_key TEXT,lat REAL,lon REAL,vegan TEXT,vegetarian TEXT,hours TEXT,raw TEXT,snapshot TEXT,PRIMARY KEY(type,id,snapshot)); CREATE INDEX osm_name_grid ON osm(name_key,lat,lon);')
 counts={}
 for f in manifest['files']:
  if 'overpass' not in f['url']:continue
  p=cache/f['path'];sha=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();assert sha==f['sha256'];data=json.loads(p.read_text());meta=data.get('osm3s',{})
  db.execute('INSERT INTO snapshot VALUES(?,?,?,?,?)',(sha,f['url'],f['retrieved_at'],meta.get('timestamp_osm_base'),meta.get('copyright')))
  for r in data['elements']:
   t=r.get('tags',{});c=r.get('center',r);name=t.get('name');db.execute('INSERT INTO osm VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(r['type'],r['id'],r.get('version'),name,norm(name) if name else None,c.get('lat'),c.get('lon'),t.get('diet:vegan'),t.get('diet:vegetarian'),t.get('opening_hours'),json.dumps(r,ensure_ascii=False),sha))
  counts[f['path']]=len(data['elements'])
 db.commit();report={'source_scope':manifest['boxes'],'counts':counts,'unique_osm_ids':db.execute('SELECT count(*) FROM (SELECT DISTINCT type,id FROM osm)').fetchone()[0],'diet_vegan_fill':db.execute('SELECT count(vegan) FROM osm').fetchone()[0],'hours_fill':db.execute('SELECT count(hours) FROM osm').fetchone()[0],'rights':'ODbL-1.0; copyright OpenStreetMap contributors; separate database; redistribution obligations remain','missing_versions':'remain null; snapshot hash pins available source','global_enrichment_complete':False};db.close();report.update(bytes=dest.stat().st_size,sha256=hashlib.file_digest(dest.open('rb'),'sha256').hexdigest());atomic_json(dest.with_suffix('.report.json'),report);print(report)
if __name__=='__main__':build(*sys.argv[1:])
