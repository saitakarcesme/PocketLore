"""New preflight regressions using copies of actual ledger bytes, not fictional approvals."""
import json,pathlib,tempfile,copy
from review_readiness import readiness,require_ready
ROOT=pathlib.Path(__file__).resolve().parents[3]

def run():
 ledger=json.loads((ROOT/'android/app/src/main/assets/bulk-source-reviews.json').read_text())
 index=(ROOT/'android/app/src/main/assets/bulk-answer-reviews.json').read_bytes()
 tests=0
 with tempfile.TemporaryDirectory(prefix='bulk-review-preflight-') as directory:
  root=pathlib.Path(directory);assets=root/'android/app/src/main/assets';assets.mkdir(parents=True)
  (assets/'bulk-answer-reviews.json').write_bytes(index)
  for mode in ('pending','summary-count','dataset-status','missing-receipt','changed-receipt','oversized-receipt'):
   data=copy.deepcopy(ledger)
   if mode=='summary-count':data['independently_reviewed_useful_generated_answers']=100
   if mode=='dataset-status':
    for s in data['dispositions']:s['rights_status']=s['fidelity_status']='dataset_license_only_unreviewed'
   if mode in ('missing-receipt','changed-receipt','oversized-receipt'):
    s=data['dispositions'][0]
    for scope in ('rights','fidelity'):s[scope+'_status']='independently_approved';s[scope+'_receipt_sha256']='a'*64
    if mode!='missing-receipt':
     (assets/'bulk-reviews').mkdir(exist_ok=True);(assets/'bulk-reviews'/('a'*64+'.json')).write_bytes(b'x'*(16385 if mode=='oversized-receipt' else 12))
   (assets/'bulk-source-reviews.json').write_text(json.dumps(data))
   report=readiness(root)
   try:require_ready(report)
   except ValueError:tests+=1
   else:raise AssertionError('Premature readiness: '+mode)
 print(str(tests)+' actual-ledger preflight mutations denied; reported counts cannot bypass missing source review')
 return tests
if __name__=='__main__':run()
