#!/usr/bin/env python3
"""Exact full-text source bytes across the canonical census, independent of queries."""
import argparse,json,pathlib,resource,sqlite3,time
from acquire import atomic
p=argparse.ArgumentParser();p.add_argument('lane');p.add_argument('priority');p.add_argument('output');a=p.parse_args();lane=pathlib.Path(a.lane);db=sqlite3.connect(a.priority,uri=True);db.executescript('PRAGMA query_only=ON; PRAGMA cache_size=-262144; PRAGMA mmap_size=0; PRAGMA temp_store=FILE; PRAGMA threads=1;');db.execute('ATTACH DATABASE ? AS source',(f'file:{lane / "census-v2.sqlite"}?mode=ro',));db.execute('PRAGMA source.cache_size=-262144');start=time.monotonic();rows=db.execute('''SELECT p.id,p.shard,p.source_row,p.views,s.text_bytes FROM priority p JOIN source.source s ON s.shard=p.shard AND s.source_row=p.source_row ORDER BY p.views DESC,p.id ASC LIMIT 2000000''');totals={};n=0;total=0;shards={}
for ident,shard,source_row,views,text_bytes in rows:
 n+=1;total+=text_bytes;shards[shard]=shards.get(shard,0)+text_bytes
 if n in [500000,1000000,1250000,1500000,1750000,2000000]:
  totals[str(n)]={'full_text_bytes':total,'cutoff_views':views,'per_shard_full_text_bytes':dict(shards)};print(n,total,flush=True)
result={'priority':str(pathlib.Path(a.priority).resolve()),'ranking':'views descending, page ID ascending, same frozen canonical set','counts':totals,'seconds':time.monotonic()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'limitations':'Exact source full-text bytes only; lead/index/supplement/compression sizes must be measured separately'};atomic(a.output,result);print(json.dumps(result,indent=2))
