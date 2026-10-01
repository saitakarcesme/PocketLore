"""Expose exact source inputs and actual prose without builder verdicts or classifier scores."""
from pathlib import Path
import json,base64,hashlib
R=Path(__file__).resolve().parents[3];E=R/'docs/evidence/independent-linking';S=E/'scoring';rows={x.split('\t')[0]:x.split('\t') for x in (S/'inputs/drafts.tsv').read_text().splitlines()};records=json.loads((S/'final/linked.json').read_text());scores={x['key']:x for x in map(json.loads,(S/'scores.jsonl').read_text().splitlines())};cards=[];failure_scores=[];review=json.loads((E/'review.json').read_text())['cases'];origins=json.loads((S/'origins.json').read_text());decode=lambda s:base64.b64decode(s).decode()
for v in records:
 id=v['id'];sources=[]
 for line in (S/'inputs'/(id+'.tsv')).read_text().splitlines():sources.append(dict(zip(['edition','id','document_sha256','passage_sha256','title','date','rights','text'],[decode(x) for x in line.split('\t')])))
 raw=decode(rows[id][2]);raw=decode(rows[id][5]) if raw=='@PROBE' else raw
 cards.append({'id':id,'question':v['question'],'kind':origins[id]['type'],'raw':raw,'final_rendered':v['rendered'],'claims':v['claims'],'sources':sources,'origin_sha256':origins[id]['sha256']})
 if v['claims']:
  byid={s['id']:s for s in sources};sc=[]
  for c in v['claims']:
   premise=''.join(byid[r['passage']]['title']+': '+r['text']+'\n' for r in c['references']);key=hashlib.sha256((premise+'\0'+c['subject']+': '+c['text']).encode()).hexdigest();sc.append({'claim':c['text'],'pair_key':key,**scores[key]})
  failure_scores.append({'id':id,'builder_supported':review[id]['supported'],'selected_complete_claim_scores':sc})
(E/'independent-review-inputs.json').write_text(json.dumps({'purpose':'Actual drafts, final prose and exact sources without builder labels or classifier/self-audit decisions. Empty final prose means withheld. Constructed probes are explicitly labeled, never generated success.','cases':cards},indent=2)+'\n');(E/'selected-claim-scores.json').write_text(json.dumps(failure_scores,indent=2)+'\n')
