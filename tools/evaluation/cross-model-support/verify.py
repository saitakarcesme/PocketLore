from pathlib import Path
import json,hashlib,subprocess,tempfile,shutil,sys
R=Path(__file__).resolve().parents[3];F=Path(__file__).parent;P=R/'docs/evidence/cross-model-support'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def artifacts(d):
 m=json.loads((d/'manifest.json').read_text())
 for n,h in m['inputs'].items():assert sha(R/n)==h,n
 for n,h in m['verification_inputs'].items():assert sha(d/'inputs'/n)==h,n
 assert sha(Path(m['runtime']['path']))==m['runtime']['sha256']
 assert len(m['runs'])==1;run=m['runs'][0];assert run['exit_code']==0
 assert sha(Path(run['model_path']))==run['model']['sha256']
 for n,h in run['files'].items():assert sha(d/'qwen25-7b'/n)==h,n
 cases=json.loads((R/'tools/evaluation/general-generation/protocol.json').read_text())['cases']+json.loads((F/'protocol.json').read_text())['probes']
 for c in cases:
  row=json.loads((d/'qwen25-7b'/(c['id']+'.json')).read_text());assert row['prompt_tokens']+512<=4096 and row['tokens']<=512
  first=row['raw'].strip().splitlines()[0] if row['raw'].strip() else ''
  expected=first.removeprefix('VERDICT: ') if first in ['VERDICT: SUPPORTED_COMPLETE','VERDICT: ABSENT','VERDICT: REJECT'] and 0<=row['tokens']<512 else 'INVALID'
  assert row['screen_route']==expected,c['id']
 return cases
handoff=json.loads((P/'HANDOFF.json').read_text());d=Path(handoff['run']);cases=artifacts(d)
with tempfile.TemporaryDirectory() as tmp:
 java=Path('/home/isa/Android/atlas-toolchain/jdk/bin');base=R/'android/app/src/main/java/org/pocketlore/app'
 subprocess.run([java/'javac','-d',tmp,*[base/(n+'.java') for n in ['ResearchEngine','GeneralGroundedAnswer','CrossModelSupport']],F/'Behavior.java'],check=True)
 subprocess.run([java/'java','-Xmx128m','-cp',tmp,'org.pocketlore.app.Behavior'],check=True)
for name in ['g01.json','p06.json']:
 with tempfile.TemporaryDirectory() as tmp:
  copy=Path(tmp);shutil.copy2(d/'manifest.json',copy/'manifest.json');shutil.copytree(d/'inputs',copy/'inputs');shutil.copytree(d/'qwen25-7b',copy/'qwen25-7b')
  if name=='g01.json':(copy/'qwen25-7b'/name).unlink()
  else:(copy/'qwen25-7b'/name).write_text('{}')
  try:artifacts(copy)
  except (AssertionError,FileNotFoundError):pass
  else:raise AssertionError('missing/changed verifier result accepted')
review=json.loads((R/'docs/evidence/general-generation/support-review.json').read_text())
old={c['id']:c for c in review['models']['qwen3-4b']['cases']}
print('PASS: real verifier artifacts, fixed decision parser, missing/changed output rejection; semantic result is separately reviewed')
rows={c['id']:json.loads((d/'qwen25-7b'/(c['id']+'.json')).read_text()) for c in cases}
false_support=[];incomplete=[];retained=[];absence_errors=[];probe_errors=[]
for key,c in old.items():
 verdict=rows[key]['screen_route']
 if key in ['g11','g12']:
  if verdict=='SUPPORTED_COMPLETE':absence_errors.append(key)
 elif verdict=='SUPPORTED_COMPLETE':
  if not c['supported'] or not c['citation_correct']:false_support.append(key)
  if not c['complete']:incomplete.append(key)
  if c['useful_as_a_supported_complete_answer'] and c['citation_correct']:retained.append(key)
for c in cases:
 if c['id'].startswith('p') and rows[c['id']]['screen_route']!=c['expected']:probe_errors.append(c['id'])
summary={'false_support_approvals':false_support,'incomplete_approvals':incomplete,'supported_complete_educational_retained':retained,'absence_promoted':absence_errors,'probe_disagreements':probe_errors,'status':'FAIL' if false_support or incomplete or absence_errors or probe_errors or not retained else 'DEVELOPMENT_ONLY','production_qualification':False}
print(json.dumps(summary));sys.exit(1 if summary['status']=='FAIL' else 0)
