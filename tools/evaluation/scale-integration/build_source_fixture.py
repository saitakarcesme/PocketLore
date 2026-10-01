#!/usr/bin/env python3
"""Real source byte regression subset; never counted as additional corpus coverage."""
import hashlib,json,pathlib,sqlite3,zlib,zipfile
root=pathlib.Path('/home/isa/PocketLore-control/scale-workers/wiki/edition-v7/000_00000')
out=pathlib.Path('downloads/scale-integration/source-fixture');out.mkdir(parents=True,exist_ok=True)
con=sqlite3.connect('file:'+str(root/'catalog.sqlite')+'?mode=ro&immutable=1',uri=True)
con.row_factory=sqlite3.Row
row=dict(con.execute('select * from articles where id=79780308').fetchone());block=con.execute('select * from blocks where id=?',(row['block_id'],)).fetchone()
with (root/'articles.blocks').open('rb') as f:f.seek(block['offset']);raw=zlib.decompress(f.read(block['length']))
record=raw[row['offset']:row['offset']+row['length']];assert hashlib.sha256(record).digest()==row['sha256'];payload=zlib.compress(record)
assert not (out/'catalog.sqlite').exists(),'Do not replace regression fixture'
c=sqlite3.connect(out/'catalog.sqlite')
for table in ('articles','blocks'):
 c.execute(con.execute('select sql from sqlite_master where name=?',(table,)).fetchone()[0])
row['block_id']=1;row['offset']=0
c.execute('insert into articles('+','.join(row)+') values('+','.join('?' for _ in row)+')',list(row.values()))
c.execute('insert into blocks(id,offset,length,raw_length,sha256) values(1,0,?,?,?)',(len(payload),len(record),hashlib.sha256(record).digest()))
c.execute("CREATE VIRTUAL TABLE search USING fts5(title,body,content='')")
c.execute('insert into search(rowid,title,body) values(?,?,?)',(row['id'],row['title'],json.loads(record)['text']));c.commit();c.close();(out/'articles.blocks').write_bytes(payload)
paths=['catalog.sqlite','articles.blocks'];files=[dict(path='fixture/'+p,bytes=(out/p).stat().st_size,sha256=hashlib.sha256((out/p).read_bytes()).hexdigest()) for p in paths]
m=dict(version=1,kind='wiki',generation_allowed=False,rights_status='dataset_license_only_unreviewed; real-source regression subset, not additional corpus',source_inventory_sha256=hashlib.sha256((root.parent/'installed-inventory.json').read_bytes()).hexdigest(),installed_bytes=sum(x['bytes'] for x in files),files=files,shards=['fixture'],documents=1,full_articles=int(row['tier']=='full'),leads=int(row['tier']=='lead'),label='Source byte regression fixture')
with zipfile.ZipFile(out.parent/'source-fixture.plscale','w') as z:
 z.writestr('manifest.json',json.dumps(m,sort_keys=True));
 for p in paths:z.write(out/p,'fixture/'+p)
print('Source regression subset prepared')
