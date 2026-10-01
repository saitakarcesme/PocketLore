"""Seal explicit builder source assessments; never infer entailment from token overlap."""
from pathlib import Path
import json,hashlib,sys
R=Path(__file__).resolve().parents[3];E=R/'docs/evidence/obligation-ledger'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def seal(run,labels):
 cases=json.loads((R/'tools/evaluation/source-plan/fixtures.json').read_text())['cases'];reviews={};counts={'eligible':0,'withheld':0,'unsupported':0,'useful':0,'absent_withheld':0,'plan_calls':0,'prose_calls':0}
 for c in cases:
  v=json.loads((run/'results'/(c['id']+'.json')).read_text());a=labels[c['id']];candidate=v['route']=='REVIEW_CANDIDATE';counts['eligible' if candidate else 'withheld']+=1
  for stage,key in [('plan','plan_calls'),('draft','prose_calls')]:counts[key]+=v[stage]['tokens']>0
  if c['expected_route']=='absent' and not candidate:counts['absent_withheld']+=1
  if candidate:
   assert len(a['claims'])==len(v['claims']);assert all(x['text']==y['text'] for x,y in zip(a['claims'],v['claims']));counts['unsupported']+=not a['supported'];counts['useful']+=all(a[k] for k in ['supported','complete','useful'])
  else:assert a['supported'] is None and a['useful'] is False
  reviews[c['id']]={**a,'record_sha256':hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()}
 (E/'review.json').write_text(json.dumps({'reviewer':'builder source inspection; not independent criticism or production authorization','cases':reviews},indent=2)+'\n')
 (E/'metrics.json').write_text(json.dumps({'counts':counts,'eligible_field_means':'Structurally valid review candidates only; no publication authorization','production_published':0,'independent_review':'pending'},indent=2)+'\n')
if __name__=='__main__':seal(Path(sys.argv[1]),json.loads(Path(sys.argv[2]).read_text()))
