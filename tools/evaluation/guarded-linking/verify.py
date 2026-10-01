"""Verify guarded composition over real immutable scores, then enforce final support gates."""
from pathlib import Path
import json,hashlib,importlib.util,tempfile,subprocess
R=Path(__file__).resolve().parents[3];F=Path(__file__).parent;E=R/'docs/evidence/guarded-linking'
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 old=module('historical_linking',R/'tools/evaluation/independent-linking/verify.py');exact=old.exact;require=old.require;sha=old.sha
 for directory in [E,R/'docs/evidence/fact-frames',R/'docs/evidence/independent-linking-reuse']:
  for line in (directory/'SHA256SUMS').read_text().splitlines():h,p=line.split('  ',1);exact(R/p,h)
 build=E/'build.json';historical=old.main(diagnostic=True,build_receipt=(build,sha(build)))
 require(historical['unsupported_eligible']==8 and historical['old_useful_eligible']==8,'Historical negative result changed')
 rep=E/'replay';receipt=json.loads((rep/'receipt.json').read_text());require(receipt['exit_code']==0,'Incomplete replay');exact(F/'protocol.json',receipt['protocol_sha256']);exact(R/'docs/evidence/independent-linking/SHA256SUMS',receipt['inputs_seal'])
 for p,h in receipt['artifacts'].items():exact(rep/p,h)
 for p,h in receipt['sources'].items():exact(R/p,h)
 # Frame semantics remain the previously measured implementation, not rewritten to pass this matrix.
 frame_manifest=json.loads((R/'docs/evidence/fact-frames/replay/manifest.json').read_text())
 for p,h in frame_manifest['sources'].items():
  if p.endswith('.java'):exact(R/p,h)
 with tempfile.TemporaryDirectory(prefix='pocketlore-guarded-') as tmp:
  t=Path(tmp);replay=module('guarded_replay',F/'replay.py');require(replay.run(t/'replay')==0,'Current controller failed');exact(t/'replay/results/linked.json',sha(rep/'results/linked.json'));exact(t/'replay/results/pairs.json',sha(R/'docs/evidence/independent-linking/scoring/prepared/pairs.json'))
  src=[R/'tools/evaluation/fact-frames/FrameBehavior.java',R/'tools/evaluation/independent-linking/LinkBehavior.java',F/'GuardedBehavior.java'];classes=t/'replay/classes';tc=replay.TC
  subprocess.run([tc/'javac','-cp',classes,'-d',classes,*src],check=True)
  for cls in ['FrameBehavior','GuardedBehavior']:subprocess.run([tc/'java','-cp',classes,'org.pocketlore.app.'+cls],check=True)
  changed=t/'changed-results';changed.write_bytes((rep/'results/linked.json').read_bytes()+b'changed');old.rejected(lambda:exact(changed,sha(rep/'results/linked.json')));old.rejected(lambda:exact(t/'missing-results',sha(rep/'results/linked.json')))
  # Actual generator artifact pin is checked by historical verifier; mutation must also fail.
  model=t/'changed-model.gguf';original=R/'downloads/model-capability/models/Qwen3-4B-Q4_K_M.gguf'
  with model.open('wb') as f:f.truncate(original.stat().st_size)
  pin='7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5';old.rejected(lambda:exact(model,pin));old.rejected(lambda:exact(t/'missing-model.gguf',pin))
 values=json.loads((rep/'results/linked.json').read_text());require(len(values)==103,'Population changed');reviews=json.loads((E/'review.json').read_text());require(reviews['reviewer'].startswith('builder'),'Review role');require(set(reviews['cases'])=={v['id'] for v in values},'Missing review')
 prior={v['id']:v for v in json.loads((R/'docs/evidence/fact-frames/replay/results/linked.json').read_text())};nli={v['id']:v for v in json.loads((R/'docs/evidence/independent-linking/scoring/final/linked.json').read_text())}
 cases=json.loads((R/'tools/evaluation/scale-model-quality/protocol.json').read_text())['cases']+json.loads((R/'tools/evaluation/obligation-binding/new-cases.json').read_text())['cases'];absent={c['id'] for c in cases if 'absent' in c.get('expected_route','') or c.get('kind')=='absence'}
 counts={'eligible':0,'withheld':0,'old_useful':0,'unsupported':0,'absent_withheld':0,'new_useful':0}
 for v in values:
  id=v['id'];r=reviews['cases'][id];require(r['record_sha256']==hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest(),'Review drift');eligible=v['route']=='SCREEN_ELIGIBLE';require(eligible==(bool(v['rendered']) and bool(v['claims']) and not v['failure']),'Route mismatch');counts['eligible' if eligible else 'withheld']+=1
  if id in absent and not eligible:counts['absent_withheld']+=1
  if eligible:
   require(nli[id]['route']=='SCREEN_ELIGIBLE','Classifier rejection bypassed');require(v['classifier_claims']==nli[id]['claims'],'Scored binding changed');require(prior[id]['route']=='SCREEN_ELIGIBLE','Semantic rejection bypassed')
   for field in ['rendered','claims','links']:require(v[field]==prior[id][field],'Source-reviewed final prose or typed references changed')
   require(len(r['claims'])==len(v['claims']),'Unreviewed published claim');counts['unsupported']+=not r['supported']
   if r['supported'] and r['complete'] and r['useful']:
    if id.startswith('s'):counts['old_useful']+=1
    if id.startswith('l'):counts['new_useful']+=1
 require(counts==json.loads((E/'metrics.json').read_text())['counts'],'Derived count drift');print(json.dumps({'guarded_behavior':'PASS','builder_counts':counts,'independent_review':'pending','scope':'Retrospective finite public regression; classifier alone remains failing'},indent=2),flush=True)
 require(counts['old_useful']>4 and counts['unsupported']==0 and counts['absent_withheld']==len(absent)==9,'QUALITY FAIL: support/usefulness/absence')
 print('GUARDED QUALITY PASS on preserved public development; not general entailment or deployment')
if __name__=='__main__':main()
