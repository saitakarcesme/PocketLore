#!/usr/bin/env python3
"""Reconcile complete source dispositions, frozen priority and lazy block integrity."""
import argparse,collections,json,pathlib,resource,sqlite3,time
from reader import Reader
from acquire import atomic
p=argparse.ArgumentParser();p.add_argument('lane');p.add_argument('edition');p.add_argument('priority');p.add_argument('output');a=p.parse_args();lane=pathlib.Path(a.lane);root=lane/a.edition;reader=Reader(root);reports=[];start=time.monotonic();total=collections.Counter()
for s,(pack,db) in enumerate(zip(reader.packs,reader.dbs)):
 db.execute('ATTACH DATABASE ? AS chosen',(f'file:{a.priority}?mode=ro',));name=pack.name+'.parquet'
 expected=db.execute('SELECT count(*),sum(full) FROM chosen.priority WHERE shard=?',(name,)).fetchone()
 actual=db.execute("SELECT count(*),sum(tier='full'),sum(tier='lead') FROM articles").fetchone()
 invalid=db.execute("SELECT count(*) FROM articles a LEFT JOIN chosen.priority p ON a.id=p.id WHERE p.id IS NULL OR p.shard!=? OR p.source_row!=a.source_row OR p.title!=a.title OR p.full!=(a.tier='full')",(name,)).fetchone()[0]
 exclusions=db.execute('SELECT count(*) FROM exclusions').fetchone()[0];measurement=json.loads((pack/'measurement.json').read_text());bad_bounds=0
 source_rows=measurement['source_rows']
 disposition_conflicts=db.execute('SELECT count(*) FROM articles WHERE source_row<0 OR source_row>=?',(source_rows,)).fetchone()[0]
 disposition_conflicts+=db.execute('SELECT count(*) FROM exclusions WHERE source_row<0 OR source_row>=?',(source_rows,)).fetchone()[0]
 disposition_conflicts+=db.execute('SELECT count(*) FROM (SELECT source_row FROM articles GROUP BY source_row HAVING count(*)!=1)').fetchone()[0]
 disposition_conflicts+=db.execute('SELECT count(*) FROM articles a JOIN exclusions e ON e.source_row=a.source_row').fetchone()[0]
 if reader.blocked[s]:
  bad_bounds=db.execute('SELECT count(*) FROM blocks WHERE offset<0 OR length<=0 OR length>67108864 OR raw_length>134217728 OR offset+length>?',((pack/'articles.blocks').stat().st_size,)).fetchone()[0]
  bad_bounds+=db.execute('SELECT count(*) FROM articles a LEFT JOIN blocks b ON b.id=a.block_id WHERE b.id IS NULL OR a.offset<0 OR a.length!=a.raw_length OR a.offset+a.length>b.raw_length').fetchone()[0]
  overlap=db.execute('SELECT count(*) FROM (SELECT offset,lag(offset+length,1,0) OVER (ORDER BY offset) previous_end FROM blocks) WHERE offset!=previous_end').fetchone()[0]
  overlap+=db.execute('SELECT count(*) FROM (SELECT offset,lag(offset+length,1,0) OVER (PARTITION BY block_id ORDER BY offset) previous_end FROM articles) WHERE offset!=previous_end').fetchone()[0]
  overlap+=db.execute('SELECT count(*) FROM blocks b LEFT JOIN (SELECT block_id,sum(length) size FROM articles GROUP BY block_id) a ON a.block_id=b.id WHERE a.size IS NULL OR a.size!=b.raw_length').fetchone()[0]
  overlap+=int(db.execute('SELECT coalesce(max(offset+length),0) FROM blocks').fetchone()[0]!=(pack/'articles.blocks').stat().st_size)
 else:
  bad_bounds=db.execute('SELECT count(*) FROM articles WHERE offset<0 OR length<=0 OR length>67108864 OR raw_length>134217728 OR offset+length>?',((pack/'articles.blocks').stat().st_size,)).fetchone()[0]
  overlap=db.execute('SELECT count(*) FROM (SELECT offset,lag(offset+length,1,0) OVER (ORDER BY offset) previous_end FROM articles) WHERE offset!=previous_end').fetchone()[0]
 # Fixed source-row strata plus real math/notice records; hashes are checked by the actual reader.
 samples=list(db.execute('SELECT * FROM articles WHERE source_row%4096=0 ORDER BY source_row'))+list(db.execute('SELECT * FROM articles WHERE has_math=1 LIMIT 5'))+list(db.execute("SELECT * FROM articles WHERE rights='notice_candidate_raw_preserved' LIMIT 5"))+list(db.execute('SELECT * FROM articles ORDER BY raw_length DESC LIMIT 1'))
 samples=list({row['id']:row for row in samples}.values())
 largest_record_bytes=db.execute('SELECT max(raw_length) FROM articles').fetchone()[0]
 distinct_blocks=len({row['block_id'] for row in samples}) if reader.blocked[s] else len(samples)
 for row in samples:
  payload=reader.payload(s,row)
  assert payload['source_revision']==row['revision'] and payload['article_date']==row['modified'] and payload['url']==row['url'] and payload['tier']==row['tier']
  if row['rights']=='notice_candidate_raw_preserved':assert payload['wikitext'], 'Recognized notice supplement lost'
 integrity=db.execute('PRAGMA integrity_check').fetchone()[0]
 passed=(actual[0]==expected[0] and actual[1]==expected[1] and invalid==0 and bad_bounds==0 and overlap==0 and disposition_conflicts==0 and actual[0]+exclusions==source_rows and integrity=='ok')
 report={'shard':pack.name,'articles':actual[0],'full':actual[1] or 0,'lead':actual[2] or 0,'exclusions':exclusions,'expected_canonical':expected[0],'invalid_canonical_rows':invalid,'source_disposition_conflicts':disposition_conflicts,'bad_block_bounds':bad_bounds,'block_gaps_or_overlaps':overlap,'sampled_articles_checked':len(samples),'distinct_sampled_blocks_checked':distinct_blocks,'largest_record_bytes':largest_record_bytes,'sqlite_integrity':integrity,'passed':passed};reports.append(report);total.update({k:report[k] for k in ['articles','full','lead','exclusions','sampled_articles_checked','distinct_sampled_blocks_checked']});db.execute('DETACH DATABASE chosen')
files=list(root.glob('*/catalog.sqlite'))+list(root.glob('*/articles.blocks'))+list(root.glob('*.txt'))+list(root.glob('*.sqlite'))+list(root.glob('*/measurement.json'))+list(root.glob('*.json'))
result={'passed':len(reports)==15 and all(r['passed'] for r in reports),'shards':reports,'counts':dict(total),'installed_data_bytes':sum(f.stat().st_size for f in files),'budget_decimal_bytes':22000000000,'budget_passed_before_manifest':sum(f.stat().st_size for f in files)<=22000000000,'seconds':time.monotonic()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'platform':'LLMRig host only','limits':['Sampled block decoding, not exhaustive re-extraction of every article','Rights screening not independent rights clearance','No Android integration, hardware or inference acceptance']};atomic(a.output,result);reader.close();print(json.dumps({k:v for k,v in result.items() if k!='shards'},indent=2));raise SystemExit(0 if result['passed'] and result['budget_passed_before_manifest'] else 1)
