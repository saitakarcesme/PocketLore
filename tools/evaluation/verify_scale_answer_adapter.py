#!/usr/bin/env python3
"""Behavior and artifact validation; fail the objective while actual independent clearance is absent."""
import sys,pathlib,json,hashlib,subprocess,importlib.util,copy
ROOT=pathlib.Path(__file__).resolve().parents[2];HERE=ROOT/'tools/evaluation/scale-answer';OUT=ROOT/'docs/evidence/scale-answer'
sys.path.insert(0,str(HERE));from run_checks import run
from review_readiness import readiness,require_ready
from check_review_readiness import run as check_readiness
sha=lambda b:hashlib.sha256(b).hexdigest()
def require(ok,message):
 if not ok:raise ValueError(message)
def integrity(manifest,override=None):
 override=override or {}
 for name,want in manifest.items():
  data=override[name] if name in override else (ROOT/name).read_bytes()
  require(data is not None and sha(data)==want,'Changed/missing artifact: '+name)
def ledger_check(ledger):
 for r in ledger['dispositions']:
  for scope in ['rights','fidelity']:
   if r[scope+'_status']=='independently_approved':
    path=ROOT/'android/app/src/main/assets/bulk-reviews'/(r[scope+'_receipt_sha256']+'.json')
    require(path.is_file(),'Independent receipt missing')
    b=path.read_bytes();require(sha(b)==r[scope+'_receipt_sha256'],'Review receipt checksum');review=json.loads(b)
    require(review['independent'] and review['decision']=='approved' and review['scope']==scope,'Review authority/scope')
    for key in ['snapshot_sha256','span_sha256','start_utf16','end_utf16']:require(review[key]==r[key],'Review target mismatch')
def main():
 frozen=json.loads((HERE/'freeze.json').read_text());integrity(frozen)
 receipt=json.loads((OUT/'repair-2/receipt.json').read_text());integrity(receipt['files'])
 handoff=json.loads((OUT/'supplement-handoff.json').read_text());base=pathlib.Path('/home/isa/PocketLore-control/scale-workers/quality-preparation')
 for f in handoff['files']:
  data=(base/f['path']).read_bytes();require(len(data)==f['bytes'] and sha(data)==f['sha256'],'Supplement handoff drift')
 ledger=json.loads((ROOT/'android/app/src/main/assets/bulk-source-reviews.json').read_text());ledger_check(ledger)
 rows=json.loads((OUT/'bulk-records.json').read_text());require(len(rows)==8,'Bulk record count')
 for row in rows:
  data=(ROOT/row['record_path']).read_bytes();d=json.loads(data);require(sha(data)==row['row']['sha256'] and sha(d['text'].encode())==row['row']['text_sha256'],'Real sealed record drift')
  review=next(r for r in ledger['dispositions'] if r['record_path']==row['record_path'])
  require(sha(d['wikitext'].encode())==review['retained_wikitext_sha256'] and d['wikitext_ranges']==review['retained_range_map'],'Formula/unit context changed')
 packet=json.loads((OUT/'repair-1/review-packet.json').read_text());integrity({packet['path']:packet['sha256']})
 check_readiness()
 report=readiness(ROOT);print('Source review preflight:',json.dumps(report,sort_keys=True));require_ready(report)
 print(run().strip())
 android=json.loads((OUT/'repair-1/android-results.json').read_text());require(len(android['records'])==8,'Android record count');require(android['missing_changed_receipt_tests']==2,'Android receipt mutation coverage');require(android['constructed_publication_checks'] and android['publication_receipt_mutations']==2,'Android publication behavior coverage')
 for r in android['records']:
  source=next(x for x in rows if str(x['row']['id'])==r['id']);require(r['text_sha256']==source['row']['text_sha256'] and r['record_sha256']==source['row']['sha256'],'Android sealed identity')
  require(r['route']=='withheld_pending_source_review' and not r['preview_truncated'],'Unreviewed source admitted or truncated')
 tests=0
 for name in ['tools/evaluation/scale-answer/cases.json','docs/evidence/scale-answer/repair-1/android-results.json','android/app/src/main/assets/bulk-source-reviews.json','android/app/src/main/assets/bulk-answer-reviews.json','android/app/src/main/java/org/pocketlore/app/ScaleAnswerPublication.java']:
  manifest=frozen if name in frozen else receipt['files']
  for data in [None,(ROOT/name).read_bytes()+b'changed']:
   try:integrity(manifest,{name:data})
   except ValueError:tests+=1
   else:raise AssertionError('Artifact mutation accepted')
 mutated=copy.deepcopy(ledger);mutated['dispositions'][0]['rights_status']='independently_approved';mutated['dispositions'][0]['rights_receipt_sha256']='a'*64
 try:ledger_check(mutated)
 except ValueError:tests+=1
 else:raise AssertionError('Dataset status promoted without receipt')
 print(str(tests)+' actual artifact/review promotion regressions pass; 8 real Android denials verified')
 cleared=[r for r in ledger['dispositions'] if r['rights_status']==r['fidelity_status']=='independently_approved']
 require(cleared,'OBJECTIVE OPEN: zero independently rights/fidelity-cleared bulk spans; no bulk generated claims were published or independently validated')
 raise ValueError('OBJECTIVE OPEN: real source-cleared controller replay and independently reviewed final bulk output are still missing; a reported useful-answer count cannot establish either')
if __name__=='__main__':
 try:main()
 except (ValueError,KeyError,FileNotFoundError,AssertionError) as e:print('FAIL:',e);sys.exit(1)
