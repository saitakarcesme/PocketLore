"""Pure owned accounting controls only; never starts Java or native helpers."""
import json,pathlib
from accounting import scan_roots,RESERVES
ROOT=pathlib.Path(__file__).resolve().parents[3]
OUT=ROOT/'downloads/ocr-publication-deadline-557/accounting-controls'
def main():
 OUT.mkdir();root=OUT/'mandatory';root.mkdir();sentinel=root/'sentinel';sentinel.write_bytes(b'authored sentinel\n');expected=(root,);out=[]
 def positive():
  files=scan_roots(expected,expected);assert files[str(sentinel)]['bytes']==18;return sum(x['bytes'] for x in files.values())
 assert positive()==18
 for name,roots,wanted in [('wrong-root',(OUT/'wrong',),'mandatory-root-roster'),('omitted-root',(),'mandatory-root-roster')]:
  positive()
  try:scan_roots(roots,expected)
  except ValueError as e:assert str(e)==wanted;out.append({'case':name,'guard':str(e)})
  else:raise AssertionError(name)
  positive()
 positive();missing=(OUT/'absent-required',)
 try:scan_roots(missing,missing)
 except ValueError as e:assert str(e)=='mandatory-root-missing';out.append({'case':'missing-root','guard':str(e)})
 else:raise AssertionError('missing accepted')
 positive();(root/'failed-review').write_bytes(b'authored refusal\n');assert positive()==35
 with (root/'failed-review').open('ab') as f:f.write(b'growth\n')
 assert positive()==42;assert positive()+RESERVES==131114
 result={'controls':out,'sentinel_bytes':18,'after_failed_review_bytes':35,'after_growth_bytes':42,'additional_reserves':RESERVES,'original_failure_files_modified':False}
 (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result))
if __name__=='__main__':main()
