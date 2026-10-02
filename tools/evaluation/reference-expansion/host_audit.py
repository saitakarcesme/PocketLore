"""Audit one real host observation; never relabel it Android or generalization evidence."""
import hashlib,json,pathlib,copy,tempfile,shutil
ROOT=pathlib.Path(__file__).resolve().parents[3]
sha=lambda b:hashlib.sha256(b).hexdigest()
def verify(out,assessment):
 receipt=json.loads((out/'receipt.json').read_text());records=json.loads((out/'outputs.json').read_text())
 for name,h in receipt['files'].items():assert pathlib.Path(name).name==name and sha((out/name).read_bytes())==h
 for name,h in receipt['source_files'].items():assert sha((ROOT/name).read_bytes())==h
 protocol=ROOT/'tools/evaluation/reference-expansion/development.json';assert sha(protocol.read_bytes())==receipt['development_sha256']
 cases=json.loads(protocol.read_text())['cases'];assert len(records)==len(cases)==53
 labels={a['id']:a for a in assessment['cases']};assert len(labels)==len(records)
 for case,row in zip(cases,records):
  assert case['id']==row['id'];a=labels[row['id']];assert a['question']==case['question'] and a['rendered_sha256']==sha(row['rendered'].encode())
  assert row['generated'] is False and a['unsupported_attributed_claims']==0
  assert isinstance(a['useful_source_brief'],bool) and a['rationale']
  if case['absent']:assert not row['source_ids'] and a['appropriate_absence']
  for q in a['quotes']:
   assert q['source_id'] in row['source_ids'] and q['quoted_text_sha256']==q['admitted_span_sha256'] and q['exact_admitted_transformed_paragraph']
   assert sha((ROOT/q['original_html_path']).read_bytes())==q['original_html_sha256']
 for name in ['compile.txt','raw.tsv']:assert json.loads((out/(name+'.command.json')).read_text())['returncode']==0
 assert 'cancel_and_changed_license_rejected=true' in (out/'raw.tsv.stderr').read_text()
 useful=sum(a['useful_source_brief'] for a in labels.values());assert assessment['summary']['useful_source_briefs']==useful
 return dict(status='PASS',scope='Host development artifact/assessment audit only',cases=len(cases),useful_source_briefs=useful,appropriate_absence=sum(a['appropriate_absence'] for a in labels.values()),unsupported_attributed_claims=0)
def check():
 path=ROOT/'docs/evidence/reference-coverage-expansion/host-source-assessment.json';a=json.loads(path.read_text());out=ROOT/a['run_path']
 for f in a['input_artifacts']:assert sha((ROOT/f['path']).read_bytes())==f['sha256']
 result=verify(out,a);controls=[]
 for kind in ['missing-output','changed-output','changed-assessment']:
  with tempfile.TemporaryDirectory(prefix='reference480-host-') as td:
   target=pathlib.Path(td)
   for p in out.iterdir():
    if p.is_file():shutil.copyfile(p,target/p.name)
   altered=copy.deepcopy(a)
   if kind=='missing-output':(target/'outputs.json').unlink()
   elif kind=='changed-output':r=json.loads((target/'outputs.json').read_text());r[0]['rendered']+=' altered';(target/'outputs.json').write_text(json.dumps(r))
   else:altered['cases'][0]['rendered_sha256']='0'*64
   try:verify(target,altered)
   except (AssertionError,FileNotFoundError,KeyError,ValueError):controls.append(kind)
   else:raise AssertionError('Changed evidence accepted')
 result['negative_controls']=controls;return result
if __name__=='__main__':print(json.dumps(check(),indent=2))
