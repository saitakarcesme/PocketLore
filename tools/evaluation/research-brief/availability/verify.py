#!/usr/bin/env python3
"""Behavior, provenance and replay checks; independent semantic review is a separate gate."""
import copy,hashlib,json,pathlib,sys,zipfile
from run import ROOT,HERE,OUT,run,sha

def check_files(manifest, base, overrides=None):
 overrides=overrides or {}
 for name,digest in manifest.items():
  data=overrides[name] if name in overrides else (base/name).read_bytes()
  if data is None or hashlib.sha256(data).hexdigest()!=digest:raise ValueError('Changed/missing artifact: '+name)

def verify():
 freeze=json.loads((HERE/'freeze.json').read_text());check_files(freeze,HERE)
 check_files(json.loads((HERE/'availability/freeze.json').read_text()),HERE/'availability')
 receipt=json.loads((OUT/'receipt.json').read_text());check_files(receipt['files'],ROOT)
 validation=json.loads((OUT.parent/'review-repair/validation-inputs.json').read_text());check_files(validation,ROOT)
 # Negative controls change real frozen/source/run bytes, not a mock success flag.
 tests=0
 for manifest,base,names in [(freeze,HERE,['sources.json','cases.json']), (receipt['files'],ROOT,['docs/evidence/research-brief/availability/outputs.json','android/app/src/main/java/org/pocketlore/app/ResearchBrief.java'])]:
  for name in names:
   for data in [None,(base/name).read_bytes()+b'corrupt']:
    try:check_files(manifest,base,{name:data})
    except ValueError:tests+=1
    else:raise AssertionError('Artifact mutation accepted')
 sources=json.loads((HERE/'sources.json').read_text());by_id={s['id']:s for s in sources}
 archives={}
 for s in sources:
  p=ROOT/s['archive']
  if p not in archives:
   assert sha(p)==s['edition_sha256'],'Changed edition archive'
   z=zipfile.ZipFile(p);archives[p]={r.split('\t')[0]:r.split('\t') for r in z.read('passages.tsv').decode().splitlines()}
  r=archives[p][s['id'].split('_',1)[1]]
  assert r[1:]==[s['title'],s['url'],s['date'],s['rights'],s['text']]
  assert hashlib.sha256(s['text'].encode()).hexdigest()==s['sha256']
 saved=json.loads((OUT/'outputs.json').read_text());actual,behavior=run()
 for a,b in zip(actual,saved):
  for key in ['id','source_ids','rendered','route','availability','generated','coverage_verified']:assert a[key]==b[key],key
  assert not b['generated'] and not b['coverage_verified']
  for id in b['source_ids']:
   s=by_id[id];assert '“'+s['text']+'”' in b['rendered']
 android=json.loads((OUT/'android-results.json').read_text())
 assert len(android['rows'])==len(saved)==36
 for a,b in zip(android['rows'],saved):assert a['id']==b['id'] and a['rendered_sha256']==hashlib.sha256(b['rendered'].encode()).hexdigest() and not a['generated'] and a['availability']==b['availability']
 reviews=json.loads((OUT/'builder-review.json').read_text())
 assert len(reviews)==36
 for a,b in zip(reviews,saved):assert a['id']==b['id'] and a['rendered_sha256']==hashlib.sha256(b['rendered'].encode()).hexdigest()
 print(behavior.strip());print(f'{tests} changed/missing real artifact controls pass; archive provenance, 36 exact host/Android replays pass')
 useful=sum(r['source_supported'] and r['complete'] and r['useful'] for r in reviews[:24])
 print(f'Builder assessment: {useful}/24 useful complete source briefs; generated successes 0; independent review is aggregate, not per-case grades')
 # Check original and supplementary absence behaviors from executed output, not labels alone.
 expected={c['id']:c['scope'].upper() for c in json.loads((HERE/'availability/cases.json').read_text())};expected.update(b22='PERSONAL',b23='PREDICTIVE',b24='CURRENT')
 for r in saved:
  if r['id'] in expected:
   assert r['availability']==expected[r['id']]
   if expected[r['id']]!='REFERENCE':
    assert r['route']=='unavailable' and not r['source_ids'] and 'No quotations selected.' in r['rendered']
 print('3 original absent controls and 12 supplementary controls pass; no unrelated quotes in unavailable routes')
 # Consecutive actual Activity requests must remain usable after extractive completion.
 import xml.etree.ElementTree as ET
 for id in ['b22','b23','b24','b01']:
  tree=ET.parse(OUT/('ui-'+id+'.xml'))
  answer=next(n.get('text') for n in tree.iter('node') if n.get('content-desc')=='Offline answer')
  if id!='b01':assert answer.startswith('Evidence unavailable') and 'Quote [' not in answer
  else:assert 'two-step process' in answer and answer.startswith('Source-backed research brief')
 assert 'b01 actual Activity control and output passed' in (OUT/'ui.log').read_text()
 # Eligibility requires actual source review, not receipt presence or quote overlap.
 errors=[]
 absent=[r for r in reviews if r['absent_control']]
 if not all(r['absence_correctly_classified'] for r in absent):errors.append('all three absent controls remain unresolved rather than correctly classified')
 # The user supplied an aggregate independent verdict, not 36 per-case labels.
 # Bind it to unchanged reviewed sources, outputs, controller and model pin.
 from review_binding import validate_review,regressions
 review_bytes=(OUT.parent/'review-repair/supplied-independent-review.json').read_bytes()
 checked=validate_review(ROOT,review_bytes)
 print(f'{regressions(ROOT,review_bytes)} review/evidence binding mutation controls pass')
 # Quote identity and exact replay above guard every factual body; builder labels remain separate.
 if any(not r['source_supported'] for r in reviews):errors.append('unsupported source brief in builder inspection')
 if useful<12:errors.append('fewer than twelve builder-inspected complete useful original briefs')
 print('Supplied independent verdict: at least 12/24 original useful source-supported briefs; unavailable controls have no quotes')
 if errors:
  print('FAIL: '+'; '.join(errors));return 1
 print('PASS: artifact, behavioral and bounded development review checks; no product acceptance');return 0
if __name__=='__main__':
 try:sys.exit(verify())
 except (AssertionError,ValueError,FileNotFoundError,KeyError) as e:print('FAIL:',e);sys.exit(1)
