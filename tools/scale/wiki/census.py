#!/usr/bin/env python3
"""Disk-backed eligibility census; freeze source locators and priority before bulk indexing."""
import argparse,collections,json,pathlib,resource,sqlite3,time
import pyarrow.parquet as pq
from build import eligibility
from acquire import atomic
p=argparse.ArgumentParser();p.add_argument('lane');p.add_argument('--inventory',default='docs/evidence/scale/wiki/english-inventory.json');a=p.parse_args();lane=pathlib.Path(a.lane)
db=sqlite3.connect(lane/'census-v2.sqlite');db.executescript('PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL; PRAGMA cache_size=-262144; PRAGMA temp_store=FILE; CREATE TABLE IF NOT EXISTS source(id INTEGER NOT NULL,title TEXT NOT NULL,shard TEXT NOT NULL,source_row INTEGER NOT NULL,eligible INTEGER NOT NULL,reason TEXT,text_bytes INTEGER NOT NULL,wikitext_bytes INTEGER NOT NULL,has_math INTEGER NOT NULL,revision INTEGER NOT NULL,PRIMARY KEY(shard,source_row)) WITHOUT ROWID; DROP INDEX IF EXISTS source_id; CREATE TABLE IF NOT EXISTS completed(shard TEXT PRIMARY KEY,rows INTEGER NOT NULL,seconds REAL NOT NULL);');start=time.monotonic()
queries=json.loads(pathlib.Path('docs/evidence/scale/wiki/queries-v1.json').read_text());wanted={t for q in queries['queries'] for t in q['expected_titles']};audit=lane/'receipts/query-sources';audit.mkdir(exist_ok=True)
for item in json.loads(pathlib.Path(a.inventory).read_text())['files']:
 name=pathlib.Path(item['path']).name
 if db.execute('SELECT 1 FROM completed WHERE shard=?',(name,)).fetchone():continue
 path=lane/'bulk'/name
 if not path.exists():print('Await acquisition: '+name,flush=True);break
 t=time.monotonic();count=0;db.execute('BEGIN')
 for batch in pq.ParquetFile(path).iter_batches(batch_size=64,use_threads=False):
  if batch.nbytes>2*1024**3:raise RuntimeError('Batch exceeds 2 GiB')
  for r in batch.to_pylist():
   why=eligibility(r)
   db.execute('INSERT INTO source VALUES (?,?,?,?,?,?,?,?,?,?)',(r['page_id'],r['title'],name,count,int(not why),why,len((r['text'] or '').encode()),len((r['wikitext'] or '').encode()),int(r['has_math'] or False),r['version'] or 0))
   if r['title'] in wanted:
    atomic(audit/(str(r['page_id'])+'.json'),{'source_shard':name,'source_sha256':item['lfs']['oid'],'source_row':count,'eligibility':why,'record':r})
   count+=1
 db.execute('INSERT INTO completed VALUES (?,?,?)',(name,count,time.monotonic()-t));db.commit();print(json.dumps({'shard':name,'rows':count,'seconds':time.monotonic()-t}),flush=True)
result={'rows':db.execute('SELECT count(*) FROM source').fetchone()[0],'eligible':db.execute('SELECT count(*) FROM source WHERE eligible=1').fetchone()[0],'completed':db.execute('SELECT * FROM completed').fetchall(),'seconds_this_run':time.monotonic()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
atomic(lane/'census-measurement.json',result);db.execute('PRAGMA wal_checkpoint(TRUNCATE)');db.close();print(json.dumps(result),flush=True)
