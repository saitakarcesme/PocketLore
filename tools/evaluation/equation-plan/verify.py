"""Replay frozen generation, verify mathematical proofs, and keep usefulness separate."""
from pathlib import Path
import json,hashlib,tempfile,importlib.util,sys
R=Path(__file__).resolve().parents[3];F=Path(__file__).parent;E=R/'docs/evidence/equation-plan'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def exact(p,h):
 if not p.is_file() or sha(p)!=h:raise AssertionError('Missing/changed artifact: '+str(p))
def reject(fn):
 try:fn()
 except (AssertionError,FileNotFoundError):return
 raise AssertionError('Mutation accepted')
def main():
 for line in (E/'SHA256SUMS').read_text().splitlines():h,p=line.split('  ',1);exact(R/p,h)
 sys.path.insert(0,str(R/'tools/evaluation/source-plan-parser'))
 spec=importlib.util.spec_from_file_location('previous_parser',R/'tools/evaluation/source-plan-parser/verify.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
 previous=old.main(diagnostic=True,build_receipt=(E/'build.json',sha(E/'build.json')));assert previous['new_useful']==0
 receipt=json.loads((E/'run/receipt.json').read_text())
 for p,h in receipt['sources'].items():exact(R/p,h)
 for p,h in receipt['artifacts'].items():exact(E/'run'/p,h)
 spec=importlib.util.spec_from_file_location('equation_replay',F/'replay.py');replay=importlib.util.module_from_spec(spec);spec.loader.exec_module(replay)
 with tempfile.TemporaryDirectory(prefix='pocketlore-equation-') as tmp:
  t=Path(tmp);out=replay.run(t/'replay');exact(out/'results.json',sha(E/'run/results.json'));exact(out/'stages.tsv',sha(E/'run/stages.tsv'))
  changed=t/'changed-results';changed.write_bytes((E/'run/results.json').read_bytes()+b'changed');reject(lambda:exact(changed,sha(E/'run/results.json')));reject(lambda:exact(t/'missing-results',sha(E/'run/results.json')))
 values=json.loads((E/'run/results.json').read_text());review=json.loads((E/'builder-review.json').read_text());exact(E/'run/results.json',review['results_sha256']);assert len(values)==24
 eligible=[v for v in values if v['claims']];assert len(eligible)==1
 for v in eligible:
  original=json.loads((R/'docs/evidence/source-plan/run/results'/(v['id']+'.json')).read_text())
  # Every full generated clause is retained; source offsets are independently rebuilt by replay.
  for c in v['claims']:assert c['text'] in original['draft']['raw'] and c['references']
  assessment=review['answers'][v['id']];assert len(assessment['claims'])==len(v['claims'])
  for c,a in zip(v['claims'],assessment['claims']):assert a['text']==c['text'] and a['supported'] is True
 counts={'records':24,'supported_candidates':len(eligible),'unsupported_candidates':0,'complete_useful':sum(review['answers'][v['id']]['complete'] and review['answers'][v['id']]['useful'] for v in eligible),'absent_withheld':sum(v['id'] in ['q04','q08','q16','q24'] and not v['claims'] for v in values)}
 assert counts==json.loads((E/'metrics.json').read_text())['counts'];assert counts['absent_withheld']==4
 print(json.dumps({'behavior':'PASS','counts':counts,'assessment':'builder source review; independent review pending'},indent=2),flush=True)
 assert counts['complete_useful']>0,'QUALITY FAIL: supported mathematical restatement does not explain why; zero complete useful answers'
if __name__=='__main__':main()
