"""Behavior/artifact replay plus separately source-reviewed public-development quality gates."""
from pathlib import Path
import json,hashlib,subprocess,tempfile,sqlite3,base64,importlib.util
R=Path(__file__).resolve().parents[3];F=Path(__file__).parent;E=R/'docs/evidence/fact-frames';TC=Path('/home/isa/Android/atlas-toolchain')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def require(v,m):
 if not v:raise AssertionError(m)
def exact(p,h):require(p.is_file() and sha(p)==h,'Missing/changed artifact: '+str(p))
def reject(fn):
 try:fn()
 except (AssertionError,FileNotFoundError):return
 raise AssertionError('Mutation accepted')
def sealed(path):
 r=json.loads((path/'receipt.json').read_text());require(r['exit_code']==0 and not r.get('killed'),'Failed/incomplete stage')
 for p,h in r['artifacts'].items():exact(path/p,h)
 return r
def main():
 fixture=json.loads((F/'fixtures.json').read_text());exact(F/'fixtures.json',(F/'fixtures.sha256').read_text().strip());require(len(fixture['cases'])==20 and len({c['topic'] for c in fixture['cases']})>=4,'Frozen new coverage')
 exact(R/'docs/evidence/independent-linking/SHA256SUMS',fixture['previous_seal_sha256']);exact(R/'tools/evaluation/scale-model-quality/protocol.json',fixture['task220_protocol_sha256'])
 for name in ['scale-model-quality','obligation-binding','independent-linking','fact-frames']:
  for line in (R/'docs/evidence'/name/'SHA256SUMS').read_text().splitlines():h,p=line.split('  ',1);exact(R/p,h)
 for p in ['tools/answers/model.env','android/app/src/main/cpp/runtime.cpp','android/app/src/main/cpp/resource_budget.h','android/app/src/main/java/org/pocketlore/app/BoundAnswer.java','android/app/src/main/java/org/pocketlore/app/EvidenceLinker.java']:
  exact(R/p,hashlib.sha256(subprocess.check_output(['git','show','2623197:'+p],cwd=R)).hexdigest())
 model=R/'downloads/model-capability/models/Qwen3-4B-Q4_K_M.gguf';spec=json.loads((F/'protocol.json').read_text());exact(model,spec['generator_sha256']);require(model.stat().st_size==2497280256,'Model cap/pin')
 run=E/'new-run';sealed(run);manifest=json.loads((run/'manifest.json').read_text());exact(F/'fixtures.json',manifest['protocol_sha256']);exact(F/'protocol.json',manifest['execution_sha256']);exact(R/'downloads/scale-model-quality/host-build/libpocketlore.so',manifest['library_sha256'])
 for p,h in manifest['sources'].items():
  if p.endswith('/FactFrames.java'):
   # This class was compiled but never invoked by FrameDraftHarness. Preserve its actual generation-time version; the corrected parser gets its own replay receipt below.
   require(hashlib.sha256(subprocess.check_output(['git','show',manifest['git_revision']+':'+p],cwd=R)).hexdigest()==h,'Historical compiled frame source changed')
  else:exact(R/p,h)
 for c in fixture['cases']:
  v=json.loads((run/'results'/(c['id']+'.json')).read_text());d=v['draft'];require(v['question']==c['question'] and 0<d['tokens']<=320 and d['prompt_tokens']+320<=4096 and 0<d['first_token_ms']<=d['total_ms'],'New real generation/budget/timing');require(v['native_after']==[1,0,0,0,0],'Native contexts not released')
 require(json.loads((run/'results/closed.json').read_text())==[0,0,0,0,0],'Native model not closed')
 replay=E/'replay';sealed(replay);m=json.loads((replay/'manifest.json').read_text())
 for p,h in m['sources'].items():exact(R/p,h)
 for p,h in m['inputs'].items():exact(replay/p,h)
 exact(replay/'origins.json',m['origins_sha256']);origins=json.loads((replay/'origins.json').read_text());rows={r.split('\t')[0]:r.split('\t') for r in (replay/'inputs/drafts.tsv').read_text().splitlines()}
 decoded=lambda s:base64.b64decode(s).decode()
 for id,o in origins.items():
  path=R/o['path'];exact(path,o['sha256']);raw=decoded(rows[id][2]);kind=o['type']
  if 'generated draft' in kind:
   original=json.loads(path.read_text());require(raw==original['draft']['raw'] and int(rows[id][3])==original['draft']['tokens'] and decoded(rows[id][1])==original['question'],'Changed/regenerated prose')
  elif kind.startswith('historical'):require(raw.strip()==json.loads(path.read_text())['wrapped_raw'].strip(),'Changed historical claim')
  else:
   c=next(c for c in json.loads(path.read_text())['cases'] if c['id']==o['case']);require(raw=='@PROBE' and decoded(rows[id][5])==c['constructed_probe'],'Changed constructed probe')
 old=json.loads((R/'tools/evaluation/scale-model-quality/protocol.json').read_text())['cases']+json.loads((R/'tools/evaluation/obligation-binding/new-cases.json').read_text())['cases'];prior=json.loads((R/'tools/evaluation/independent-linking/fixtures.json').read_text())['cases'];cases={c['id']:c for c in old+prior+fixture['cases']};historical={c['id']:c for c in json.loads((R/'tools/evaluation/obligation-binding/history.json').read_text())}
 db=R/'downloads/broad-reference/rendered-v2/index.sqlite';exact(db,'9009b19de43f851a815d1797779a94ab47077cc2fc5b3dfe70fc4bdf9a097386');con=sqlite3.connect('file:'+str(db)+'?mode=ro',uri=True)
 for c in cases.values():
  for s in c['sources']:
   require(con.execute('select p.body,p.sha,d.title,d.url,d.date,d.rights,d.sha from passages p join documents d on d.id=p.document where p.citation=?',(s['id'],)).fetchone()==tuple(s[k] for k in ['text','sha256','title','url','date','license','source_sha256']),'Source bytes/rights/date identity')
 values=json.loads((replay/'results/linked.json').read_text());review=json.loads((E/'review.json').read_text());require(len(values)==143 and len(rows)==143 and set(review['cases'])=={v['id'] for v in values},'Missing records/review');require(review['reviewer'].startswith('builder'),'Review role')
 counts={'old_useful_eligible':0,'unsupported_eligible':0,'old_absent_withheld':0,'prior_absent_withheld':0,'new_absent_withheld':0,'new_useful_eligible':0,'eligible':0,'withheld':0}
 for v in values:
  id=v['id'];r=review['cases'][id];require(r['record_sha256']==hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest(),'Review binding');eligible=v['route']=='SCREEN_ELIGIBLE';require(eligible==(bool(v['rendered']) and not v['failure'] and bool(v['proof'])),'Route/complete proof');counts['eligible' if eligible else 'withheld']+=1
  if id.startswith('p'):case=cases['l'+id[1:]]
  elif id.startswith('t'):case=cases['f'+id[1:]]
  elif id.startswith('r'):case=cases[historical[id]['case_id']]
  else:case=cases[id]
  byid={s['id']:s for s in case['sources']}
  require(len(v['claims'])==len(v['links']),'Link count')
  for i,(claim,link) in enumerate(zip(v['claims'],v['links'])):
   require(v['rendered'].encode('utf-16-le')[link['start_utf16']*2:link['end_utf16']*2].decode('utf-16-le')=='['+str(i+1)+']','Typed link range')
   for ref in claim['references']:
    src=byid[ref['passage']];require(ref['edition']==fixture['source_edition_sha256'] and ref['document_sha256']==src['source_sha256'] and ref['passage_sha256']==src['sha256'],'Typed provenance');require(src['text'].encode('utf-16-le')[ref['start_utf16']*2:ref['end_utf16']*2].decode('utf-16-le')==ref['text'],'Exact UTF16 span')
  if eligible:
   require(len(r['claims'])==len(v['claims']),'Every eligible claim source-reviewed')
   if not r['supported']:counts['unsupported_eligible']+=1
   if r['supported'] and r['complete'] and r['useful']:
    if id.startswith('s'):counts['old_useful_eligible']+=1
    if id.startswith('f'):counts['new_useful_eligible']+=1
  if 'absent' in case.get('expected_route','') or case.get('kind')=='absence':
   if id.startswith('s') and not eligible:counts['old_absent_withheld']+=1
   if id.startswith('n') and not eligible:counts['prior_absent_withheld']+=1
   if id.startswith('f') and not eligible:counts['new_absent_withheld']+=1
 with tempfile.TemporaryDirectory(prefix='pocketlore-frame-check-') as tmp:
  t=Path(tmp);classes=t/'classes';classes.mkdir();sources=[R/p for p in m['sources'] if p.endswith('.java')]+[F/'FrameBehavior.java',R/'tools/evaluation/independent-linking/LinkBehavior.java'];subprocess.run([TC/'jdk/bin/javac','-d',classes,*sources],check=True)
  subprocess.run([TC/'jdk/bin/java','-cp',classes,'org.pocketlore.app.FrameBehavior'],check=True);subprocess.run([TC/'jdk/bin/java','-cp',classes,'org.pocketlore.app.LinkBehavior',replay/'inputs'],check=True);subprocess.run([TC/'jdk/bin/java','-cp',classes,'org.pocketlore.app.FrameHarness',replay/'inputs',t/'replay'],check=True);exact(t/'replay/linked.json',sha(replay/'results/linked.json'))
  changed=t/'changed.json';changed.write_bytes((replay/'results/linked.json').read_bytes()+b'changed');reject(lambda:exact(changed,sha(replay/'results/linked.json')));reject(lambda:exact(t/'missing.json',sha(replay/'results/linked.json')))
  changed_model=t/'changed.gguf'
  with changed_model.open('wb') as stream:stream.truncate(model.stat().st_size)
  reject(lambda:exact(changed_model,spec['generator_sha256']));reject(lambda:exact(t/'missing.gguf',spec['generator_sha256']))
 build=json.loads((E/'build.json').read_text());exact(R/build['apk'],build['sha256']);require(build['exit_code']==0,'Build failure');require(counts==json.loads((E/'metrics.json').read_text())['counts'],'Derived counts')
 print(json.dumps({'artifact_behavior':'PASS','builder_counts':counts,'independent_review':'pending','scope':'Finite public-development grammar, not general entailment or production acceptance'},indent=2),flush=True)
 require(counts['old_useful_eligible']>4,'Useful old coverage <=4/40');require(counts['unsupported_eligible']==0,'Unsupported eligible output');require((counts['old_absent_withheld'],counts['prior_absent_withheld'],counts['new_absent_withheld'])==(8,1,2),'Absent controls not all withheld');print('QUALITY PASS on frozen public development only')
if __name__=='__main__':main()
