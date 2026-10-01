#!/usr/bin/env python3
"""Prepare source-review inputs without model identity or builder ratings."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[3];E=R/'docs/evidence/model-capability'
def main():
 protocol=json.loads((R/'tools/evaluation/model-capability/protocol.json').read_text());packet=[];key={}
 for model in [e['id'] for e in json.loads((R/'tools/evaluation/model-capability/execution-v2.json').read_text())['models']]:
  for c in protocol['cases']:
   row=json.loads((E/'run'/model/(c['id']+'.json')).read_text())
   blind=hashlib.sha256(('capability-v1:'+model+':'+c['id']).encode()).hexdigest()[:16]
   packet.append({'review_id':blind,'case':c['id'],'question':c['question'],'offered_evidence':c['sources'],'evidence':[s for s in c['sources'] if s['text'] in row['prompt']],'expectation':c['expectation'],'answerable':c['answerable'],'production_route':row['route'],'production_text':row['text'],'raw_generation':row['resolved_raw'],'diagnostic_only':row['diagnostic_only'],'prompt':row['prompt'],'instruction':'Judge claims only against evidence actually retained in the recorded prompt, not dropped offered evidence, including subject, conditions and temporal scope. Separately rate factual support, completeness and usefulness; syntax and overlap are not entailment. Production fallback is not generated success.'})
   key[blind]={'model':model,'case':c['id']}
 packet.sort(key=lambda x:x['review_id'])
 (E/'blind-review.json').write_text(json.dumps({'classification':'Public development; identity-blind source review inputs; no independent review performed by this builder','rows':packet},indent=2)+'\n')
 (E/'identity-key.json').write_text(json.dumps(key,indent=2)+'\n')
if __name__=='__main__':main()
