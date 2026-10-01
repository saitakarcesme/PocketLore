#!/usr/bin/env python3
"""Reconstruct per-source rights/extraction and separately reviewed topic dispositions."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[4]
STAGE=ROOT/'downloads/broad-reference/html-v2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def records():
 info=json.loads((ROOT/'downloads/broad-reference/rendered-v2/build.json').read_text())
 admitted={r['id']:r for r in info['sources']};excluded={r['id']:r for r in info['excluded']}
 review=json.loads((ROOT/'docs/evidence/broad-reference/repair/semantic-review.json').read_text())
 reviewed={r['id']:r for r in review['documents']};result=[]
 for p in sorted((STAGE/'extracted').glob('*.json'),key=lambda p:int(p.stem)):
  d=json.loads(p.read_text());ident=d['id'];r=reviewed.get(ident)
  assert (ident in admitted)!=(ident in excluded),'Missing or ambiguous disposition'
  result.append({'id':ident,'title':d['title'],'revision':d['revision'],'url':'https://en.wikipedia.org/w/index.php?oldid='+str(d['revision']['revid']),'html_sha256':d['html_sha256'],'extraction_sha256':sha(p),'disposition':'admitted' if ident in admitted else 'excluded','reason':excluded[ident]['reason'] if ident in excluded else 'Selected rendered paragraphs; source-specific notices retained; compatible terms under builder admission policy','source_notices':d['attribution_notices'],'math_representations':d['math_representations'],'quoted_blocks_excluded':len(d['excluded']),'historical_keyword_area_not_semantic_evidence':d['original_area'],'semantic_judgment':{'status':'builder-source-reviewed','area':r['area'],'reason':r['reason'],'support_sha256':hashlib.sha256(r['support_text'].encode()).hexdigest()} if r else {'status':'not counted toward semantic quotas','area':None}})
 return {'edition':info['id'],'pack_sha256':info['pack_sha256'],'review_sha256':info['review_sha256'],'assessment':'Builder admission and semantic judgments; independent review pending; no publication authorization','documents':result}
if __name__=='__main__':print(json.dumps(records(),indent=2,ensure_ascii=False))
