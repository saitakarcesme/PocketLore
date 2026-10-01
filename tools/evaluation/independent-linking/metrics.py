"""Derive reported route/quality counts and timings from sealed actual records and builder reviews."""
from pathlib import Path
import json,math
R=Path(__file__).resolve().parents[3];E=R/'docs/evidence/independent-linking';F=Path(__file__).parent
v=json.loads((E/'scoring/final/linked.json').read_text());review=json.loads((E/'review.json').read_text())['cases'];fixtures=json.loads((F/'fixtures.json').read_text());cases={c['id']:c for c in json.loads((R/'tools/evaluation/scale-model-quality/protocol.json').read_text())['cases']+json.loads((R/'tools/evaluation/obligation-binding/new-cases.json').read_text())['cases']+fixtures['cases']}
counts={'old_useful_eligible':0,'new_useful_eligible':0,'unsupported_eligible':0,'old_absent_withheld':0,'new_absent_withheld':0,'eligible':0,'withheld':0,'historical_unsupported_eligible':0,'probe_false_approvals':0,'probe_false_rejections':0};pop={}
for x in v:
 id=x['id'];r=review[id];eligible=x['route']=='SCREEN_ELIGIBLE';prefix=id[0];p=pop.setdefault(prefix,{'n':0,'eligible':0,'supported_eligible':0,'useful_eligible':0,'unsupported_eligible':0,'eligible_ids':[],'unsupported_ids':[]});p['n']+=1;counts['eligible' if eligible else 'withheld']+=1
 if eligible:
  p['eligible']+=1;p['eligible_ids'].append(id)
  if r['supported']:p['supported_eligible']+=1
  else:counts['unsupported_eligible']+=1;p['unsupported_eligible']+=1;p['unsupported_ids'].append(id)
  if r['supported'] and r['complete'] and r['useful']:
   p['useful_eligible']+=1
   if prefix=='s':counts['old_useful_eligible']+=1
   if prefix=='l':counts['new_useful_eligible']+=1
 if prefix in ['s','n'] and ('absent' in cases[id].get('expected_route','') or cases[id]['kind']=='absence') and not eligible:counts['old_absent_withheld' if prefix=='s' else 'new_absent_withheld']+=1
 if prefix=='r' and eligible and not r['supported']:counts['historical_unsupported_eligible']+=1
 if prefix=='p':
  expected=cases['l'+id[1:]]['expected_probe_supported']
  if eligible and not expected:counts['probe_false_approvals']+=1
  if not eligible and expected:counts['probe_false_rejections']+=1
scores=[json.loads(l) for l in (E/'scoring/scores.jsonl').read_text().splitlines()];new=[json.loads((E/'new-run/results'/(c['id']+'.json')).read_text()) for c in fixtures['cases']]
def stats(values):
 values=sorted(values);return {'n':len(values),'p50':values[math.ceil(.5*len(values))-1],'p95':values[math.ceil(.95*len(values))-1],'max':values[-1]}
def memory(path):
 samples=json.loads(path.read_text());return {k:max(int(s.get(k,'0').split()[0])*1024 for s in samples) for k in ['VmRSS','VmHWM','VmSwap']}
output={'counts':counts,'populations':pop,'reviewer':'builder, independent source review pending','timing_definition':'Nearest-rank ceil(p*n)-1 on distinct requests/pairs, not repeated cold-phone latency; all CPU host, no mixed-backend comparison','new_generation_ms':{'first_token':stats([x['draft']['first_token_ms'] for x in new]),'draft_total':stats([x['draft']['total_ms'] for x in new]),'draft_plus_self_audit':stats([x['draft']['total_ms']+x['audit']['total_ms'] for x in new])},'classifier_pair_seconds':stats([x['elapsed_s'] for x in scores]),'classifier_pairs':len(scores),'classifier_rejected_oversize':sum(x['tokens']>512 for x in scores),'classifier_failed_pairs':sum(bool(x['failure']) and x['tokens']<=512 for x in scores),'generation_memory_bytes':memory(E/'new-run/memory.json'),'classifier_memory_bytes':memory(E/'scoring/memory.json'),'classifier_run_seconds':json.loads((E/'scoring/score-receipt.json').read_text())['elapsed_s'],'new_generation_seconds':json.loads((E/'new-run/receipt.json').read_text())['elapsed_s'],'new_generation_max_prompt_tokens':max(max(x['draft']['prompt_tokens'],x['audit']['prompt_tokens']) for x in new),'new_generation_max_total_tokens':max(x['draft']['tokens']+x['audit']['tokens'] for x in new),'native_peaks':[max(max(x['draft']['native_peaks'][i],x['audit']['native_peaks'][i]) for x in new) for i in range(5)]}
(E/'metrics.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output,indent=2))
