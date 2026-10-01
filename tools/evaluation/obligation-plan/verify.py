"""Verify source-plan behavior, actual saved native stages, and source-reviewed quality."""
from pathlib import Path
import json,hashlib,subprocess,tempfile,base64,sys,importlib.util
R=Path(__file__).resolve().parents[3];F=Path(__file__).parent;E=R/'docs/evidence/obligation-ledger';TC=Path('/home/isa/Android/atlas-toolchain/jdk/bin')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def require(v,m):
 if not v:raise AssertionError(m)
def exact(p,h):require(p.is_file() and sha(p)==h,'Missing/changed '+str(p))
def rejected(fn):
 try:fn()
 except (AssertionError,FileNotFoundError):return
 raise AssertionError('Mutation admitted')
def main(*, diagnostic=False, build_receipt=None):
 for line in (E/'SHA256SUMS').read_text().splitlines():h,p=line.split('  ',1);exact(R/p,h)
 fixture=json.loads((R/'tools/evaluation/source-plan/fixtures.json').read_text());exact(R/'tools/evaluation/source-plan/fixtures.json',(R/'tools/evaluation/source-plan/fixtures.sha256').read_text().strip());require(len(fixture['cases'])==24 and len({c['topic'] for c in fixture['cases']})==6,'Frozen coverage')
 previous=json.loads((R/'tools/evaluation/fact-frames/fixtures.json').read_text());byorigin={c['id']:c for c in previous['cases']};exact(R/'tools/evaluation/fact-frames/fixtures.json',fixture['previous_fixture_sha256'])
 for c in fixture['cases']:require(c['sources']==byorigin[c['origin_case']]['sources'],'Source/provenance drift')
 # Preserve prior negative protocols/runs; current build checked by historical behavior chain.
 for directory in ['source-plan','source-plan-parser','equation-plan']:
  for line in (R/'docs/evidence'/directory/'SHA256SUMS').read_text().splitlines():h,p=line.split('  ',1);exact(R/p,h)
 sys.path.insert(0,str(R/'tools/evaluation/source-plan'));spec=importlib.util.spec_from_file_location('old_source_plan',R/'tools/evaluation/source-plan/verify.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old);previous=old.main(diagnostic=True,build_receipt=(E/'build.json',sha(E/'build.json')));require(previous['useful']==0,'Historical result drift')
 run=E/'run';receipt=json.loads((run/'receipt.json').read_text());require(receipt['exit_code']==0 and not receipt['killed'],'Partial/failed native run')
 for p,h in receipt['artifacts'].items():exact(run/p,h)
 manifest=json.loads((run/'manifest.json').read_text());exact(R/'tools/evaluation/source-plan/fixtures.json',manifest['protocol_sha256']);exact(E/'declared-protocol.md',manifest['execution_sha256']);exact(R/'downloads/model-capability/models/Qwen3-4B-Q4_K_M.gguf',manifest['model_sha256']);require(manifest['model_sha256']=='7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5','Model role/pin');exact(R/'downloads/scale-model-quality/host-build/libpocketlore.so',manifest['library_sha256'])
 for p,h in manifest['sources'].items():exact(R/p,h)
 review=json.loads((E/'review.json').read_text());require(review['reviewer'].startswith('builder'),'Source review role');require(set(review['cases'])=={c['id'] for c in fixture['cases']},'Review coverage')
 values=[];counts={'eligible':0,'withheld':0,'unsupported':0,'useful':0,'absent_withheld':0,'plan_calls':0,'prose_calls':0};encode=lambda s:base64.b64encode(s.encode()).decode();rows=[]
 for c in fixture['cases']:
  v=json.loads((run/'results'/(c['id']+'.json')).read_text());require(v['question']==c['question'],'Question drift');values.append(v);r=review['cases'][c['id']];require(r['record_sha256']==hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest(),'Review/output drift');require(v['native_after']==[1,0,0,0,0],'Leaked native context')
  require(v['plan']['tokens']+v['draft']['tokens']<=512,'Total token budget')
  for stage,limit,key in [('plan',160,'plan_calls'),('draft',352,'prose_calls')]:
   s=v[stage];require(0<=s['tokens']<=limit,'Stage token budget')
   if s['tokens']:
    counts[key]+=1;require(s['prompt_tokens']+limit<=4096 and 0<s['first_token_ms']<=s['total_ms'],'Real stage timing/context')
  require(v['route'] in ['REVIEW_CANDIDATE','WITHHELD'],'Unknown route');eligible=v['route']=='REVIEW_CANDIDATE';require(eligible==(bool(v['rendered']) and bool(v['claims']) and not v['failure']),'Route drift');counts['eligible' if eligible else 'withheld']+=1
  if c['expected_route']=='absent' and not eligible:counts['absent_withheld']+=1
  if eligible:
   require(len(r['claims'])==len(v['claims']),'Unreviewed clause');counts['unsupported']+=not r['supported'];counts['useful']+=all(r[k] for k in ['supported','complete','useful'])
   require(all(a['text']==claim['text'] for a,claim in zip(r['claims'],v['claims'])),'Claim review text drift');require(r['supported']==all(a['supported'] for a in r['claims']),'Claim support aggregation drift')
   require(len(v['links'])==len(v['claims']),'Missing typed citation link')
   sources={s['id']:s for s in c['sources']}
   for i,(claim,link) in enumerate(zip(v['claims'],v['links'])):
    require(v['rendered'].encode('utf-16-le')[link['start_utf16']*2:link['end_utf16']*2].decode('utf-16-le')=='['+str(i+1)+']','Typed citation range')
    for ref in claim['references']:
     s=sources[ref['passage']];require(ref['edition']==fixture['source_edition_sha256'] and ref['passage_sha256']==s['sha256'] and ref['document_sha256']==s['source_sha256'],'Citation provenance');require(s['text'].encode('utf-16-le')[ref['start_utf16']*2:ref['end_utf16']*2].decode('utf-16-le')==ref['text'],'Exact citation span')
  rows.append('\t'.join([c['id'],encode(v['question']),encode(v['plan']['raw']),str(v['plan']['tokens']),encode(v['draft']['raw']),str(v['draft']['tokens']),encode(v['plan']['failure']),encode(v['draft']['failure'])]))
 require(json.loads((run/'results/closed.json').read_text())==[0,0,0,0,0],'Model not closed')
 with tempfile.TemporaryDirectory(prefix='pocketlore-plan-') as tmp:
  t=Path(tmp);classes=t/'classes';classes.mkdir();sources=[R/p for p in manifest['sources'] if p.endswith('.java')]+[F/'ReplayLedger.java',F/'PlanReceipt.java',F/'Behavior.java',R/'tools/evaluation/fact-frames/FrameBehavior.java'];subprocess.run([TC/'javac','-d',classes,*sources],check=True);controls=json.loads((F/'controls.json').read_text());controlfile=t/'controls.tsv';controlfile.write_text('\n'.join(encode(v) for v in [controls['valid']]+controls['invalid'])+'\n');subprocess.run([TC/'java','-cp',classes,'org.pocketlore.app.Behavior',controlfile],check=True)
  rowsfile=t/'stages.tsv';rowsfile.write_text('\n'.join(rows)+'\n');subprocess.run([TC/'java','-cp',classes,'org.pocketlore.app.ReplayLedger',run/'inputs',rowsfile,t/'replay.json'],check=True)
  subprocess.run([TC/'java','-cp',classes,'org.pocketlore.app.PlanReceipt',run/'inputs',rowsfile,t/'plans.json'],check=True);exact(t/'plans.json',sha(E/'plans.json'))
  for actual,expected in zip(json.loads((t/'replay.json').read_text()),values):
   for k in ['id','rendered','claims','failure']:require(actual[k]==expected[k],'Controller replay mismatch')
  changed=t/'changed-plan';original=run/'results/q10.json';changed.write_bytes(original.read_bytes()+b'changed');rejected(lambda:exact(changed,sha(original)));rejected(lambda:exact(t/'missing-plan',sha(original)))
 require(counts==json.loads((E/'metrics.json').read_text())['counts'],'Derived counts');print(json.dumps({'behavior':'PASS','builder_review_candidate_counts':counts,'independent_review':'pending'},indent=2),flush=True)
 if diagnostic:return counts
 require(counts['unsupported']==0 and counts['absent_withheld']==4 and counts['useful']>0,'CANDIDATE QUALITY FAIL: unsupported, absent or no complete useful generated answer')
 print('Candidate quality passed builder source review only; no deployment authorization')
 raise AssertionError('PUBLICATION GATE FAIL: independent semantic authorization is not implemented; review candidates cannot be published')
if __name__=='__main__':main()
