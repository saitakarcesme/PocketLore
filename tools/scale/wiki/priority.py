#!/usr/bin/env python3
"""Canonical revisions and pageview tiers, with bounded SQLite sort/aggregation."""
import argparse,json,pathlib,resource,sqlite3,time
from acquire import atomic,digest
p=argparse.ArgumentParser();p.add_argument('lane');p.add_argument('--full',type=int,default=2000000);a=p.parse_args();lane=pathlib.Path(a.lane);out=lane/f'priority-{a.full}.sqlite'
if out.exists():raise SystemExit('Refuse to overwrite a priority freeze')
db=sqlite3.connect(out,uri=True);db.executescript('PRAGMA journal_mode=DELETE; PRAGMA synchronous=FULL; PRAGMA cache_size=-262144; PRAGMA temp_store=FILE; PRAGMA threads=1;');db.create_function('viewkey',1,lambda x:x.replace(' ','_').lower(),deterministic=True)
db.execute('ATTACH DATABASE ? AS census',(f'file:{lane / "census-v2.sqlite"}?mode=ro',));db.execute('ATTACH DATABASE ? AS rawviews',(f'file:{lane / "bulk/pageviews-neuml.sqlite"}?mode=ro',));t=time.monotonic()
assert db.execute('SELECT count(*) FROM census.completed').fetchone()[0]==15,'Census must be complete'
db.executescript('''
CREATE TABLE canonical AS SELECT id,title,shard,source_row,eligible,reason,revision FROM (SELECT *,row_number() OVER (PARTITION BY title ORDER BY revision DESC,id ASC,shard ASC,source_row ASC) title_rank FROM (SELECT *,row_number() OVER (PARTITION BY id ORDER BY revision DESC,shard ASC,source_row ASC) id_rank FROM census.source) WHERE id_rank=1) WHERE title_rank=1;
CREATE UNIQUE INDEX canonical_id ON canonical(id);
CREATE TABLE views(title TEXT PRIMARY KEY,views INTEGER NOT NULL,source_records INTEGER NOT NULL) WITHOUT ROWID;
INSERT INTO views SELECT title,SUM(views),COUNT(*) FROM rawviews.pages WHERE typeof(views)='integer' AND views>=0 GROUP BY title;
CREATE TABLE priority(id INTEGER PRIMARY KEY,title TEXT NOT NULL,shard TEXT NOT NULL,source_row INTEGER NOT NULL,views INTEGER,full INTEGER NOT NULL DEFAULT 0);
INSERT INTO priority(id,title,shard,source_row,views) SELECT c.id,c.title,c.shard,c.source_row,v.views FROM canonical c LEFT JOIN views v ON v.title=viewkey(c.title) WHERE c.eligible=1;
CREATE INDEX priority_order ON priority(views DESC,id ASC);
''')
db.execute('UPDATE priority SET full=1 WHERE id IN (SELECT id FROM priority ORDER BY views DESC,id ASC LIMIT ?)',(a.full,));db.commit()
result={'source_rows':db.execute('SELECT count(*) FROM census.source').fetchone()[0],'canonical_articles':db.execute('SELECT count(*) FROM canonical').fetchone()[0],'eligible_canonical':db.execute('SELECT count(*) FROM priority').fetchone()[0],'full':db.execute('SELECT count(*) FROM priority WHERE full=1').fetchone()[0],'lead':db.execute('SELECT count(*) FROM priority WHERE full=0').fetchone()[0],'observed_views':db.execute('SELECT count(*) FROM priority WHERE views IS NOT NULL').fetchone()[0],'full_with_unknown_views':db.execute('SELECT count(*) FROM priority WHERE full=1 AND views IS NULL').fetchone()[0],'pageview_source_rows':db.execute('SELECT SUM(source_records) FROM views').fetchone()[0],'pageview_unique_keys':db.execute('SELECT count(*) FROM views').fetchone()[0],'normalization':'Literal underscore-for-space then Unicode lower; no fuzzy match; aggregates same stored view title','aggregation_period':'unknown; precomputed database in NeuML June 2025 dataset','seconds':time.monotonic()-t,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'per_shard':db.execute('SELECT shard,count(*),sum(full) FROM priority GROUP BY shard').fetchall(),'sha256_sources':{'census':digest(lane/'census-v2.sqlite'),'pageviews':'409c4d1643171d050d77c9ea03416d77dac3a538ff8a78f59e3344df9bb49dc1'}}
db.close();result['sha256']=digest(out);atomic(lane/f'priority-{a.full}.json',result);print(json.dumps(result,indent=2))
