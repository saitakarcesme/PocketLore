#!/usr/bin/env python3
"""Verify real host comparison receipts and tamper rejection; not entailment certification."""
from pathlib import Path
import hashlib,json,shutil,tempfile,sys
R=Path(__file__).resolve().parents[2];F=R/'tools/evaluation/model-capability';E=R/'docs/evidence/model-capability'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def require(test,message):
 if not test:raise ValueError(message)
def validate(out,overrides=None):
 overrides=overrides or {}
 spec=json.loads((F/'protocol.json').read_text());execution=json.loads((F/'execution-v2.json').read_text());manifest=json.loads((out/'manifest.json').read_text())
 require(sha(F/'protocol.json')==manifest['protocol_sha256'],'protocol hash changed')
 require(len(spec['cases'])>=24 and len({c['topic'] for c in spec['cases']})>=4,'insufficient fixture breadth')
 require(set(c['type'] for c in spec['cases'])>={'comparison','explanation','multisource','qualifier','absent','contradiction'},'missing case type')
 require(manifest['execution_sha256']==sha(F/'execution-v2.json'),'execution changed')
 require([r['model'] for r in manifest['receipts']]==[m['id'] for m in execution['models']],'model set/order changed')
 require(execution['baseline']=='qwen3-1.7b','wrong current baseline')
 require(all(m['capacity_billion']>1.7 for m in execution['models'][1:]),'alternatives are not greater capacity')
 require(manifest['host_threads_per_process']==6 and manifest['max_concurrency'] in [1,2],'host policy changed')
 require(manifest['max_concurrency']==1 or manifest['admission_mem_available_bytes']>=12*1024**3,'parallel admission violated')
 require(sha(R/manifest['library_path'])==manifest['library_sha256'],'native library changed')
 for p,h in manifest['source_hashes'].items():require(sha(R/p)==h,'production/harness source changed: '+p)
 import zipfile,csv,io
 source_rows={}
 for p,h in spec['packs'].items():
  require(sha(R/p)==h,'pack changed')
  for row in csv.reader(io.StringIO(zipfile.ZipFile(R/p).read('passages.tsv').decode()),delimiter='\t'):
   source_rows[row[0]]=dict(zip(['id','title','url','date','license','text'],row))
 for c in spec['cases']:
  for s in c['sources']:require(s==source_rows[s['id']],'source excerpt changed or fabricated')
 prompts={};routes={};model_hashes=set()
 for receipt in manifest['receipts']:
  name=receipt['model'];pin=receipt['pin'];p=overrides.get(name,R/receipt['path'])
  pin_file=next(m['pin'] for m in execution['models'] if m['id']==name)
  require(pin==json.loads((F/pin_file).read_text()),'model pin changed')
  require(p.stat().st_size==pin['bytes']<=4*1024**3,'model size changed: '+name)
  require(sha(p)==pin['sha256'],'model hash changed: '+name);model_hashes.add(pin['sha256'])
  require(len(pin['revision'])==40 and pin['license'].lower() in ['apache-2.0','mit'],'unpinned model rights')
  require(sha(R/receipt['license_path'])==receipt['license_sha256'],'license changed')
  require(receipt['exit_code']==0,'failed model process: '+name)
  for p,h in receipt['artifact_hashes'].items():require(sha(out/p)==h,'run artifact changed: '+p)
  load=json.loads((out/name/'load.json').read_text());require(load['load_ms']>0 and 'bb4caa7540188872173c44d161602d9271386413' in load['identity'],'no measured pinned runtime load')
  require('threads=6' in load['identity'] and 'HOST SCREEN' in load['identity'],'wrong host runtime')
  require(len(list((out/name).glob('cap-*.json')))==24,'incomplete run')
  counts={}
  for c in spec['cases']:
   row=json.loads((out/name/(c['id']+'.json')).read_text())
   require(row['id']==c['id'] and row['question']==c['question'],'question changed')
   require(not row['error'] and row['raw'].strip() and 0<row['tokens']<=256,'no actual generation')
   require(0<row['first_token_ms']<=row['generation_total_ms'] and row['prompt_tokens']+row['tokens']<=2048,'invalid timing/budget')
   require(row['diagnostic_only']==(not row['controller_invoked']),'route conflation')
   require(row['route'] in ['GENERATED','FALLBACK','ABSTAINED'],'unknown controller route')
   if c['id'] in prompts:require(prompts[c['id']]==(row['system'],row['prompt']),'unequal supplied evidence/prompt')
   prompts[c['id']]=(row['system'],row['prompt']);counts[row['route']]=counts.get(row['route'],0)+1
  routes[name]=counts
 require(len(model_hashes)==3,'duplicate models')
 return routes

def main():
 out=E/'run'
 import subprocess
 subprocess.run([sys.executable,str(F/'check_host_policy.py')],check=True)
 routes=validate(out)
 # Sealed fixture and result set. Hash manifests are frozen at checkpoint; this
 # detects accidental drift, not a hostile editor rewriting Git and all hashes.
 for line in (E/'SHA256SUMS').read_text().splitlines():
  h,p=line.split('  ',1);require(sha(R/p)==h,'frozen evidence changed: '+p)
 assessments=json.loads((E/'builder-assessments.json').read_text())
 require(len(assessments['rows'])==72,'missing builder source review')
 require({(a['model'],a['case']) for a in assessments['rows']}=={(m,c['id']) for m in routes for c in json.loads((F/'protocol.json').read_text())['cases']},'assessment coverage changed')
 regression=[]
 with tempfile.TemporaryDirectory(prefix='pocketlore-capability-') as tmp:
  tmp=Path(tmp)
  def rejected(label,fn,expected):
   try:fn()
   except (ValueError,FileNotFoundError) as e:
    require(expected in str(e),'unexpected regression failure: '+str(e));regression.append(label);return
   raise ValueError('mutation accepted: '+label)
  copy=tmp/'run';shutil.copytree(out,copy)
  victim=copy/'qwen3-1.7b/cap-01.json';original=victim.read_bytes();victim.unlink()
  rejected('missing run record',lambda:validate(copy),'cap-01.json')
  victim.write_bytes(original+b' ')
  rejected('changed run record',lambda:validate(copy),'run artifact changed')
  rejected('missing model',lambda:validate(out,{'qwen3-1.7b':tmp/'missing.gguf'}),'missing.gguf')
  # Same-length sparse file tests actual SHA comparison, not only file presence/size.
  corrupt=tmp/'changed.gguf'
  with corrupt.open('wb') as f:f.truncate(1834426016)
  rejected('changed model bytes',lambda:validate(out,{'qwen3-1.7b':corrupt}),'model hash changed')
 print(json.dumps({'status':'PASS','scope':'72 real host outputs, exact evidence/model identity and tamper rejection; builder ratings are not independent entailment or acceptance','routes':routes,'mutation_rejections':regression},indent=2))
if __name__=='__main__':main()
