#!/usr/bin/env python3
"""Verify executable guard regressions separately; here bind measurements, identities and ratings."""
from pathlib import Path
import hashlib,json,collections,re
R=Path(__file__).resolve().parents[3];E=R/'docs/evidence/complete-claims'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text())
def validate_record(d):
 assert not d['error'],d['error']
 assert 0<d['tokens']<=256 and d['prompt_tokens']+256<=2048
 assert d['generation_total_ms']>0 and 0<d['first_token_ms']<=d['generation_total_ms']
 assert d['route'] in ['GENERATED','ABSTAINED','FALLBACK']
 if d['route']=='GENERATED':
  assert d['controller_invoked'] and not d['diagnostic_only'] and d['tokens']<256
  assert d['resolved_raw'].strip() in d['text']
  lines=d['raw'].strip().splitlines();assert 1<=len(lines)<=4
  for line in lines:
   assert re.match(r'^(?:\[S[0-9]+\]\s*)+.+\.$',line),line
   assert len(re.findall('[A-Za-z]+',re.sub(r'\[[^]]+\]','',line)))>=2
protocol=read(R/'tools/evaluation/complete-claims/protocol.json');old=read(R/'tools/evaluation/model-capability/protocol.json')
assert sha(R/'tools/evaluation/model-capability/protocol.json')==protocol['prior_cases_sha256']
assert len(protocol['cases'])==8 and len(old['cases'])==24
frozen=read(E/'integrity.json')
for name,digest in frozen['files'].items():assert sha(R/name)==digest,'Changed or missing evidence/source: '+name
model=R/'downloads/synthesis/model/Qwen3-1.7B-Q8_0.gguf';assert sha(model)==protocol['model_sha256']
for name,digest in protocol['packs'].items():assert sha(R/name)==digest
records={}
for stage in ['before','after']:
 m=read(E/stage/'manifest.json');assert m['exit_code']==0 and m['protocol_sha256']==sha(R/'tools/evaluation/complete-claims/protocol.json')
 assert m['model_sha256']==protocol['model_sha256'];assert 'six threads' in m['environment']
 for name,digest in m['artifacts'].items():assert sha(E/stage/name)==digest
 ids=[c['id'] for c in (old['cases'] if stage=='after' else [])+protocol['cases']];assert m['case_ids']==ids
 load=read(E/stage/'results/load.json');assert 'threads=6' in load['identity'] and 'context=2048' in load['identity']
 for i in ids:
  d=read(E/stage/'results'/(i+'.json'));validate_record(d);records[stage,i]=d
 if stage=='after':
  for name,digest in m['sources'].items():assert sha(R/name)==digest,'Product/harness changed since measured after run: '+name
  assert sha(R/'downloads/model-capability/host-v2-build/libpocketlore.so')==m['library_sha256']
for c in old['cases']:
 i=c['id'];records['before',i]=read(R/'docs/evidence/model-capability/run/qwen3-1.7b'/(i+'.json'))
 if not c['answerable']:
  for stage in ['before','after']:assert records[stage,i]['route']=='ABSTAINED' and not records[stage,i]['controller_invoked']
# Actual JNI proofs of optional second claim and removal of forced character cutoff.
assert records['after','cap-02']['route']=='GENERATED' and len(records['after','cap-02']['raw'].splitlines())==1
assert len(re.sub(r'\[[^]]+\]','',records['after','cap-13']['raw']).strip())>220
ratings=read(E/'builder-assessments.json');assert len(ratings['rows'])==64
summary={}
for stage in ['before','after']:
 for suite in ['prior24','new8']:
  rows=[r for r in ratings['rows'] if r['stage']==stage and r['case'].startswith('cap-' if suite=='prior24' else 'new-')]
  assert len(rows)==(24 if suite=='prior24' else 8)
  for r in rows:
   d=records[stage,r['case']];assert r['route']==d['route']
   p=(R/'docs/evidence/model-capability/run/qwen3-1.7b' if stage=='before' and suite=='prior24' else E/stage/'results')/(r['case']+'.json');assert r['record_sha256']==sha(p)
   assert r['published_support']==(r['raw_support'] if d['route']=='GENERATED' else 'withheld')
   assert r['published_fully_useful']==(d['route']=='GENERATED' and (r['raw_support'],r['raw_completeness'],r['raw_usefulness'])==('supported','full','useful'))
  summary[stage+'_'+suite]={'routes':dict(collections.Counter(r['route'] for r in rows)),'answerable':sum(r['answerable'] for r in rows),'fully_useful_supported_published':sum(r['published_fully_useful'] for r in rows),'unsupported_published':sum(r['published_support']=='unsupported' for r in rows),'absent_withheld':sum(not r['answerable'] and r['route']=='ABSTAINED' for r in rows)}
assert summary==read(E/'summary.json')
assert summary['after_prior24']['unsupported_published']<=summary['before_prior24']['unsupported_published']
# A negative usefulness outcome is reportable; do not demand positive scores or infer entailment.
em=E/'emulator';m=read(em/'manifest.json');assert m['case_ids']==protocol['emulator_cases'] and m['exit_code']==0
assert m['model_sha256']==protocol['model_sha256']
for name,digest in m['artifacts'].items():assert sha(em/name)==digest
assert 'INSTRUMENTATION_CODE: -1' in (em/'instrumentation.txt').read_text()
identity=read(em/'load.json')['identity'];assert 'threads=2' in identity and 'model-budget=2147483648' in identity and 'HOST SCREEN' not in identity
for i in m['case_ids']:validate_record(read(em/(i+'.json')))
assert read(em/'cap-02.json')['route']=='GENERATED'
# Regression: integrity checking must reject both missing and changed evidence, not just metadata flags.
def check_bytes(blob,digest):
 assert blob is not None and hashlib.sha256(blob).hexdigest()==digest
sample=E/'after/results/cap-02.json'
for bad in [None,sample.read_bytes()+b'changed']:
 try:check_bytes(bad,sha(sample))
 except AssertionError:pass
 else:raise AssertionError('Integrity mutation accepted')
print('PASS 64 before/after records, pinned model/packs/source hashes, three actual emulator JNI records, five absent gates and missing/changed evidence rejection')
print('Builder ratings reproduced; independent semantic review and physical acceptance remain open.')
