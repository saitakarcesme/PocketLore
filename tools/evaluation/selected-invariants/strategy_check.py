"""Current context-inspection execution; preserve unchanged full aggregate gates."""
import base64,hashlib,json,pathlib,subprocess,sys,time,uuid,zlib
ROOT=pathlib.Path(__file__).resolve().parents[3];BASE=ROOT/'downloads/selected-source-invariants-strategy';ART=ROOT/'docs/evidence/selected-source-invariants-review.json'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def embed(path):
 raw=path.read_bytes();assert len(raw)<=16*1024**2
 return {'path':str(path),'sha256':sha(raw),'bytes':len(raw),'encoding':'zlib+base64','content':base64.b64encode(zlib.compress(raw)).decode()}
def main():
 run=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'-'+uuid.uuid4().hex[:8];out=BASE/run;out.mkdir(parents=True);paths=[ROOT/'tools/packs/selected-source/read.py',pathlib.Path(__file__),pathlib.Path(__file__).with_name('context_inspection.py'),ROOT/'tools/evaluation/check_selected_source_invariants.sh'];source={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in paths}
 report={'task':'523-complete-source-selected-invariants-and-context-eligibility-strategy-change','run_id':run,'status':'FAIL','start':time.time(),'source':source,'commands':[],'raw':[],'errors':[],'source_admission_established':False,'android_execution':False,'production_launch_qualified':False}
 try:
  previous=subprocess.check_output(['git','show','8f261e2f57f87e366211a5d931f5588d5c346b46:docs/evidence/selected-source-invariants-review.json']);(out/'preserved-repair2.json').write_bytes(previous)
  p=json.loads(previous);assert p['status']=='FAIL';report['preserved_failed_checkpoint']='8f261e2f57f87e366211a5d931f5588d5c346b46'
  assert sha((ROOT/'tools/packs/selected-source/producer.py').read_bytes())==p['producer_code']['tools/packs/selected-source/producer.py'];report['producer_unchanged']=True
  command=['python3',str(pathlib.Path(__file__).with_name('context_inspection.py')),str(out/'context')];start=time.time();r=subprocess.run(command,capture_output=True,timeout=30,cwd=ROOT);(out/'stdout').write_bytes(r.stdout);(out/'stderr').write_bytes(r.stderr);report['commands'].append({'argv':command,'start':start,'end':time.time(),'exit':r.returncode});assert r.returncode==0,'Current source context control failed'
  result=json.loads((out/'context/result.json').read_text());assert result['status']=='PASS' and len(result['positive'])==5 and not result['independently_generation_eligible_contexts'];assert result['reader_sha256']==source['tools/packs/selected-source/read.py'] and result['test_sha256']==source['tools/evaluation/selected-invariants/context_inspection.py'];report['current_context_controls']=result
  build=json.loads((BASE/'build/build.json').read_text());assert build['exit']==0 and build['inputs_unchanged']
  for name,digest in build['source_inputs_before'].items():assert sha((ROOT/name).read_bytes())==digest
  report['build']=build
  assert {str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in paths}==source
  report['host_context_controls_pass']=True
 except BaseException as e:report['errors'].append(type(e).__name__+': '+str(e))
 finally:
  report['unmet_gates']=['Current-code 6000/12000 source candidate execution under dedicated 512MiB/swap0/CPU400/Tasks32 kernel limits remains absent.','Independent source packet explicitly grants zero generation eligibility: full attribution and additional quotation rights remain unresolved.','Actual Android v3 reader/import/export/restart remains unexecuted after terminal emulator; bounded host inspection is not Android proof.','Whole original/latest/disposition identity, >=1.25M eligible full articles (target 2–3M), 45GB target/50GB installed-update and 12GB device profile remain unproven.']
  packet=pathlib.Path('/home/isa/PocketLore-control/overnight-20261005/source-context-independent-prerequisites-20261006T0606Z');files=list(packet.glob('*.json'))+paths+list(out.glob('*'))+list(BASE.glob('context-*.log'))+list(BASE.glob('context-*/result.json'))+[BASE/'reader-before.py']+list((BASE/'build').glob('*'))+[ROOT/'docs/evidence/523-complete-source-selected-invariants-and-context-eligibility-strategy-change.md',ROOT/'docs/evidence/selected-source-invariants-launch.json']
  original=pathlib.Path('/home/isa/PocketLore-control/overnight-20261005');files += [original/'source-reader-prerequisite-review-20261006T0323Z'/('original-'+str(n)+'.json') for n in [2956,100000]]+[original/'source-reader-genuine-extended-review-20261006T0403Z'/('original-'+str(n)+'.json') for n in [1263712,342233,5010470]]
  seen=set()
  for path in files:
   if path.is_file() and path not in seen and path.suffix not in ('.sqlite','.apk','.class') and path.stat().st_size<=16*1024**2:report['raw'].append(embed(path));seen.add(path)
  report['end']=time.time();rendered=json.dumps(report,indent=2)+'\n';assert len(rendered.encode())<32*1024**2;ART.write_text(rendered);(out/'outcome.json').write_text(json.dumps({'exit':1,'review_sha256':sha(rendered.encode()),'errors':report['errors']}));print(json.dumps({'status':'FAIL','host_context_controls_pass':report.get('host_context_controls_pass',False),'errors':report['errors'],'unmet_gates':report['unmet_gates']},indent=2))
 return 1
if __name__=='__main__':sys.exit(main())
