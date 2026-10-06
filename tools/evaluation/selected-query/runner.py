"""Execute and freeze bounded query engineering receipts; no Android runtime claim."""
import base64,copy,hashlib,json,pathlib,subprocess,sys,time,uuid,zlib
ROOT=pathlib.Path(__file__).resolve().parents[3];BASE=ROOT/'downloads/selected-source-query';ART=ROOT/'docs/evidence/selected-source-query-roundtrip-review.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def embed(path):
 raw=path.read_bytes();assert len(raw)<=16*1024**2
 return {'path':str(path),'bytes':len(raw),'sha256':sha(raw),'encoding':'zlib+base64','content':base64.b64encode(zlib.compress(raw)).decode()}
def validate(result,source):
 assert result['status']=='PASS' and result['source']==source,'Failed or stale executable result'
 assert len(result['positives'])==11 and len(result['genuine_retrieval'])==5,'Missing retrieval outcomes'
 assert all(x['rejected'] for x in result['negatives'].values()) and len(result['negatives'])>=16,'Missing or failed negative controls'
 assert not result['source_admission_established'] and not result['android_execution'],'False admission'
def main():
 run=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'-'+uuid.uuid4().hex[:8];out=BASE/run;out.mkdir(parents=True);start=time.time();code=list((ROOT/'tools/packs/selected-source').glob('*.py'))+list(pathlib.Path(__file__).parent.glob('*.py'))+[ROOT/'tools/packs/source-structure/produce.py',ROOT/'tools/packs/complete-source/production.py',ROOT/'tools/packs/complete-source/compact.py',ROOT/'tools/evaluation/check_selected_source_query_roundtrip.sh'];source={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in code};report={'run_id':run,'start':start,'status':'FAIL','source':source,'commands':[],'errors':[],'raw':[],'source_admission_established':False,'android_execution':False}
 try:
  for name,argv in [('controls',['python3',str(pathlib.Path(__file__).with_name('check.py')),str(out/'controls')]),('same_input_baseline',['python3',str(pathlib.Path(__file__).with_name('baseline.py')),str(out/'controls/originals'),str(out/'baseline')])]:
   t=time.time();r=subprocess.run(argv,capture_output=True,timeout=30,cwd=ROOT);(out/(name+'.stdout')).write_bytes(r.stdout);(out/(name+'.stderr')).write_bytes(r.stderr);report['commands'].append({'name':name,'argv':argv,'start':t,'end':time.time(),'exit':r.returncode});assert r.returncode==0,name+' failed'
  result=json.loads((out/'controls/result.json').read_text());expected={n:source[n] for n in result['source']};validate(result,expected)
  rejected=[]
  for label in ('stale','failed','missing'):
   bad=copy.deepcopy(result)
   if label=='stale':bad['source']['tools/packs/selected-source/read.py']='0'*64
   elif label=='failed':bad['status']='FAIL'
   else:bad['positives']=[]
   try:validate(bad,expected)
   except AssertionError:rejected.append(label)
   else:raise AssertionError('Invalid evidence accepted')
  report['evidence_negative_controls']=rejected;report['controls']=result;report['baseline']=json.loads((out/'baseline/result.json').read_text());assert len(report['baseline']['input_hashes'])==18
  report['current_storage']={'bytes':(out/'controls/index.sqlite').stat().st_size,'allocated_bytes':(out/'controls/index.sqlite').stat().st_blocks*512,'sha256':sha((out/'controls/index.sqlite').read_bytes())};assert report['current_storage']['sha256']==result['index_sha256']
  for name,digest in report['baseline']['input_hashes'].items():assert sha((out/'controls/originals'/name).read_bytes())==digest
  build=json.loads((BASE/'build/build.json').read_text());assert build['exit']==0 and build['inputs_unchanged']
  for name,digest in build['source_inputs_before'].items():assert sha((ROOT/name).read_bytes())==digest
  assert sha((ROOT/'android/app/build/outputs/apk/debug/app-debug.apk').read_bytes())==build['apk_sha256'];report['build']=build
  assert {str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in code}==source
  report['status']='PASS';report['scope']='Bounded host query/source roundtrip engineering and Android compilation only'
 except BaseException as e:report['errors'].append(type(e).__name__+': '+str(e))
 finally:
  report['end']=time.time();report['unproven']=['Terminal Android runtime untouched: no Android query/import/export/restart observations','New index code has no revised6000/12000 dedicated-kernel scale qualification','Whole-source/latest/rights>=1.25M floor/2–3M target remain unmet','Full45GBtarget/50GBinstalled-update/12GBdevice and physical/unseen quality remain unproven','URL attribution route preserved; imported notices/modification/nontext/quotation obligations and semantic support remain separately unverified']
  files=code+list(out.rglob('*.json'))+list(out.glob('*.stdout'))+list(out.glob('*.stderr'))+list(BASE.glob('*.log'))+list(BASE.glob('*/result.json'))+list((BASE/'build').glob('*'))+list((BASE/'before-code').rglob('*.py'))+list((ROOT/'docs/evidence/selected-source-query').glob('*'))
  overnight=pathlib.Path('/home/isa/PocketLore-control/overnight-20261005')
  for folder in ['source-v3-cross-inline-prerequisites-20261006T0600Z','source-context-independent-prerequisites-20261006T0606Z','source-context-attribution-scope-erratum-20261006T0610Z']:
   files += [p for p in (overnight/folder).rglob('*') if p.suffix in ('.json','.py','.html')]
  seen=set()
  for path in files:
   if path.is_file() and path not in seen and path.stat().st_size<=16*1024**2:report['raw'].append(embed(path));seen.add(path)
  rendered=json.dumps(report,indent=2)+'\n';assert len(rendered.encode())<32*1024**2;ART.write_text(rendered);(out/'outcome.json').write_text(json.dumps({'exit':0 if report['status']=='PASS' else 1,'review_sha256':sha(rendered.encode())}));print(json.dumps({k:report[k] for k in ('run_id','status','errors','unproven')},indent=2))
 return 0 if report['status']=='PASS' else 1
if __name__=='__main__':sys.exit(main())
