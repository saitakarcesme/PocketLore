"""Post-source-freeze public title probes; not semantic usefulness or admitted research."""
import json,sqlite3,time,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[3];packet=json.loads((R/'docs/evidence/broad-corpus-admission-review.json').read_text());c=sqlite3.connect(R/'downloads/official-wiki/index-v1/provenance.sqlite');c.row_factory=sqlite3.Row;rows=[]
for sample in packet['source_records']:
 d=sample['document'];query='"'+d['title'].replace('"','""')+'"';start=time.monotonic()
 result=[dict(r) for r in c.execute('select title,text,doc from search where title match ? limit 4',(query,))]
 rows.append({'query':query,'expected_source_identity':d['id'],'elapsed_ms':(time.monotonic()-start)*1000,'raw_results':result,'expected_source_found':any(int(r['doc'])==d['id'] for r in result),'route':'HOST_PENDING_SOURCE_DISCOVERY_ONLY','supported_research_answer':False})
p=R/'downloads/official-wiki/query-probes-repaired.json';assert not p.exists();p.write_text(json.dumps({'source_freeze_sha256':hashlib.sha256((R/'docs/evidence/broad-corpus-admission-review.json').read_bytes()).hexdigest(),'scope':'16 systematic first-shard public title probes after source freeze; lexical lookup only, not paraphrase or unseen evaluation','results':rows},indent=2)+'\n');print(sum(r['expected_source_found'] for r in rows),'of',len(rows),'source identities retrieved; no research admission')
