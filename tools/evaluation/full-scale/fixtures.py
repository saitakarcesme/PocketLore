#!/usr/bin/env python3
"""Small real-byte Android transaction fixtures; never counted as full coverage."""
import hashlib,json,pathlib,sqlite3,zlib,zipfile
ROOT=pathlib.Path('/home/isa/PocketLore-control/scale-workers/wiki/edition-v7')
OUT=pathlib.Path('downloads/full-scale/fixtures');OUT.mkdir(parents=True,exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=[];shards=[];counts=[0,0]
for title in ['Acid','Cooking']:
 for p in sorted(ROOT.glob('*/catalog.sqlite')):
  c=sqlite3.connect('file:'+str(p)+'?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row
  row=c.execute('select * from articles where title=?',(title,)).fetchone()
  if row:break
  c.close()
 assert row,title
 row=dict(row);b=c.execute('select * from blocks where id=?',(row['block_id'],)).fetchone()
 with (p.parent/'articles.blocks').open('rb') as f:f.seek(b['offset']);raw=zlib.decompress(f.read(b['length']))
 record=raw[row['offset']:row['offset']+row['length']];assert hashlib.sha256(record).digest()==row['sha256']
 shard=p.parent.name;d=OUT/shard;d.mkdir();shards.append(shard)
 dest=sqlite3.connect(d/'catalog.sqlite')
 for table in ['articles','blocks']:dest.execute(c.execute('select sql from sqlite_master where name=?',(table,)).fetchone()[0])
 row['block_id']=1;row['offset']=0;packed=zlib.compress(record)
 dest.execute('insert into articles('+','.join(row)+') values('+','.join('?' for _ in row)+')',list(row.values()))
 dest.execute('insert into blocks values(1,0,?,?,?)',(len(packed),len(record),hashlib.sha256(record).digest()))
 dest.execute("create virtual table search using fts5(title,body,content='')")
 dest.execute('insert into search(rowid,title,body) values(?,?,?)',(row['id'],title,json.loads(record)['text']));dest.commit();dest.close();c.close()
 (d/'articles.blocks').write_bytes(packed)
 counts[int(row['tier']=='lead')]+=1
 for name in ['catalog.sqlite','articles.blocks']:
  f=d/name;files.append(dict(path=str(f.relative_to(OUT)),bytes=f.stat().st_size,sha256=sha(f),payload=True))
 (OUT/(title+'.receipt.json')).write_text(json.dumps({'original_shard':shard,'article_id':row['id'],'source_record_sha256':hashlib.sha256(record).hexdigest(),'tier':row['tier']},indent=2))
notice=OUT/'NOTICE.txt';notice.write_bytes((ROOT/'NOTICE.txt').read_bytes());common=dict(path='NOTICE.txt',bytes=notice.stat().st_size,sha256=sha(notice),payload=True)
def bundle(name,fs,ss,previous=''):
 nfull=nlead=0
 for sh in ss:
  c=sqlite3.connect(OUT/sh/'catalog.sqlite');a,b=c.execute("select sum(tier='full'),sum(tier='lead') from articles").fetchone();nfull+=a;nlead+=b;c.close()
 m=dict(version=2,kind='wiki',collection_key='wiki-real-regression',replaces=previous,label='Real source subset — transaction test only',generation_allowed=False,rights_status='unreviewed; browse only',source_inventory_sha256=sha(ROOT/'installed-inventory.json'),installed_bytes=sum(f['bytes'] for f in fs),files=fs,shards=ss,documents=len(ss),full_articles=nfull,leads=nlead)
 raw=(json.dumps(m,sort_keys=True)+'\n').encode()
 with zipfile.ZipFile(OUT/(name+'.plscale'),'w') as z:
  z.writestr('manifest.json',raw)
  for f in fs:
   if f['payload']:z.write(OUT/f['path'],f['path'])
 (OUT/(name+'.json')).write_bytes(raw)
 return hashlib.sha256(raw).hexdigest()
id1=bundle('base',files[:2]+[common],shards[:1])
second=[dict(f,payload=False) for f in files[:2]]+files[2:]+[dict(common,payload=False)]
id2=bundle('update',second,shards,id1)
# A corrupt payload changes real bytes while retaining its original expected hash.
with zipfile.ZipFile(OUT/'update.plscale') as src,zipfile.ZipFile(OUT/'corrupt.plscale','w') as dst:
 for i,n in enumerate(src.namelist()):
  b=src.read(n)
  if i==1:b=bytes([b[0]^1])+b[1:]
  dst.writestr(n,b)
print(id1,id2)
