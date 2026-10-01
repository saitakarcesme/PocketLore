#!/usr/bin/env python3
"""Measure a new positional index in a new edition without changing article payloads."""
import argparse,fcntl,json,pathlib,resource,sqlite3,subprocess,time
from acquire import atomic,digest
from reader import Reader
from index_text import body,STOP
p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('out');a=p.parse_args();source=pathlib.Path(a.source);out=pathlib.Path(a.out)
assert json.loads((source/'measurement.json').read_text())['source_complete'];source_lock=(source/'writer.lock').open('rb');fcntl.flock(source_lock,fcntl.LOCK_SH|fcntl.LOCK_NB);out.mkdir(parents=True,exist_ok=False);lock=(out/'writer.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);start=time.monotonic()
for name in ['catalog.sqlite','articles.blocks']:subprocess.run(['cp','--reflink=auto',str(source/name),str(out/name)],check=True)
reader=Reader(source);db=sqlite3.connect(out/'catalog.sqlite');db.executescript("PRAGMA cache_size=-262144; PRAGMA temp_store=FILE; PRAGMA threads=1; PRAGMA journal_mode=WAL; DROP TABLE terms; DROP TABLE search; CREATE VIRTUAL TABLE search USING fts5(title,body,content='',tokenize='unicode61'); CREATE VIRTUAL TABLE terms USING fts5vocab(search,'row');");count=0
for row in reader.dbs[0].execute('SELECT * FROM articles ORDER BY source_row'):
 payload=reader.payload(0,row);db.execute('INSERT INTO search(rowid,title,body) VALUES (?,?,?)',(row['id'],row['title'],body(payload['text'])));count+=1
 if count%8192==0:db.commit();print(count,flush=True)
db.commit();db.execute("INSERT INTO search(search) VALUES ('optimize')");db.commit();cfg=json.loads(db.execute("SELECT value FROM checkpoints WHERE key='config'").fetchone()[0]);cfg['reindex_sources']={name:digest(pathlib.Path(__file__).parent/name) for name in ['reindex.py','index_text.py','reader.py','acquire.py']};cfg['index_policy']='reader_stopwords_v1';cfg['index_stopwords']=sorted(STOP);cfg['index_parent_catalog_sha256']=digest(source/'catalog.sqlite');db.execute("UPDATE checkpoints SET value=? WHERE key='config'",(json.dumps(cfg),));db.commit();db.execute('VACUUM');db.execute('PRAGMA wal_checkpoint(TRUNCATE)');integrity=db.execute('PRAGMA integrity_check').fetchone()[0];assert integrity=='ok';db.close();reader.close()
m=json.loads((source/'measurement.json').read_text());m['installed_bytes']=sum((out/name).stat().st_size for name in ['articles.blocks','catalog.sqlite']);m['reindexing']={'source':str(source.resolve()),'source_bytes':json.loads((source/'measurement.json').read_text())['installed_bytes'],'records_verified':count,'policy':'reader_stopwords_v1','payloads':'Byte-identical file copy, every decoded record hash verified','seconds':time.monotonic()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'sqlite_integrity':integrity};atomic(out/'measurement.json',m);print(json.dumps(m,indent=2),flush=True)
