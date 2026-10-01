"""Verify immutable inputs, replay shared behavior, then enforce source-reviewed quality."""
from pathlib import Path
import base64,hashlib,json,math,subprocess,tempfile,shutil,sqlite3,importlib.util
R=Path(__file__).resolve().parents[3];F=Path(__file__).parent;E=R/'docs/evidence/independent-linking';OLD=R/'docs/evidence/obligation-binding';TC=Path('/home/isa/Android/atlas-toolchain')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def require(v,m):
 if not v:raise AssertionError(m)
def exact(p,h):require(p.is_file() and sha(p)==h,'Missing/changed artifact: '+str(p))
def rejected(fn):
 try:fn()
 except (AssertionError,FileNotFoundError):return
 raise AssertionError('Mutation admitted')
def receipt(directory,name='receipt.json'):
 v=json.loads((directory/name).read_text())
 if name=='receipt.json':require(v['exit_code']==0 and not v.get('killed'),'Incomplete native run')
 for p,h in v['artifacts'].items():exact(directory/p,h)
 return v
def main():
 fixtures=json.loads((F/'fixtures.json').read_text());exact(F/'fixtures.json',(F/'fixtures.sha256').read_text().strip());require(len(fixtures['cases'])==16 and len({c['topic'] for c in fixtures['cases']})>=4,'Frozen coverage')
 exact(OLD/'SHA256SUMS',fixtures['old_seal_sha256'])
 for seal in [OLD/'SHA256SUMS',R/'docs/evidence/scale-model-quality/SHA256SUMS',E/'SHA256SUMS']:
  for line in seal.read_text().splitlines():h,p=line.split('  ',1);exact(R/p,h)
 for p in ['tools/answers/model.env','android/app/src/main/cpp/runtime.cpp','android/app/src/main/cpp/resource_budget.h','android/app/src/main/java/org/pocketlore/app/BoundAnswer.java']:
  exact(R/p,hashlib.sha256(subprocess.check_output(['git','show','15a742f:'+p],cwd=R)).hexdigest())
 protocol=json.loads((F/'protocol.json').read_text());pin=protocol['verifier'];model=R/'downloads/independent-linking/model'/pin['file'];exact(model,pin['sha256']);require(model.stat().st_size==pin['bytes']<=1024**3,'Verifier cap')
 exact(R/'downloads/model-capability/models/Qwen3-4B-Q4_K_M.gguf',protocol['generator_sha256'])
 acquisition=json.loads((E/'model-receipt.json').read_text());require(acquisition['pin']==pin,'Model pin drift')
 for p,v in acquisition['assets'].items():exact(R/'downloads/independent-linking/model'/p,v['sha256'])
 receipt(E/'new-run');runmanifest=json.loads((E/'new-run/manifest.json').read_text())
 for p,h in runmanifest['sources'].items():exact(R/p,h)
 exact(F/'fixtures.json',runmanifest['protocol_sha256']);exact(F/'protocol.json',runmanifest['execution_sha256']);exact(R/'downloads/scale-model-quality/host-build/libpocketlore.so',runmanifest['library_sha256'])
 counts={'old_useful_eligible':0,'new_useful_eligible':0,'unsupported_eligible':0,'old_absent_withheld':0,'new_absent_withheld':0,'eligible':0,'withheld':0,'historical_unsupported_eligible':0,'probe_false_approvals':0,'probe_false_rejections':0}
 oldcases=json.loads((R/'tools/evaluation/scale-model-quality/protocol.json').read_text())['cases']+json.loads((R/'tools/evaluation/obligation-binding/new-cases.json').read_text())['cases'];cases={c['id']:c for c in oldcases+fixtures['cases']}
 db=R/'downloads/broad-reference/rendered-v2/index.sqlite';exact(db,'9009b19de43f851a815d1797779a94ab47077cc2fc5b3dfe70fc4bdf9a097386');con=sqlite3.connect('file:'+str(db)+'?mode=ro',uri=True)
 for c in cases.values():
  for s in c['sources']:
   row=con.execute('select p.body,p.sha,d.title,d.url,d.date,d.rights,d.sha from passages p join documents d on d.id=p.document where p.citation=?',(s['id'],)).fetchone();require(row==tuple(s[k] for k in ['text','sha256','title','url','date','license','source_sha256']),'Exact reviewed source drift')
 for c in fixtures['cases']:
  v=json.loads((E/'new-run/results'/(c['id']+'.json')).read_text());require(v['question']==c['question'] and v['draft']['tokens']>0,'Missing actual new generation')
  require(0<v['draft']['tokens']<=320 and 0<=v['audit']['tokens']<=192 and v['draft']['tokens']+v['audit']['tokens']<=512,'Budget');require(v['native_after']==[1,0,0,0,0],'Native contexts not released')
  for kind,budget in [('draft',320),('audit',192)]:
   st=v[kind]
   if st['tokens']:require(st['prompt_tokens']+budget<=4096 and 0<st['first_token_ms']<=st['total_ms'],'Timing/context')
 score=E/'scoring';receipt(score,'score-receipt.json');manifest=json.loads((score/'manifest.json').read_text())
 for p,h in manifest['sources'].items():exact(R/p,h)
 for p,h in manifest['inputs'].items():exact(score/p,h)
 exact(score/'prepared/pairs.json',manifest['pairs_sha256']);runtime=json.loads((score/'runtime.json').read_text());require(runtime['providers']==['CPUExecutionProvider'] and runtime['packages']=={'onnxruntime':'1.24.1','tokenizers':'0.22.1','numpy':'2.3.3'},'Runtime identity')
 pairs=json.loads((score/'prepared/pairs.json').read_text());scores=[json.loads(x) for x in (score/'scores.jsonl').read_text().splitlines()];require(len(pairs)==len(scores) and len({x['key'] for x in scores})==len(scores),'Incomplete scores')
 tsv=[]
 for p,s in zip(pairs,scores):
  require(p['key']==s['key']==hashlib.sha256((p['premise']+'\0'+p['hypothesis']).encode()).hexdigest(),'Pair binding')
  if not s['failure']:
   logits=s['logits'];ex=[math.exp(v-max(logits)) for v in logits];probs=[v/sum(ex) for v in ex];require(len(probs)==3 and all(abs(a-b)<1e-9 for a,b in zip(probs,s['probabilities'])) and 0<s['tokens']<=512 and s['elapsed_s']>0,'Score validity')
  tsv.append('\t'.join([s['key'],*[str(x) for x in s['probabilities']],str(s['tokens']),base64.b64encode(s['failure'].encode()).decode()]))
 require((score/'scores.tsv').read_text()=='\n'.join(tsv)+'\n','Score transport drift')
 linked=json.loads((score/'final/linked.json').read_text());review=json.loads((E/'review.json').read_text());require(review['reviewer'].startswith('builder'),'Builder review distinction');require(len(linked)==103 and set(review['cases'])=={v['id'] for v in linked},'Incomplete populations/review')
 historical={h['id']:h for h in json.loads((R/'tools/evaluation/obligation-binding/history.json').read_text())};newby={c['id']:c for c in fixtures['cases']}
 for v in linked:
  id=v['id'];r=review['cases'][id];require(r['record_sha256']==hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest(),'Unbound source assessment');eligible=v['route']=='SCREEN_ELIGIBLE';require(eligible==(bool(v['rendered']) and not v['failure']),'Route integrity');counts['eligible' if eligible else 'withheld']+=1
  if id.startswith('p'):c=newby['l'+id[1:]]
  elif id.startswith('r'):c=cases[historical[id]['case_id']]
  else:c=cases[id]
  byid={s['id']:s for s in c['sources']}
  for claim,link in zip(v['claims'],v['links']):
   text=v['rendered'].encode('utf-16-le')[link['start_utf16']*2:link['end_utf16']*2].decode('utf-16-le');require(text.startswith('[') and text.endswith(']'),'Typed citation span')
   for ref in claim['references']:
    src=byid[ref['passage']];require(ref['edition']==fixtures['edition'] and ref['passage_sha256']==src['sha256'] and ref['document_sha256']==src['source_sha256'],'Reference identity');require(src['text'].encode('utf-16-le')[ref['start_utf16']*2:ref['end_utf16']*2].decode('utf-16-le')==ref['text'],'Exact source offsets')
  if eligible:
   require(len(r['claims'])==len(v['claims']) and len(v['links'])==len(v['claims']),'Every eligible claim reviewed')
   if not r['supported']:counts['unsupported_eligible']+=1
   if id.startswith('s') and r['supported'] and r['complete'] and r['useful']:counts['old_useful_eligible']+=1
   if id.startswith('l') and r['supported'] and r['complete'] and r['useful']:counts['new_useful_eligible']+=1
  if id.startswith(('s','n')) and ('absent' in c.get('expected_route','') or c['kind']=='absence'):
   if not eligible:counts['old_absent_withheld' if id.startswith('s') else 'new_absent_withheld']+=1
  if id.startswith('r') and eligible and not r['supported']:counts['historical_unsupported_eligible']+=1
  if id.startswith('p'):
   if eligible and not c['expected_probe_supported']:counts['probe_false_approvals']+=1
   if not eligible and c['expected_probe_supported']:counts['probe_false_rejections']+=1
 with tempfile.TemporaryDirectory(prefix='pocketlore-independent-check-') as tmp:
  t=Path(tmp);classes=t/'classes';classes.mkdir();sources=[R/p for p in manifest['sources'] if p.endswith('.java')]+[F/'LinkBehavior.java'];subprocess.run([TC/'jdk/bin/javac','-d',classes,*sources],check=True);subprocess.run([TC/'jdk/bin/java','-cp',classes,'org.pocketlore.app.LinkBehavior'],check=True)
  subprocess.run([TC/'jdk/bin/java','-cp',classes,'org.pocketlore.app.LinkHarness',score/'inputs',t/'replay',score/'scores.tsv'],check=True);exact(t/'replay/linked.json',sha(score/'final/linked.json'));exact(t/'replay/pairs.json',sha(score/'prepared/pairs.json'))
  for name,p,h in [('run',score/'scores.jsonl',sha(score/'scores.jsonl')),('verifier',model,pin['sha256'])]:
   changed=t/name
   if name=='verifier':
    with changed.open('wb') as f:f.truncate(p.stat().st_size)
   else:changed.write_bytes(p.read_bytes()+b'changed')
   rejected(lambda:exact(changed,h));rejected(lambda:exact(t/('missing-'+name),h))
 build=json.loads((E/'build.json').read_text());exact(R/build['apk'],build['sha256']);require(build['exit_code']==0,'Android build failure')
 require(counts==json.loads((E/'metrics.json').read_text())['counts'],'Derived counts drift');print(json.dumps({'artifact_behavior':'PASS','builder_assessed_counts':counts,'independent_review':'pending'},indent=2),flush=True)
 failures=[]
 if counts['old_useful_eligible']<=4:failures.append('Useful old answers did not exceed4/40')
 if counts['unsupported_eligible']:failures.append('Unsupported eligible prose remains')
 if (counts['old_absent_withheld'],counts['new_absent_withheld'])!=(8,1):failures.append('Absent control admitted')
 if counts['probe_false_approvals']:failures.append('Constructed unsupported probe admitted')
 if failures:raise AssertionError('QUALITY FAIL: '+'; '.join(failures))
 print('QUALITY PASS on public development fixtures only; independent review and deployment gates remain open')
if __name__=='__main__':main()
