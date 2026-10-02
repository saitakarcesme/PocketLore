"""Validate actual experiment integrity separately from unresolved product gates."""
from pathlib import Path
import json,hashlib,tempfile,shutil,subprocess,sys
R=Path(__file__).resolve().parents[3];P=R/'docs/evidence/general-generation'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def artifacts(out):
 m=json.loads((out/'manifest.json').read_text())
 for n,h in m['inputs'].items():assert sha(R/n)==h,('input',n)
 assert sha(Path(m['runtime']['path']))==m['runtime']['sha256']
 assert len(m['runs'])==2
 for row in m['runs']:
  model=Path(row['model_path']);assert model.stat().st_size==row['model']['bytes'];assert sha(model)==row['model']['sha256']
  name='qwen3-4b' if 'Qwen3' in row['model']['filename'] else 'qwen25-7b';d=out/name
  for n,h in row['files'].items():assert sha(d/n)==h,(name,n)
  assert row['exit_code']==0,(name,'process failed')
  for i in range(1,13):
   x=json.loads((d/f'g{i:02d}.json').read_text());assert x['prompt_tokens']+512<=4096 and 0<=x['tokens']<=512
   assert x['screen_route']=='WITHHELD_PENDING_INDEPENDENT_ENTAILMENT_AND_COMPLETENESS'
 return m
h=json.loads((P/'HANDOFF.json').read_text());out=Path(h['run']);artifacts(out)
subprocess.run([sys.executable,R/'tools/evaluation/general-generation/behavior.py'],check=True)
negative=[]
# Copy only small run metadata/outputs, never model bytes.
for mutation in ['missing-output','changed-output','changed-model-identity','missing-model']:
 with tempfile.TemporaryDirectory() as tmp:
  d=Path(tmp)
  for name in ['manifest.json','qwen3-4b','qwen25-7b']:
   src=out/name
   if src.is_dir():shutil.copytree(src,d/name)
   else:shutil.copy2(src,d/name)
  if mutation=='missing-output':(d/'qwen3-4b/g01.json').unlink()
  elif mutation=='changed-output':(d/'qwen3-4b/g01.json').write_text('{}')
  else:
   m=json.loads((d/'manifest.json').read_text())
   if mutation=='changed-model-identity':m['runs'][0]['model']['sha256']='0'*64
   else:m['runs'][0]['model_path']=str(d/'missing.gguf')
   (d/'manifest.json').write_text(json.dumps(m))
  try:artifacts(d)
  except (AssertionError,FileNotFoundError):negative.append(mutation)
  else:raise AssertionError('Mutation accepted: '+mutation)
assert len(negative)==4
print(json.dumps({'artifact_behavior':'PASS','negative_controls':negative,'scope':'host development; no semantic approval inferred'}))
# Required check must not pass because safe withholding hides missing usefulness or Android qualification.
review=json.loads((P/'support-review.json').read_text()) if (P/'support-review.json').exists() else {}

if review:
 assert review['status']=='COMPLETE_SUPPLEMENTAL_REVIEW_PRODUCT_NOT_QUALIFIED'
 for name,model in review['models'].items():
  assert len(model['cases'])==12
  for case in model['cases']:assert sha(R/case['raw_path'])==case['raw_file_sha256']
gates={'independent_review_present':bool(review),'selected_model_android_jni_ui':False,'general_runtime_support_verifier_qualified':False,'current_complete_distribution_measured':False}
print(json.dumps({'product_gates':gates,'status':'FAIL','reason':'Host draft feasibility is not a qualified general supported Android answer path'}))
sys.exit(1)
