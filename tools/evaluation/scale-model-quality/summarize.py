#!/usr/bin/env python3
"""Derive measurements and obligation/source links from frozen outputs; no semantic scoring."""
from pathlib import Path
import json,math,re
R=Path(__file__).resolve().parents[3];F=Path(__file__).resolve().parent;E=R/'docs/evidence/scale-model-quality'
protocol=json.loads((F/'protocol.json').read_text());selection=json.loads((E/'selection.json').read_text())
def percentiles(values):
 values=sorted(values)
 return {'n':len(values),'p50':values[math.ceil(.50*len(values))-1],'p95':values[math.ceil(.95*len(values))-1],'min':values[0],'max':values[-1]}
metrics={'definitions':{'percentile':'Nearest rank: sorted values[ceil(p*n)-1], no interpolation; 48 cases/model, not repeated identical requests.','first_token_ms':'From generateChat entry, includes prompt prefill and context creation, excludes preceding model load/token count.','total_ms':'Same start through generation and incremental output writes; no retrieval in this oracle screen.','load_ms':'Native create/load, separate from lazy context/repacking/prefill. Preflight SHA reads can warm the OS page cache; not disk-cold latency. One model handle per process, fresh context for each question.','native_peaks':'Maximum callback-observed native buffers: leases, contexts, model, KV, compute bytes. Not OS PSS or isolated allocation peaks.','rss_swap':'Process /proc status sampled once per second; possible missed transients.','published':'None: this architecture is experimental and not wired to production. Screen candidates require source review.'},'models':{}}
links=[]
for name,path in selection['runs'].items():
 d=R/path;review=json.loads((E/'reviews'/f'{name}.json').read_text())['cases'];rows=[json.loads((d/(c['id']+'.json')).read_text()) for c in protocol['cases']];receipt=json.loads((d/'receipt.json').read_text());memory=json.loads((d/'memory.json').read_text())
 stat={'load_ms':json.loads((d/'load.json').read_text())['load_ms'],'elapsed_s':receipt['elapsed_s'],'model_file_bytes':receipt['pin']['bytes'],'first_token_ms':percentiles([v['first_token_ms'] for v in rows]),'total_ms':percentiles([v['total_ms'] for v in rows]),'prompt_tokens':percentiles([v['prompt_tokens'] for v in rows]),'output_tokens':percentiles([v['tokens'] for v in rows]),'native_peak_bytes':[max(v['native_peaks'][i] for v in rows) for i in range(2,5)],'rss_peak_bytes':max(int(m.get('VmRSS','0 kB').split()[0])*1024 for m in memory),'swap_peak_bytes':max(int(m.get('VmSwap','0 kB').split()[0])*1024 for m in memory),'kinds':{}}
 for c,v in zip(protocol['cases'],rows):
  a=review[c['id']];k=stat['kinds'].setdefault(c['kind'],{'n':0,'candidate':0,'useful_draft':0,'unsupported_fact_draft':0,'citation_support_failure':0,'incomplete':0});k['n']+=1;k['candidate']+=v['screen_route']=='CANDIDATE_FOR_SOURCE_REVIEW';k['useful_draft']+=a['fully_useful_draft'];k['unsupported_fact_draft']+=not a['all_facts_supported'];k['citation_support_failure']+=not a['cited_claims_supported'];k['incomplete']+=not a['obligations_complete']
  obligations=[]
  for i,o in enumerate(c['obligations'],1):
   # Retain all repeats; this is evidence linkage, not a support assertion.
   pieces=re.findall(r'(?ms)^O'+str(i)+r':\s*(.*?)(?=^O[1-4]:|\Z)',v['raw'])
   labels=sorted({int(n) for piece in pieces for n in re.findall(r'\[S([1-6])\]',piece)})
   obligations.append({'obligation':o,'raw_slots':pieces,'cited_sources':[c['sources'][n-1] for n in labels],'distinct_cited_documents':len({c['sources'][n-1]['url'] for n in labels})})
  links.append({'model':name,'case':c['id'],'screen_route':v['screen_route'],'builder_assessment':a,'obligations':obligations})
 metrics['models'][name]=stat
(E/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n');(E/'obligation-source-review.json').write_text(json.dumps(links,indent=2)+'\n')
print(json.dumps(metrics,indent=2))
