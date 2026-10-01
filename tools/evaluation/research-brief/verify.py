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
 receipt=json.loads((OUT/'receipt.json').read_text());check_files(receipt['files'],ROOT)
 # Negative controls change real frozen/source/run bytes, not a mock success flag.
 tests=0
 for manifest,base,names in [(freeze,HERE,['sources.json','cases.json']), (receipt['files'],ROOT,['docs/evidence/research-brief/outputs.json','android/app/src/main/java/org/pocketlore/app/ResearchBrief.java'])]:
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
  for key in ['id','source_ids','rendered','route','generated','coverage_verified']:assert a[key]==b[key],key
  assert not b['generated'] and not b['coverage_verified']
  for id in b['source_ids']:
   s=by_id[id];assert '“'+s['text']+'”' in b['rendered']
 android=json.loads((OUT/'android-results.json').read_text())
 assert len(android['rows'])==len(saved)==24
 for a,b in zip(android['rows'],saved):assert a['id']==b['id'] and a['rendered_sha256']==hashlib.sha256(b['rendered'].encode()).hexdigest() and not a['generated']
 reviews=json.loads((OUT/'builder-review.json').read_text())
 assert len(reviews)==24
 for a,b in zip(reviews,saved):assert a['id']==b['id'] and a['rendered_sha256']==hashlib.sha256(b['rendered'].encode()).hexdigest()
 print(behavior.strip());print(f'{tests} changed/missing real artifact controls pass; archive provenance, 24 exact host/Android replays pass')
 useful=sum(r['source_supported'] and r['complete'] and r['useful'] for r in reviews)
 print(f'Builder assessment: {useful}/24 useful complete source briefs; generated successes 0; independently reviewed briefs 0')
 # Do not invent independent assessments or equate unchanged quotes with relevance.
 print('FAIL: independent final-prose source review and absent-control eligibility judgments are pending; no quality acceptance claimed')
 return 1
if __name__=='__main__':
 try:sys.exit(verify())
 except (AssertionError,ValueError,FileNotFoundError,KeyError) as e:print('FAIL:',e);sys.exit(1)
