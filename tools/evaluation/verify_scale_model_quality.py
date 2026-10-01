#!/usr/bin/env python3
"""Verify measured host artifacts, source provenance and controller behavior, not entailment."""
from pathlib import Path
import base64,hashlib,json,sqlite3,subprocess,tempfile,sys,shutil
R=Path(__file__).resolve().parents[2];F=R/'tools/evaluation/scale-model-quality';E=R/'docs/evidence/scale-model-quality'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def require(ok,message):
 if not ok:raise ValueError(message)
def hashed(p,h):require(sha(p)==h,'Artifact hash changed: '+str(p))
def model(p,pin):
 require(p.stat().st_size==pin['bytes']<=6_000_000_000,'Model file size changed')
 hashed(p,pin['sha256'])
def run_artifacts(d,receipt):
 for path,h in receipt['artifact_hashes'].items():hashed(d/path,h)
def main():
 subprocess.run([sys.executable,str(F/'check_profiles.py')],check=True)
 protocol=json.loads((F/'protocol.json').read_text());hashed(F/'protocol.json',(F/'protocol.sha256').read_text().strip())
 cases=protocol['cases'];require(len(cases)>=48 and len({c['topic'] for c in cases})>=8,'Frozen case breadth missing')
 require({c['kind'] for c in cases}>={'literal','explanation','comparison','multi-part','false-premise','absence'},'Case shapes missing')
 # Exact source bytes and rights, independently from retrieval or model judgments.
 db=R/'downloads/broad-reference/rendered-v2/index.sqlite';hashed(db,'9009b19de43f851a815d1797779a94ab47077cc2fc5b3dfe70fc4bdf9a097386')
 con=sqlite3.connect('file:'+str(db)+'?mode=ro',uri=True)
 for c in cases:
  require(len(c['sources'])<=6 and len(c['obligations'])<=4,'Context plan unbounded')
  for s in c['sources']:
   row=con.execute('select p.body,p.sha,d.title,d.url,d.date,d.rights,d.sha from passages p join documents d on d.id=p.document where p.citation=?',(s['id'],)).fetchone()
   require(row==(s['text'],s['sha256'],s['title'],s['url'],s['date'],s['license'],s['source_sha256']),'Source bytes/provenance changed: '+s['id'])
 for line in (E/'SHA256SUMS').read_text().splitlines():
  h,path=line.split('  ',1);hashed(R/path,h)
 for stage,revision,execution,library in [('initial','9db899b','execution.json','host-build'),('buffer-v2','097fe24','execution-buffer-v2.json','host-buffer-v2-build')]:
  manifest=json.loads((E/'runs'/stage/'manifest.json').read_text())
  require(manifest['protocol_sha256']==sha(F/'protocol.json'),'Manifest protocol differs')
  require(manifest['execution_sha256']==sha(F/execution),'Execution policy changed')
  hashed(R/'downloads/scale-model-quality'/library/'libpocketlore.so',manifest['library_sha256'])
  for path,h in manifest['source_hashes'].items():
   archived=subprocess.check_output(['git','show',revision+':'+path],cwd=R)
   require(hashlib.sha256(archived).hexdigest()==h,'Compiled source identity changed: '+path)
   if path.endswith('.java'):hashed(R/path,h)
 for name in ['qwen25-7b','qwen15-moe']:
  failed=E/'runs/initial'/name;receipt=json.loads((failed/'receipt.json').read_text());run_artifacts(failed,receipt)
  for c in cases:
   v=json.loads((failed/(c['id']+'.json')).read_text())
   require(v['tokens']==0 and not v['raw'] and 'Runtime buffers exceed' in v['failure'],'Historical allocation failure overwritten')
 selection=json.loads((E/'selection.json').read_text());require(selection['deployment']=='unchanged production 0.5B','Optional model relabeled as deployed')
 require(set(selection['runs'])=={'baseline','qwen3-4b','qwen25-7b','qwen15-moe'},'Incomplete model matrix')
 prompts={};replay=[];counts={}
 for name,loc in selection['runs'].items():
  d=R/loc;receipt=json.loads((d/'receipt.json').read_text());pin=receipt['pin'];model(R/receipt['path'],pin)
  pins={'baseline':R/'tools/evaluation/model-capability/baseline.json','qwen3-4b':R/'tools/evaluation/model-capability/qwen3-4b.json','qwen25-7b':F/'qwen25-7b.json','qwen15-moe':F/'qwen15-moe.json'}
  require(pin==json.loads(pins[name].read_text()),'Pinned model differs from run')
  require(receipt['id']==name and receipt['exit_code']==0 and not receipt['timeout'],'Failed/incomplete quality run')
  require(len(pin['revision'])==40,'Mutable model revision');hashed(R/receipt['license'],receipt['license_sha256'])
  run_artifacts(d,receipt)
  load=json.loads((d/'load.json').read_text());require('bb4caa7540188872173c44d161602d9271386413' in load['identity'] and 'threads=6' in load['identity'],'Runtime identity differs')
  review=json.loads((E/'reviews'/f'{name}.json').read_text());require(set(review['cases'])=={c['id'] for c in cases},'Missing clause/source reviews: '+name)
  counts[name]={'candidate':0,'withheld':0,'useful_drafts_supported_population':0,'useful_abstentions':0,'unsupported_candidates':0}
  for c in cases:
   p=d/(c['id']+'.json');v=json.loads(p.read_text());a=review['cases'][c['id']];hashed(p,a['result_sha256'])
   require(v['question']==c['question'] and v['id']==c['id'],'Question changed')
   require(v['raw'].strip() and 0<v['tokens']<=512 and v['prompt_tokens']+512<=4096,'Missing generation or context overflow')
   require(0<v['first_token_ms']<=v['total_ms'] and v['native_after'][1]==0,'Timing/context release failed')
   require(v['native_peaks'][2]<=9_000_000_000 and v['native_peaks'][3]<=805306368 and v['native_peaks'][4]<=1073741824,'Native budget exceeded')
   prompt=(d/(c['id']+'.prompt.txt')).read_bytes()
   require(c['id'] not in prompts or prompts[c['id']]==prompt,'Unequal evidence prompts');prompts[c['id']]=prompt
   candidate=v['screen_route']=='CANDIDATE_FOR_SOURCE_REVIEW';require(candidate==(not v['failure']),'Route/failure mismatch')
   counts[name]['candidate' if candidate else 'withheld']+=1
   require(type(a['fully_useful_draft']) is bool and len(a['assessment'])>30,'Missing substantive builder assessment')
   if a['fully_useful_draft']:
    require(a['all_facts_supported'] and a['cited_claims_supported'] and a['obligations_complete'],'Useful score contradicts support review')
    counts[name]['useful_abstentions' if c['kind']=='absence' else 'useful_drafts_supported_population']+=1
   if candidate and not a['cited_claims_supported']:counts[name]['unsupported_candidates']+=1
   replay.append((c,v))
 # Actual Java gate replay, preserving both false withholding and unsupported candidates.
 with tempfile.TemporaryDirectory(prefix='pocketlore-scale-check-') as tmp:
  t=Path(tmp);enc=lambda x:base64.b64encode(str(x).encode()).decode()
  for c in cases:(t/(c['id']+'.tsv')).write_text(''.join('\t'.join(enc(s[k]) for k in ['id','title','url','date','license','text'])+'\n' for s in c['sources']))
  (t/'replay.tsv').write_text(''.join('\t'.join([c['id'],enc(c['question']),enc(v['raw']),str(v['excerpt_limit']),str(v['tokens']),enc(v['failure'])])+'\n' for c,v in replay))
  tc=Path('/home/isa/Android/atlas-toolchain/jdk/bin');sources=[R/'android/app/src/main/java/org/pocketlore/app'/(n+'.java') for n in ['ResearchEngine','EvidencePrompt','AnswerEngine','ObligationAnswer','NativeRuntime']]+[F/'ScaleHarness.java',F/'ReplayHarness.java']
  subprocess.run([tc/'javac','-d',t,*sources],check=True);subprocess.run([tc/'java','-cp',t,'org.pocketlore.app.ReplayHarness',t],check=True)
  # Shared validation functions must reject actual missing/changed bytes, not flags.
  def reject(fn):
   try:fn()
   except (FileNotFoundError,ValueError):return
   raise ValueError('Corruption accepted')
  original=R/selection['runs']['baseline'];copy=t/'changed-run';shutil.copytree(original,copy);receipt=json.loads((copy/'receipt.json').read_text())
  sample=copy/'s01.json';content=sample.read_bytes();sample.unlink();reject(lambda:run_artifacts(copy,receipt));sample.write_bytes(content+b' ');reject(lambda:run_artifacts(copy,receipt))
  baseline=receipt['pin'];reject(lambda:model(t/'missing.gguf',baseline))
  changed=t/'changed.gguf'
  with changed.open('wb') as f:f.truncate(baseline['bytes'])
  reject(lambda:model(changed,baseline))
 require(counts==selection['measured_counts'],'Reported selection counts do not match raw reviews')
 print(json.dumps({'status':'PASS','scope':'Host artifacts, exact sources and controller behavior; builder support judgments require independent review','counts':counts,'corruption_rejections':4},indent=2))
if __name__=='__main__':main()
