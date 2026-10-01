#!/usr/bin/env python3
"""Freeze deterministic complete-shard Android probes from sealed local bytes."""
import pathlib,json,sqlite3,zlib,hashlib
ROOT=pathlib.Path('/home/isa/PocketLore-control/scale-workers');OUT=pathlib.Path('docs/evidence/full-scale/sweep');OUT.mkdir(exist_ok=True)
def ro(p):return sqlite3.connect('file:'+str(p)+'?mode=ro&immutable=1',uri=True)
rows=[]
for kind in ['wiki','places']:
 m=json.loads(pathlib.Path('docs/evidence/full-scale/'+kind+'-all.json').read_text());base=ROOT/('wiki/edition-v7' if kind=='wiki' else 'places/data')
 for shard in m['shards']:
  c=ro(base/shard/ 'catalog.sqlite' if kind=='wiki' else base/shard)
  if kind=='wiki':
   r=c.execute('select id,title,hex(text_sha256) from articles where length<=33554432 order by id limit 1').fetchone();n,f,l=c.execute("select count(*),sum(tier='full'),sum(tier='lead') from articles").fetchone();probe={'id':str(r[0]),'title':r[1],'source_sha256':r[2]};counts=dict(documents=n,full_articles=f,leads=l)
  else:
   r=c.execute('select id,payload,sha256 from block order by id limit 1').fetchone();raw=zlib.decompress(r[1]);assert hashlib.sha256(raw).hexdigest()==r[2];v=json.loads(raw)[0];probe={'ordinal':v[0],'lat':v[1],'lon':v[2],'id':v[4]['id'],'source_block_sha256':r[2]};counts={'source_records':c.execute('select sum(records) from block').fetchone()[0]}
  c.close();rows.append(dict(kind=kind,shard=shard,probe=probe,counts=counts))
plan={'kind':'Rolling complete-shard Android compatibility, not simultaneous full installation','frozen_rows':rows,'prior_protocol':'tools/evaluation/full-scale/protocol.json','rules':['exact expected wiki source ID/hash','actual bounded spatial lookup and source inspection','all15 wiki and16 place shards; failures retained','shared metadata-only collection between primary shards','no rights clearance or generation','no full-install/update acceptance from rolling residency']}
with (OUT/'plan.json').open('x') as f:json.dump(plan,f,indent=2);f.write('\n')
