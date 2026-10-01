#!/usr/bin/env python3
"""Retain actual source blocks near two frozen cities; subset is not global coverage."""
import json,pathlib,sqlite3,hashlib,zipfile,math
P=pathlib.Path('/home/isa/PocketLore-control/scale-workers/places/data');O=pathlib.Path('downloads/full-scale/places-fixture');O.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ro(p):return sqlite3.connect('file:'+str(p)+'?mode=ro&immutable=1',uri=True)
city=ro(P/'cities.sqlite');anchors=[]
for q in ['London','Mexico City']:
 r=city.execute('select c.* from city c join alias a on a.city_id=c.id where a.name_key=? order by c.population desc,c.id limit 1',(q.lower(),)).fetchone();anchors.append(r)
with sqlite3.connect(O/'cities.sqlite') as d:
 for t in ['city','alias']:d.execute(city.execute('select sql from sqlite_master where name=?',(t,)).fetchone()[0])
 for row in anchors:
  d.execute('insert into city values('+','.join('?'*len(row))+')',row)
  for a in city.execute('select * from alias where city_id=?',(row[0],)):d.execute('insert or ignore into alias values('+','.join('?'*len(a))+')',a)
city.close()
# City schema names locate coordinates, without guessing column order.
with ro(O/'cities.sqlite') as d:coords=d.execute('select lat,lon from city').fetchall()
shards=[];records=0
for path in sorted(P.glob('compact-*.sqlite')):
 s=ro(path);blocks=set()
 for lat,lon in coords:
  dy=math.degrees(1/6371.0088);dx=dy/math.cos(math.radians(lat))
  blocks.update(x[0] for x in s.execute('select distinct block from grid where gy between ? and ? and gx between ? and ?',(math.floor((lat-dy+90)*10),math.floor((lat+dy+90)*10),math.floor((lon-dx+180)*10),math.floor((lon+dx+180)*10))))
 if not blocks:s.close();continue
 d=sqlite3.connect(O/path.name)
 for t in ['metadata','block','grid','category']:
  d.execute(s.execute('select sql from sqlite_master where name=?',(t,)).fetchone()[0])
  rows=s.execute('select * from metadata') if t=='metadata' else s.execute('select * from '+t+' where '+('id' if t=='block' else 'block')+' in ('+','.join('?'*len(blocks))+')',list(blocks))
  for row in rows:d.execute('insert into '+t+' values('+','.join('?'*len(row))+')',row)
 for sql, in s.execute("select sql from sqlite_master where type='index' and sql is not null and tbl_name in ('grid','category')"):d.execute(sql)
 records+=d.execute('select sum(records) from block').fetchone()[0];d.commit();d.close();s.close();shards.append(path.name)
files=[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p),payload=True) for p in sorted(O.glob('*.sqlite'))]
m=dict(version=2,kind='places',collection_key='places-real-regression',replaces='',generation_allowed=False,rights_status='unreviewed; browse only; real block subset not full coverage',source_inventory_sha256=sha(P.parent/'HANDOFF.json'),installed_bytes=sum(f['bytes'] for f in files),files=files,shards=shards,cities='cities.sqlite',source_records=records,label='Real two-city block subset')
raw=(json.dumps(m,sort_keys=True)+'\n').encode();(O/'manifest.json').write_bytes(raw)
with zipfile.ZipFile(O/'places.plscale','w') as z:
 z.writestr('manifest.json',raw)
 for f in files:z.write(O/f['path'],f['path'])
print(len(shards),records,m['installed_bytes'])
