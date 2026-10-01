"""Artifact/behavior checks and separately declared builder-assessed quality gates."""
from pathlib import Path
import base64,hashlib,json,sqlite3,subprocess,tempfile,shutil
R=Path(__file__).resolve().parents[3];F=Path(__file__).parent;E=R/'docs/evidence/obligation-binding';TC=Path('/home/isa/Android/atlas-toolchain')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def require(x,m):
 if not x:raise AssertionError(m)
def exact(p,h):require(p.is_file() and sha(p)==h,'Missing/changed artifact: '+str(p))
def sealed(path):
 r=json.loads((path/'receipt.json').read_text());require(r['exit_code']==0 and not r['killed'],'Run failed or incomplete')
 for p,h in r['artifacts'].items():exact(path/p,h)
 return r
def reject(fn):
 try:fn()
 except (AssertionError,FileNotFoundError):return
 raise AssertionError('Mutation was not rejected')
def main():
 exact(F/'new-cases.json',(F/'new-cases.sha256').read_text().strip());new=json.loads((F/'new-cases.json').read_text());oldpath=R/'tools/evaluation/scale-model-quality/protocol.json';exact(oldpath,new['task220_protocol_sha256']);old=json.loads(oldpath.read_text());cases=old['cases']+new['cases'];require(len(cases)==60 and len({c['id'] for c in cases})==60,'Incomplete frozen cases')
 spec=json.loads((F/'execution.json').read_text());require((spec['context_tokens'],spec['draft_tokens'],spec['audit_tokens'])==(4096,320,192),'Budget drift')
 model=R/'downloads/model-capability/models/Qwen3-4B-Q4_K_M.gguf';exact(model,spec['model_sha256']);require(model.stat().st_size==2497280256,'Model identity size')
 require('74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db' in (R/'tools/answers/model.env').read_text(),'Production model changed')
 for line in (E/'SHA256SUMS').read_text().splitlines():h,p=line.split('  ',1);exact(R/p,h)
 run=E/'run';history=E/'history';sealed(run);sealed(history)
 manifest=json.loads((run/'manifest.json').read_text());exact(F/'execution.json',manifest['execution_sha256']);exact(F/'new-cases.json',manifest['protocol_sha256']);exact(R/'downloads/scale-model-quality/host-build/libpocketlore.so',manifest['library_sha256'])
 for p,h in manifest['sources'].items():exact(R/p,h)
 hm=json.loads((history/'manifest.json').read_text());exact(F/'history.json',hm['fixture_sha256']);require(hm['model_sha256']==spec['model_sha256'] and hm['library_sha256']==manifest['library_sha256'],'History native identity drift')
 for p,h in hm['source_hashes'].items():exact(R/p,h)
 inventory=json.loads((E/'build.json').read_text());exact(R/inventory['apk'],inventory['sha256'])
 db=R/'downloads/broad-reference/rendered-v2/index.sqlite';exact(db,'9009b19de43f851a815d1797779a94ab47077cc2fc5b3dfe70fc4bdf9a097386')
 # Exact source comparison is integrity/provenance, never a semantic support score.
 con=sqlite3.connect('file:'+str(db)+'?mode=ro',uri=True)
 review=json.loads((E/'review.json').read_text());require(review['reviewer'].startswith('builder'),'Builder labels missing');require(set(review['cases'])=={c['id'] for c in cases},'Missing source assessments')
 counts={'old_useful_eligible':0,'old_supported_drafts':0,'new_useful_eligible':0,'unsupported_eligible':0,'old_absent_withheld':0,'new_absent_withheld':0,'eligible':0,'withheld':0};enc=lambda s:base64.b64encode(s.encode()).decode();rows=[]
 for c in cases:
  p=run/'results'/(c['id']+'.json');v=json.loads(p.read_text());r=review['cases'][c['id']];exact(p,r['result_sha256']);require(v['question']==c['question'],'Question drift');require(v['draft']['tokens']>0,'No actual generation')
  require(v['draft']['tokens']<=320 and v['audit']['tokens']<=192 and v['draft']['tokens']+v['audit']['tokens']<=512,'Token budget violation')
  for stage in ('draft','audit'):
   s=v[stage]
   if s['tokens']:
    require(s['first_token_ms']>0 and s['total_ms']>=s['first_token_ms'],'Invalid timing');require(s['prompt_tokens']+(320 if stage=='draft' else 192)<=4096,'Context overflow')
  require(not any(v['native_after']),'Active context not released')
  byid={s['id']:s for s in c['sources']}
  for source in c['sources']:
   dbrow=con.execute('select p.body,p.sha,d.title,d.url,d.date,d.rights,d.sha from passages p join documents d on d.id=p.document where p.citation=?',(source['id'],)).fetchone()
   require(dbrow==tuple(source[k] for k in ['text','sha256','title','url','date','license','source_sha256']),'Source bytes or provenance drift')
  for claim in v['claims']:
   for ref in claim['references']:
    s=byid[ref['passage']];require(ref['edition']==old['source_edition_sha256'] and ref['passage_sha256']==s['sha256'] and ref['document_sha256']==s['source_sha256'],'Reference identity drift')
    # Android/Java offsets use UTF-16 code units, not Python codepoints.
    actual=s['text'].encode('utf-16-le')[ref['start_utf16']*2:ref['end_utf16']*2].decode('utf-16-le');require(actual==ref['text'],'Changed source span')
  require(len(r['claims'])==len(v['claims']) if v['claims'] else True,'Missing claim-level assessment')
  useful=r['all_claims_supported'] and r['all_cited_spans_support'] and r['obligations_complete'] and r['complete_prose'];require(r['fully_useful_draft']==useful,'Derived usefulness mismatch')
  eligible=v['route']=='SCREEN_ELIGIBLE';require(eligible==(not v['failure'] and bool(v['rendered'])),'Route integrity')
  counts['eligible' if eligible else 'withheld']+=1
  if eligible and not(r['all_claims_supported'] and r['all_cited_spans_support']):counts['unsupported_eligible']+=1
  absent='absent' in c['expected_route'] or c['kind']=='absence'
  if c['id'].startswith('s'):
   if absent and not eligible:counts['old_absent_withheld']+=1
   if not absent and useful:counts['old_supported_drafts']+=1
   if not absent and useful and eligible:counts['old_useful_eligible']+=1
  else:
   if absent and not eligible:counts['new_absent_withheld']+=1
   if not absent and useful and eligible:counts['new_useful_eligible']+=1
  rows.append('\t'.join([c['id'],enc(c['question']),enc(v['draft']['raw']),str(v['draft']['tokens']),enc(v['audit']['raw']),str(v['audit']['tokens']),enc(v['failure']),enc(v['rendered'])]))
 for h in json.loads((F/'history.json').read_text()):
  exact(R/h['original_path'],h['original_sha256'])
  v=json.loads((history/'results'/(h['id']+'.json')).read_text());require(v['claims'] and v['audit']['tokens']>0,'Historical test rejected only syntax or missing native audit')
 cancel=json.loads((history/'results/cancellation.json').read_text());require(cancel['callback_count']==1 and cancel['cancel_latency_ms']>=0 and cancel['retry_tokens']>0 and not any(cancel['after_cancel']) and not any(cancel['after_retry']),'Cancellation/retry failed')
 with tempfile.TemporaryDirectory(prefix='pocketlore-binding-check-') as tmp:
  t=Path(tmp);inputs=t/'inputs';shutil.copytree(run/'inputs',inputs);(inputs/'replay.tsv').write_text('\n'.join(rows)+'\n');classes=t/'classes';classes.mkdir();sources=[R/p for p in manifest['sources'] if p.endswith('.java')]+[F/'BehaviorHarness.java']
  subprocess.run([TC/'jdk/bin/javac','-d',classes,*sources],check=True);subprocess.run([TC/'jdk/bin/java','-cp',classes,'org.pocketlore.app.BehaviorHarness',inputs],check=True)
  original=run/'results/s01.json';changed=t/'changed.json';changed.write_bytes(original.read_bytes()+b' ');reject(lambda:exact(changed,sha(original)));reject(lambda:exact(t/'missing.json',sha(original)))
  # Real file hashing is exercised, not a self-reported validity flag.
  small=t/'changed-model.gguf'
  with small.open('wb') as f:f.truncate(model.stat().st_size)
  reject(lambda:exact(small,spec['model_sha256']));reject(lambda:exact(t/'missing.gguf',spec['model_sha256']))
 print(json.dumps({'artifact_behavior':'PASS','counts':counts,'builder_assessment_not_independent_review':True},indent=2),flush=True)
 failures=[]
 if counts['old_useful_eligible']<=4:failures.append('Useful old supported answers did not exceed4/40')
 if counts['unsupported_eligible']:failures.append('Unsupported screen-eligible answers remain')
 if counts['old_absent_withheld']!=8:failures.append('Old absent controls not all withheld')
 for h in json.loads((F/'history.json').read_text()):
  v=json.loads((history/'results'/(h['id']+'.json')).read_text())
  if not h['expected_support'] and v['route']=='SCREEN_ELIGIBLE':failures.append('Historical unsupported claim admitted: '+h['id'])
 require(not failures,'QUALITY FAIL: '+'; '.join(failures));print('PASS fixed source-binding behavioral and builder quality gates; independent criticism pending')
if __name__=='__main__':main()
