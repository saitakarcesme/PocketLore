"""Read-only source-review preflight. Packaging metadata is never semantic approval."""
import hashlib,json,pathlib

def readiness(root):
 root=pathlib.Path(root);asset=root/'android/app/src/main/assets'
 ledger=json.loads((asset/'bulk-source-reviews.json').read_text())
 pending=[];invalid=[];cleared=[]
 for source in ledger['dispositions']:
  key=source['key'];missing=[]
  for scope in ('rights','fidelity'):
   if source[scope+'_status']!='independently_approved':
    missing.append(scope);continue
   digest=source.get(scope+'_receipt_sha256','')
   if len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):
    invalid.append({'source':key,'reason':scope+' receipt hash missing/invalid'});continue
   path=asset/'bulk-reviews'/(digest+'.json')
   if not path.is_file():
    invalid.append({'source':key,'reason':scope+' receipt bytes missing'});continue
   raw=path.read_bytes()
   if len(raw)>16384 or hashlib.sha256(raw).hexdigest()!=digest:
    invalid.append({'source':key,'reason':scope+' receipt bytes changed/oversized'});continue
   try:
    review=json.loads(raw)
    valid=review.get('independent') is True and review.get('scope')==scope and review.get('decision')=='approved'
    valid=valid and all(review.get(k)==source[k] for k in ('snapshot_sha256','span_sha256','start_utf16','end_utf16'))
   except (ValueError,TypeError):valid=False
   if not valid:invalid.append({'source':key,'reason':scope+' receipt target/scope mismatch'})
  if missing:pending.append({'source':key,'missing':missing,'reason':source['builder_reason']})
  if not missing and not any(x['source']==key for x in invalid):cleared.append(key)
 oversized=[s['key'] for s in ledger['dispositions'] if not 0<s['end_utf16']-s['start_utf16']<=1200]
 index=json.loads((asset/'bulk-answer-reviews.json').read_text())
 return {'pending_sources':pending,'invalid_receipts':invalid,'source_receipts_present':cleared,'oversized_proposals':oversized,'bundled_answer_receipts':len(index['receipts']),'ready_for_real_answer_validation':bool(cleared) and not invalid and any(k not in oversized for k in cleared),'limitations':'Receipt presence and integrity are not source clearance or entailment by themselves; the independent review process must establish authority and actual judgments.'}

def require_ready(report):
 if not report['ready_for_real_answer_validation']:
  raise ValueError('OBJECTIVE OPEN: independent exact-revision rights/fidelity review is missing or invalid; no repeated model/Android matrix was run')
