#!/usr/bin/env python3
"""Frozen title recall, raw misses, bounded source checks; never claims answer entailment."""
import argparse,hashlib,json,os,pathlib,resource,statistics,time
from reader import Reader
from acquire import atomic,digest
p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('output');p.add_argument('--queries',default='docs/evidence/scale/wiki/queries-v1.json');a=p.parse_args()
output=pathlib.Path(a.output);partial=output.with_suffix(output.suffix+'.cases.jsonl')
if output.exists() or partial.exists():raise SystemExit('Refuse to overwrite evaluation evidence')
start=time.monotonic();reader=Reader(a.root);opened=time.monotonic();cases=[]
for q in json.loads(pathlib.Path(a.queries).read_text())['queries']:
 result=reader.search(q['query']);got=[h['title'] for h in result['hits']]
 support=[]
 for title in q['expected_titles']:
  source=reader.source(title)
  if source:
   s,row,payload=source
   frozen=q.get('frozen_source');frozen_match=None
   if frozen:
    cfg=json.loads(reader.dbs[s].execute("SELECT value FROM checkpoints WHERE key='config'").fetchone()[0]);frozen_match=(row['id']==frozen['id'] and row['revision']==frozen['revision'] and row['modified']==frozen['date'] and row['source_row']==frozen['source_row'] and payload['source_text_sha256']==frozen['source_text_sha256'] and cfg['source_sha256']==frozen['parquet_sha256'] and payload['text'].startswith(frozen['lead_excerpt']))
   support.append({'title':title,'id':row['id'],'revision':row['revision'],'modified':row['modified'],'url':row['url'],'tier':row['tier'],'text_sha256':row['text_sha256'].hex() if isinstance(row['text_sha256'],bytes) else row['text_sha256'],'wikitext_sha256':row['wikitext_sha256'].hex() if isinstance(row['wikitext_sha256'],bytes) else row['wikitext_sha256'],'source_shard':reader.packs[s].name,'lead_excerpt':payload['text'][:700],'literal_source_available':True,'frozen_source_match':frozen_match,'claim_entailment':'unreviewed'})
  else:support.append({'title':title,'literal_source_available':False})
 cases.append({**q,**result,'matched_titles':[t for t in q['expected_titles'] if t in got],'all_titles_at_10':bool(q['expected_titles']) and all(t in got for t in q['expected_titles']),'source_audit':support,'absence_claim':'No answer generated; related hits do not support requested absent facts' if not q['expected_titles'] else None})
 with partial.open('a') as f:f.write(json.dumps(cases[-1])+'\n');f.flush();os.fsync(f.fileno())
 print(json.dumps({'query':q['id'],'milliseconds':result['milliseconds'],'all_titles_at_10':cases[-1]['all_titles_at_10']}),flush=True)
lat=sorted(c['milliseconds'] for c in cases);supported=[c for c in cases if c['expected_titles']]
summary={'queries_sha256':digest(a.queries),'platform':'LLMRig host, uncontrolled OS cache (no reset), no inference; not Android acceptance','queries':len(cases),'supported_title_cases':len(supported),'all_titles_at_10':sum(c['all_titles_at_10'] for c in supported),'missing_cases':[c['id'] for c in supported if not c['all_titles_at_10']],'frozen_source_mismatch_cases':[c['id'] for c in cases if c.get('frozen_source') and not all(s.get('frozen_source_match',False) for s in c['source_audit'])],'absence_controls':sum(not c['expected_titles'] for c in cases),'absence_controls_with_hits':sum(not c['expected_titles'] and bool(c['hits']) for c in cases),'absence_answer_abstention':'Not implemented or scored by this retrieval-only tool','source_locator_missing':[c['id'] for c in supported if not all(s['literal_source_available'] for s in c['source_audit'])],'latency_p50_ms':statistics.median(lat),'latency_p95_ms':lat[int(.95*(len(lat)-1))],'latency_max_ms':max(lat),'open_seconds':opened-start,'total_seconds':time.monotonic()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'max_candidates':max(c['candidates'] for c in cases),'total_articles':reader.total,'query_categories':sorted(set(c['category'] for c in cases))}
atomic(a.output,{'summary':summary,'cases':cases});print(json.dumps(summary,indent=2));reader.close()
