#!/usr/bin/env python3
"""Offline independent reconstruction and corruption controls for the source edition."""
import copy,hashlib,importlib.util,json,pathlib,sys,tempfile,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/packs/reference-expansion'))
import build as edition
assert pathlib.Path(edition.__file__).resolve()==ROOT/'tools/packs/reference-expansion/build.py'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def check():
 packet=edition.PACKET;review=edition.REVIEW
 inventory=ROOT/'docs/evidence/reference-coverage-expansion/source-artifacts.json'
 assert sha(inventory)=='b7984508afc1342e4cbfb451feaab06cb73fdca8395c28becc69625ffaa68c69', 'Source inventory changed'
 for item in json.loads(inventory.read_text())['files']:
  original=ROOT/item['path'];assert original.stat().st_size==item['bytes'] and sha(original)==item['sha256'], 'Original response/legal/acquisition bytes changed: '+item['path']
 assert sha(ROOT/'tools/packs/reference-expansion/selection.json')=='21dab3107d7267b7a4ec79eeba32d7677cff087ecc5a354746a65779086bc29a'
 assert sha(packet)=='abbb800f0c837f401cb9c9d0f3ccf836e191c9f06d797917ef7678833ee392bc'
 original_packet=json.loads(packet.read_text());original_review=json.loads(review.read_text())
 with tempfile.TemporaryDirectory(prefix='reference480-') as directory:
  td=pathlib.Path(directory);m=edition.build(td/'a.plpack');edition.build(td/'b.plpack')
  assert (td/'a.plpack').read_bytes()==(td/'b.plpack').read_bytes(),'Nonreproducible edition'
  installed=ROOT/'downloads/reference-expansion/reference-expansion.plpack'
  assert installed.read_bytes()==(td/'a.plpack').read_bytes(),'Changed edition archive'
  assert len({d['source_identity'] for d in m['documents']})==len(m['documents'])>=100
  assert len({d['category'] for d in m['documents']})>=20
  # Every source-text paragraph has a complete mapped span. This is fidelity,
  # not an automated entailment/relevance judgment.
  for d in m['documents']:
   raw=d['source_text'].encode('utf-16-le');end=-2
   for p in d['passages']:
    a,b=p['source_utf16_start'],p['source_utf16_end'];assert a==end+2 and b>a
    quote=raw[a*2:b*2].decode('utf-16-le');assert hashlib.sha256(quote.encode()).hexdigest()==p['sha256'];end=b
   assert end*2==len(raw)
  admitted=[x for x in original_packet['documents'] if original_review['documents'][str(x['page_id'])]['decision']=='admit-selected-spans']
  assert admitted
  controls=[]
  for name in ['missing-source','changed-source-hash','shifted-original-offset','missing-review','rights-denied','changed-license']:
   p=copy.deepcopy(original_packet);r=copy.deepcopy(original_review);first=next(x for x in p['documents'] if x['page_id']==admitted[0]['page_id']);decision=r['documents'][str(first['page_id'])]
   if name=='missing-source':first['html_path']='downloads/reference-expansion/definitely-missing-source.html'
   elif name=='changed-source-hash':first['html_sha256']='0'*64
   elif name=='shifted-original-offset':
    selected=next(s for s in first['spans'] if s['sha256'] in decision['admitted_span_sha256']);selected['html_utf16_start']+=1
   elif name=='missing-review':del r['documents'][str(first['page_id'])]
   elif name=='rights-denied':
    for d in r['documents'].values():d['decision']='needs-evidence'
   pp=td/(name+'-packet.json');pp.write_text(json.dumps(p));r['packet_sha256']=sha(pp);rr=td/(name+'-review.json');rr.write_text(json.dumps(r))
   old_license=edition.LICENSE
   if name=='changed-license':edition.LICENSE=td/'changed-license.txt';edition.LICENSE.write_bytes(old_license.read_bytes()+b'changed')
   try:
    try:edition.build(td/(name+'.plpack'),pp,rr)
    except (AssertionError,ValueError,KeyError,FileNotFoundError):controls.append(name)
    else:raise AssertionError('Source mutation accepted: '+name)
   finally:edition.LICENSE=old_license
  return dict(status='PASS',classification='Offline reconstruction and source/rights integrity only; not device or factual quality acceptance',documents=len(m['documents']),families=len({d['category'] for d in m['documents']}),pack_sha256=sha(installed),packet_sha256=sha(packet),review_sha256=sha(review),negative_controls=controls)
if __name__=='__main__':print(json.dumps(check(),indent=2))
