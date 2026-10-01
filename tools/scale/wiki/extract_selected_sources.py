#!/usr/bin/env python3
"""Bind frozen probes to actual selected source rows using bounded row-group reads."""
import argparse,json,pathlib,sqlite3,collections
import pyarrow.parquet as pq
from acquire import atomic
p=argparse.ArgumentParser();p.add_argument('lane');p.add_argument('priority');a=p.parse_args();lane=pathlib.Path(a.lane);out=lane/'receipts/selected-query-sources';out.mkdir(exist_ok=True);db=sqlite3.connect(f'file:{a.priority}?mode=ro',uri=True)
wanted={t for q in json.loads(pathlib.Path('docs/evidence/scale/wiki/queries-v1.json').read_text())['queries'] for t in q['expected_titles']};by_shard=collections.defaultdict(dict);missing=[]
found=set()
for ident,title,shard,source_row in db.execute('SELECT id,title,shard,source_row FROM priority WHERE title IN ('+','.join('?' for _ in wanted)+')',tuple(sorted(wanted))):
 by_shard[shard][source_row]=(ident,title);found.add(title)
missing=sorted(wanted-found)
pins={pathlib.Path(f['path']).name:f['lfs']['oid'] for f in json.loads(pathlib.Path('docs/evidence/scale/wiki/english-inventory.json').read_text())['files']};count=0
for shard,targets in by_shard.items():
 pf=pq.ParquetFile(lane/'bulk'/shard);base=0
 for g in range(pf.metadata.num_row_groups):
  end=base+pf.metadata.row_group(g).num_rows;needed={n for n in targets if base<=n<end}
  if needed:
   n=base
   for batch in pf.iter_batches(row_groups=[g],batch_size=64,use_threads=False):
    if batch.nbytes>2*1024**3:raise RuntimeError('Batch exceeds 2 GiB')
    for r in batch.to_pylist():
     if n in needed:
      assert (r['page_id'],r['title'])==targets[n]
      atomic(out/(str(r['page_id'])+'.json'),{'source_shard':shard,'source_sha256':pins[shard],'source_row':n,'record':r});count+=1
     n+=1
    if n>max(needed):break
  base=end
atomic(lane/'receipts/selected-query-source-summary.json',{'selected_sources':count,'missing_source_titles':missing});print(count,missing)
