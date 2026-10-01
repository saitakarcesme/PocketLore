#!/usr/bin/env python3
"""Shared bounded zlib blocks, binary checksums, and source-identical positional FTS."""
import argparse, collections, datetime, fcntl, hashlib, json, os, pathlib, re, resource, sqlite3, time, zlib
import pyarrow as pa
import pyarrow.parquet as pq
from acquire import atomic, digest
from supplements import extract as extract_supplement
from index_text import body as index_body,STOP as INDEX_STOP
pa.set_cpu_count(1); pa.set_io_thread_count(1)
SCHEMA='''
PRAGMA journal_mode=WAL;
PRAGMA wal_autocheckpoint=16384;
PRAGMA synchronous=FULL;
PRAGMA cache_size=-786432;
PRAGMA temp_store=FILE;
PRAGMA threads=0;
CREATE TABLE IF NOT EXISTS articles(id INTEGER PRIMARY KEY,title TEXT NOT NULL,url TEXT NOT NULL,revision INTEGER,modified TEXT,tier TEXT NOT NULL,views INTEGER,offset INTEGER NOT NULL,length INTEGER NOT NULL,raw_length INTEGER NOT NULL,sha256 BLOB NOT NULL,text_sha256 BLOB NOT NULL,wikitext_sha256 BLOB NOT NULL,has_math INTEGER NOT NULL,source_row INTEGER NOT NULL,rights TEXT NOT NULL,block_id INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS blocks(id INTEGER PRIMARY KEY,offset INTEGER NOT NULL,length INTEGER NOT NULL,raw_length INTEGER NOT NULL,sha256 BLOB NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS title_index ON articles(title);
CREATE TABLE IF NOT EXISTS aliases(alias TEXT NOT NULL,target INTEGER NOT NULL,kind TEXT NOT NULL,PRIMARY KEY(alias,target)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS exclusions(source_row INTEGER PRIMARY KEY,page_id INTEGER,title TEXT,reason TEXT NOT NULL);
CREATE VIRTUAL TABLE IF NOT EXISTS search USING fts5(title,body,content='',tokenize='unicode61');
CREATE TABLE IF NOT EXISTS checkpoints(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE VIRTUAL TABLE IF NOT EXISTS terms USING fts5vocab(search,'row');
'''
# Conservative unresolved markers; raw wikitext is retained for every admitted article.
BAD=re.compile(r'\{\{\s*(?:copyvio|copy-paste|copypaste|copyright violation|cv-unsure|close paraphrasing|non-free|fair use|permission pending|permission received|OTRS pending|VRT pending)\b',re.I)
NOTICE=re.compile(r'CIA World Factbook|CIA factbook|Factbook|EB1911|DNB|DANFS|Nuttall|Catholic Encyclopedia|Jewish Encyclopedia|USGS|copyright|attribut|public.domain|incorporat.{0,40}(?:text|material)|CC.BY|GFDL|permission|\{\{\s*(?:PD[- ]|1911|DNB|EB1911|catholic|Nuttall)',re.I)
def notice_candidate(wikitext):
    lower=wikitext.lower()
    return bool(re.search(r'\{\{\s*pd[- ]',lower)) or any(marker in lower for marker in ('copyright','attribut','public domain','public-domain','incorporat','cc-by','cc by','gfdl','permission','{{pd-','{{pd ','1911','dnb','danfs','nuttall','catholic encyclopedia','jewish encyclopedia','cia world factbook','cia factbook','usgs'))
def lead(text):
    return re.split(r'(?m)^##\s',text,maxsplit=1)[0].rstrip()+'\n'
def eligibility(r):
    required=['text','title','url','date_modified','version','page_id','wikitext']
    missing=[k for k in required if not r.get(k)]
    if missing:return 'missing:'+','.join(missing)
    if r.get('in_language')!='en' or r.get('wikiname')!='enwiki':return 'not_english_wikipedia'
    if not r['url'].startswith('https://en.wikipedia.org/wiki/'):return 'unexpected_url'
    m=BAD.search(r['wikitext'])
    if m:return 'unresolved_rights_marker:'+m.group(0)
    return None

def run(args):
    out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    lock=(out/'writer.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    source=pathlib.Path(args.source);db=sqlite3.connect(out/'catalog.sqlite');db.executescript(SCHEMA)
    cfg={'source':str(source),'source_sha256':args.sha256,'mode':args.mode,'priority_sha256':(getattr(args,'priority_sha',None) or digest(args.priority)) if args.priority else None,'schema':3,'block_max_records':64,'block_target_bytes':8388608,'supplement':getattr(args,'supplement','full'),'compression_level':getattr(args,'compression_level',6),'index_policy':getattr(args,'index_policy','verbatim')}
    cfg['builder_sqlite_cache_kib']=786432
    cfg['notice_empty_fallback']='complete_source_for_screening_candidate'
    cfg['producer_sources']={name:digest(pathlib.Path(__file__).parent/name) for name in ['build_v3.py','supplements.py','index_text.py','acquire.py']}
    old=db.execute("SELECT value FROM checkpoints WHERE key='config'").fetchone()
    if old and json.loads(old[0])!=cfg:raise RuntimeError('Immutable build configuration differs; use a new edition')
    db.execute('INSERT OR IGNORE INTO checkpoints VALUES (?,?)',('config',json.dumps(cfg)));db.commit()
    old=db.execute("SELECT value FROM checkpoints WHERE key='progress'").fetchone();progress=json.loads(old[0]) if old else {'rows':0,'offset':0,'counts':{},'seconds':0}
    counts=collections.Counter(progress['counts']);t=time.monotonic();startrow=progress['rows']
    blocks=(out/'articles.blocks').open('r+b' if (out/'articles.blocks').exists() else 'w+b')
    # SQLite commit is authoritative. Preserve uncommitted trailing bytes before truncation.
    blocks.seek(0,2)
    if blocks.tell()>progress['offset']:
        blocks.seek(progress['offset']);orphan=out/f'orphan-{time.time_ns()}.blocks'
        with orphan.open('wb') as f:
            while b:=blocks.read(8*1024*1024):f.write(b)
        blocks.truncate(progress['offset'])
    blocks.seek(progress['offset'])
    block_id=db.execute('SELECT coalesce(max(id),0) FROM blocks').fetchone()[0]
    pending=[];buffer=bytearray();pending_ids=set();pending_titles=set()
    def flush_block():
        nonlocal block_id,pending,buffer,pending_ids,pending_titles
        if not pending:return
        block_id+=1;compressed=zlib.compress(buffer,args.compression_level);off=blocks.tell();blocks.write(compressed)
        if len(buffer)>128*1024**2 or len(compressed)>64*1024**2:raise RuntimeError('Block exceeds reader bound')
        db.execute('INSERT INTO blocks VALUES (?,?,?,?,?)',(block_id,off,len(compressed),len(buffer),hashlib.sha256(buffer).digest()))
        db.executemany('INSERT INTO articles VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',[tuple(row+[block_id]) for row in pending])
        counts['compressed_payload_bytes']+=len(compressed);counts['blocks']+=1;counts['max_block_raw_bytes']=max(counts['max_block_raw_bytes'],len(buffer))
        pending=[];buffer=bytearray();pending_ids=set();pending_titles=set()
    priority=sqlite3.connect(f'file:{args.priority}?mode=ro',uri=True) if args.priority else None
    if priority:
        priority.execute('PRAGMA cache_size=-65536');priority.execute('PRAGMA mmap_size=0')
    selected=iter(priority.execute('SELECT id,views,full,source_row FROM priority WHERE shard=? ORDER BY source_row',(source.name,))) if priority else iter(())
    selected_row=next(selected,None)
    while selected_row and selected_row[3]<startrow:selected_row=next(selected,None)
    pf=pq.ParquetFile(source);rowno=0;batchmax=0
    for batch in pf.iter_batches(batch_size=64,use_threads=False):
        batchmax=max(batchmax,batch.nbytes)
        if batch.nbytes>2*1024**3:raise RuntimeError('Arrow batch exceeds 2 GiB')
        if rowno+batch.num_rows<=startrow:rowno+=batch.num_rows;continue
        rows=batch.to_pylist()
        for r in rows:
            n=rowno;rowno+=1
            if n<startrow:continue
            counts['source_rows']+=1
            why=eligibility(r)
            if not why and not priority and (r['page_id'] in pending_ids or r['title'] in pending_titles or db.execute('SELECT 1 FROM articles WHERE id=? OR title=?',(r['page_id'],r['title'])).fetchone()):
                why='duplicate_page_or_title_in_shard_keep_first'
            score=None
            if selected_row and selected_row[3]==n:
                if selected_row[0]!=r['page_id']:raise RuntimeError('Canonical source row/page ID mismatch')
                score=(selected_row[1],selected_row[2],source.name,n);selected_row=next(selected,None)
            if not why and priority and (not score or (score[2],score[3])!=(source.name,n)):
                why='not_selected_canonical_revision'
            if why:
                db.execute('INSERT INTO exclusions VALUES (?,?,?,?)',(n,r.get('page_id'),r.get('title'),why));counts['excluded']+=1;continue
            tier='full' if args.mode=='full' or (score and score[1]) else 'lead'
            text=r['text'] if tier=='full' else lead(r['text'])
            notice=notice_candidate(r['wikitext'])
            keep_wiki=args.supplement in ('full','lean') or notice or bool(r['has_math']) or bool(re.search(r'<(?:math|chem)|\{\{\s*(?:convert|cvt|val|math|physconst)\b',r['wikitext'],re.I))
            retained_wiki=r['wikitext'] if keep_wiki else ''
            wiki_scope='complete' if keep_wiki else 'archived_in_pinned_source_only';wiki_ranges=[[0,len(r['wikitext'])]] if keep_wiki else []
            if keep_wiki and args.supplement in ('fragments','lean'):retained_wiki,wiki_ranges,wiki_scope=extract_supplement(r['wikitext'],lean=args.supplement=='lean',has_math=bool(r['has_math']),preserve_empty_candidate=notice)
            payload={'text':text,'wikitext':retained_wiki,'source_wikitext_sha256':hashlib.sha256(r['wikitext'].encode()).hexdigest(),'wikitext_scope':wiki_scope,'wikitext_ranges':wiki_ranges,'infoboxes':r.get('infoboxes'),'source_text_sha256':hashlib.sha256(r['text'].encode()).hexdigest(),'source_revision':r['version'],'article_date':r['date_modified'],'url':r['url'],'tier':tier,'notice_status':('exact_source_ranges_not_independently_cleared' if args.supplement in ('fragments','lean') else 'raw_wikitext_retained_not_independently_cleared') if keep_wiki else 'no_recognized_notice_source_archive_unreviewed','changes':'FineWiki HTML extraction; PocketLore lead selection when tier=lead; source supplement may contain exact ranges, as labeled by wikitext_scope'}
            raw=json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode()
            if pending and (len(buffer)+len(raw)>8388608 or len(pending)>=64):flush_block()
            off=len(buffer);buffer.extend(raw)
            rights='notice_candidate_raw_preserved' if notice else 'dataset_license_only_unreviewed'
            pending_ids.add(r['page_id']);pending_titles.add(r['title'])
            pending.append([r['page_id'],r['title'],r['url'],r['version'],r['date_modified'],tier,score[0] if score else None,off,len(raw),len(raw),hashlib.sha256(raw).digest(),hashlib.sha256(text.encode()).digest(),hashlib.sha256(retained_wiki.encode()).digest(),int(r['has_math'] or False),n,rights])
            norm=r['title'].replace('_',' ').casefold()
            db.execute('INSERT OR IGNORE INTO aliases VALUES (?,?,?)',(norm,r['page_id'],'normalized_title'))
            # Only literal redirect directives are authoritative; do not invent aliases from prose.
            for target in re.findall(r'(?im)^\s*#redirect\s*\[\[([^\]|#]+)',r['wikitext']):
                db.execute('INSERT OR IGNORE INTO aliases VALUES (?,?,?)',(r['title'].casefold(),r['page_id'],'source_redirect_unresolved:'+target))
            db.execute('INSERT INTO search(rowid,title,body) VALUES (?,?,?)',(r['page_id'],r['title'],index_body(text) if args.index_policy=='reader_stopwords_v1' else text))
            counts[tier]+=1;counts[tier+'_text_bytes']+=len(text.encode());counts['raw_payload_bytes']+=len(raw);counts['retained_text_bytes']+=len(text.encode());counts['wikitext_bytes']+=len(retained_wiki.encode());counts['wikitext_'+wiki_scope]+=1;counts['math_articles']+=int(r['has_math'] or False);counts[rights]+=1
        if rowno%4096<64 or rowno==pf.metadata.num_rows:
            flush_block();blocks.flush();os.fsync(blocks.fileno())
            progress={'rows':rowno,'offset':blocks.tell(),'counts':dict(counts),'seconds':progress['seconds']+time.monotonic()-t};t=time.monotonic()
            db.execute('INSERT OR REPLACE INTO checkpoints VALUES (?,?)',('progress',json.dumps(progress)));db.commit()
            atomic(out/'progress.json',progress)
            print(json.dumps({'rows':rowno,'total':pf.metadata.num_rows,'full':counts['full'],'lead':counts['lead'],'excluded':counts['excluded']}),flush=True)
    assert not pending, 'Final batch must be checkpointed'
    db.execute("INSERT INTO search(search) VALUES ('optimize')");db.commit()
    db.execute('VACUUM')
    db.execute("INSERT INTO search(search) VALUES ('integrity-check')");db.commit()
    db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    integrity=db.execute('PRAGMA integrity_check').fetchone()[0]
    result={'source_sha256':args.sha256,'source_rows':pf.metadata.num_rows,'counts':dict(counts),'seconds':progress['seconds'],'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'max_arrow_batch_bytes':batchmax,'sqlite_integrity':integrity,'platform':'LLMRig Linux host staging, not Android','installed_bytes':sum((out/x).stat().st_size for x in ['catalog.sqlite','articles.blocks']),'sqlite_version':sqlite3.sqlite_version,'arrow_version':pa.__version__,'source_complete':rowno==pf.metadata.num_rows}
    atomic(out/'measurement.json',result);db.close();blocks.close();print(json.dumps(result),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);p.add_argument('--sha256',required=True);p.add_argument('--mode',choices=['full','tiered'],default='full');p.add_argument('--priority');p.add_argument('--priority-sha');p.add_argument('--supplement',choices=['full','screened','fragments','lean'],default='full');p.add_argument('--index-policy',choices=['verbatim','reader_stopwords_v1'],default='verbatim');p.add_argument('--compression-level',type=int,choices=range(1,10),default=6);run(p.parse_args())
