#!/usr/bin/env python3
"""Lossless v2 -> v3 migration into a new directory; original pack remains immutable."""
import argparse,fcntl,hashlib,json,pathlib,resource,shutil,sqlite3,subprocess,time,zlib
from acquire import atomic,digest
from build_v3 import SCHEMA,notice_candidate
import pyarrow.parquet as pq
import re
from supplements import extract as extract_supplement
p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('out');p.add_argument('--fragments',action='store_true');p.add_argument('--source-parquet');p.add_argument('--lean',action='store_true');p.add_argument('--compression-level',type=int,choices=range(1,10),default=3);a=p.parse_args();a.fragments=a.fragments or a.lean;source=pathlib.Path(a.source);out=pathlib.Path(a.out);source_measurement=json.loads((source/'measurement.json').read_text());assert source_measurement['source_complete'];source_lock=(source/'writer.lock').open('rb');fcntl.flock(source_lock,fcntl.LOCK_SH|fcntl.LOCK_NB);out.mkdir(parents=True,exist_ok=False);out_lock=(out/'writer.lock').open('w');fcntl.flock(out_lock,fcntl.LOCK_EX|fcntl.LOCK_NB);t=time.monotonic()
subprocess.run(['cp','--reflink=auto',str(source/'catalog.sqlite'),str(out/'catalog.sqlite')],check=True);db=sqlite3.connect(out/'catalog.sqlite');db.execute('PRAGMA cache_size=-262144');db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA temp_store=FILE')
article_sql=next(x.strip() for x in SCHEMA.split(';') if x.strip().startswith('CREATE TABLE IF NOT EXISTS articles('));db.execute(article_sql.replace('articles(','articles_v3(',1));db.execute('CREATE TABLE blocks(id INTEGER PRIMARY KEY,offset INTEGER NOT NULL,length INTEGER NOT NULL,raw_length INTEGER NOT NULL,sha256 BLOB NOT NULL)')
original=sqlite3.connect(f'file:{source / "catalog.sqlite"}?mode=ro&immutable=1',uri=True);original.row_factory=sqlite3.Row
pending=[];buffer=bytearray();block_id=0;records=0;max_raw=0;wiki_bytes=0;scope_counts={};raw_bytes=0;notice_count=0
def source_rows():
    if not a.source_parquet:return
    for batch in pq.ParquetFile(a.source_parquet).iter_batches(batch_size=64,columns=['page_id','wikitext'],use_threads=False):
        if batch.nbytes>2*1024**3:raise RuntimeError('Source batch exceeds 2 GiB')
        yield from batch.to_pylist()
source_iter=enumerate(source_rows());source_position=-1;source_record=None
f=(source/'articles.blocks').open('rb');g=(out/'articles.blocks').open('xb')
def flush():
 global pending,buffer,block_id,max_raw
 if not pending:return
 block_id+=1;comp=zlib.compress(buffer,a.compression_level);offset=g.tell();g.write(comp);db.execute('INSERT INTO blocks VALUES (?,?,?,?,?)',(block_id,offset,len(comp),len(buffer),hashlib.sha256(buffer).digest()));db.executemany('INSERT INTO articles_v3 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',[tuple(r+[block_id]) for r in pending]);max_raw=max(max_raw,len(buffer));pending=[];buffer=bytearray()
for row in original.execute('SELECT * FROM articles ORDER BY offset'):
 if not 0<row['length']<=64*1024**2 or not 0<row['raw_length']<=128*1024**2:raise RuntimeError('Source block bound')
 f.seek(row['offset']);dec=zlib.decompressobj();raw=dec.decompress(f.read(row['length']),row['raw_length']+1)
 if not dec.eof or dec.unused_data or len(raw)!=row['raw_length'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise RuntimeError('Original source block mismatch')
 r=list(row)
 for i in [10,11,12]:r[i]=bytes.fromhex(r[i])
 if a.fragments:
  payload=json.loads(raw);wiki=payload['wikitext']
  if a.source_parquet:
   while source_position<row['source_row']:source_position,source_record=next(source_iter)
   assert source_record['page_id']==row['id']
   wiki=source_record['wikitext'];assert hashlib.sha256(wiki.encode()).hexdigest()==payload['source_wikitext_sha256']
   notice=notice_candidate(wiki);keep=notice or bool(row['has_math']) or bool(re.search(r'<(?:math|chem)|\{\{\s*(?:convert|cvt|val|math|physconst)\b',wiki,re.I))
   r[15]='notice_candidate_raw_preserved' if notice else 'dataset_license_only_unreviewed';notice_count+=int(notice)
   if not keep and not a.lean:wiki=''
  if wiki:
   assert hashlib.sha256(wiki.encode()).hexdigest()==payload['source_wikitext_sha256']
   fragment,ranges,scope=extract_supplement(wiki,lean=a.lean,has_math=bool(row['has_math']),preserve_empty_candidate=notice_candidate(wiki));payload.update({'wikitext':fragment,'wikitext_ranges':ranges,'wikitext_scope':scope});r[12]=hashlib.sha256(fragment.encode()).digest()
  else:payload['wikitext']='';payload['wikitext_ranges']=[];scope='archived_in_pinned_source_only';payload['wikitext_scope']=scope;r[12]=hashlib.sha256(b'').digest()
  payload['changes']='FineWiki HTML extraction; PocketLore lead selection when tier=lead; source supplement may contain exact ranges, as labeled by wikitext_scope'
  payload['notice_status']='exact_source_ranges_not_independently_cleared' if payload['wikitext'] else 'no_recognized_notice_source_archive_unreviewed'
  wiki_bytes+=len(payload['wikitext'].encode());scope_counts[scope]=scope_counts.get(scope,0)+1
  raw=json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode();r[9]=len(raw);r[10]=hashlib.sha256(raw).digest()
 if pending and (len(pending)>=64 or len(buffer)+len(raw)>8388608):flush()
 r[7]=len(buffer);r[8]=len(raw);raw_bytes+=len(raw)
 pending.append(r);buffer.extend(raw);records+=1
 if records%8192==0:flush();db.commit();print(records,flush=True)
flush();g.flush();g.close();f.close();original.close();db.commit();db.execute('DROP TABLE articles');db.execute('ALTER TABLE articles_v3 RENAME TO articles');db.execute('CREATE UNIQUE INDEX title_index ON articles(title)');db.commit();db.execute('VACUUM');db.execute('PRAGMA wal_checkpoint(TRUNCATE)');assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
m=json.loads((source/'measurement.json').read_text());counts=m['counts'];counts.pop('full_compressed_bytes',None);counts.pop('lead_compressed_bytes',None);counts['compressed_payload_bytes']=(out/'articles.blocks').stat().st_size;counts['blocks']=block_id;counts['max_block_raw_bytes']=max_raw
if a.fragments:
 counts['raw_payload_bytes']=raw_bytes;counts['wikitext_bytes']=wiki_bytes;counts.pop('wikitext_complete',None);counts.pop('wikitext_archive_only',None)
 for scope,count in scope_counts.items():counts['wikitext_'+scope]=count
 if a.source_parquet:counts['notice_candidate_raw_preserved']=notice_count;counts['dataset_license_only_unreviewed']=records-notice_count
cfg=json.loads(db.execute("SELECT value FROM checkpoints WHERE key='config'").fetchone()[0]);cfg.update({'schema':3,'compression_level':a.compression_level,'block_max_records':64,'block_target_bytes':8388608,'lossless_source_catalog_sha256':digest(source/'catalog.sqlite')});
if a.fragments:cfg['supplement']='lean' if a.lean else 'fragments';cfg['supplement_source_rescan']=bool(a.source_parquet)
db.execute("UPDATE checkpoints SET value=? WHERE key='config'",(json.dumps(cfg),));progress=json.loads(db.execute("SELECT value FROM checkpoints WHERE key='progress'").fetchone()[0]);progress.update({'offset':counts['compressed_payload_bytes'],'counts':counts});db.execute("UPDATE checkpoints SET value=? WHERE key='progress'",(json.dumps(progress),));db.commit();db.execute('PRAGMA wal_checkpoint(TRUNCATE)');db.close()
m['installed_bytes']=sum((out/x).stat().st_size for x in ['catalog.sqlite','articles.blocks']);m['reblocking']={'source':str(source),'source_installed_bytes':json.loads((source/'measurement.json').read_text())['installed_bytes'],'records_verified':records,'blocks':block_id,'seconds':time.monotonic()-t,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'text_and_wikitext':'Retained text byte-identical; wikitext exact source ranges with original full hash' if a.fragments else 'Byte-identical raw record payloads; no source supplement removed'};atomic(out/'measurement.json',m);atomic(out/'progress.json',progress);print(json.dumps(m,indent=2))
