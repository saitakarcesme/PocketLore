"""Read-only recovery audit; do not rerun unchanged controls when external gates are absent."""
import base64,hashlib,json,pathlib,subprocess,sys,time,zlib
ROOT=pathlib.Path(__file__).resolve().parents[3]
COMMIT='b5d490c11ad9131f83593c1d8e5f1262e75b236a'
ART=ROOT/'docs/evidence/selected-source-invariants-review.json'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def embed(raw):return {'sha256':sha(raw),'bytes':len(raw),'encoding':'zlib+base64','content':base64.b64encode(zlib.compress(raw)).decode()}
def audit(previous):
 for item in previous['raw']:
  raw=zlib.decompress(base64.b64decode(item['content']));assert len(raw)==item['bytes'] and sha(raw)==item['sha256'],'Corrupt prior raw receipt'
 for name,digest in previous['source'].items():
  # This new wrapper is a preflight, not historical execution of the old wrapper.
  if name=='tools/evaluation/check_selected_source_invariants.sh':continue
  assert sha((ROOT/name).read_bytes())==digest,'Changed historical test/producer input: '+name
 assert previous['status']=='FAIL' and previous['host_controls_pass'] is True
 return {'producer_and_test_inputs_match':True,'verified_raw_files':len(previous['raw']),'prior_run_id':previous['run_id'],'prior_gate':'FAIL','fresh_host_controls_executed':False}
def main():
 started=time.time();raw=subprocess.check_output(['git','show',COMMIT+':docs/evidence/selected-source-invariants-review.json'],cwd=ROOT);previous=json.loads(raw);verification=audit(previous)
 # Demonstrate that a corrupted embedded receipt and changed code identity fail closed.
 import copy
 negatives={}
 for name in ['raw','source']:
  bad=copy.deepcopy(previous)
  if name=='raw':bad['raw'][0]['sha256']='0'*64
  else:bad['source']['tools/packs/selected-source/producer.py']='0'*64
  try:audit(bad)
  except AssertionError:negatives[name]=True
  else:raise AssertionError('Recovery audit accepted corrupt '+name)
 bus=subprocess.run(['systemctl','--user','show','--property=Version'],capture_output=True,timeout=5)
 group=next(line[3:] for line in pathlib.Path('/proc/self/cgroup').read_text().splitlines() if line.startswith('0::'));cg=pathlib.Path('/sys/fs/cgroup')/group.lstrip('/');limits={n:(cg/n).read_text().strip() for n in ['memory.max','memory.swap.max','cpu.max','pids.max']}
 launch=json.loads((ROOT/'docs/evidence/selected-source-invariants-launch.json').read_text());missing=[]
 for command in launch['short_scale_commands_sequential']:
  out=pathlib.Path(command['output'])
  for name in ['owner.json','status.json','index.sqlite']:
   if not (out/name).is_file():missing.append(str(out/name))
 from external_receipts import load_packet,validate_bindings,validate_index
 request=ROOT/'downloads/selected-source-invariants/external-receipts.json'
 external={'request_present':request.is_file(),'runs':[],'errors':[],'scope':'Kernel/code/index/disposition identities only, not source fidelity, context rights or Android qualification'}
 expected_names=['tools/packs/selected-source/producer.py','tools/packs/source-structure/produce.py','tools/packs/complete-source/production.py','tools/packs/complete-source/compact.py']
 expected_code={name:sha((ROOT/name).read_bytes()) for name in expected_names}
 if request.is_file():
  try:
   require_request=json.loads(request.read_text());assert [r['count'] for r in require_request['runs']]==[6000,12000],'Exactly the two required scales are needed'
   for item in require_request['runs']:
    assert item['through']==99999,'Unexpected frozen prefix'
    bundle=load_packet(item['packet_root'],item['manifest_sha256']);validated=validate_bindings(bundle,expected_code,item['count'],item['through']);validated['index']=validate_index(bundle,item['index_path']);external['runs'].append(validated)
  except (AssertionError,ValueError,KeyError,TypeError,IndexError,OSError) as error:external['errors'].append(type(error).__name__+': '+str(error))
 else:external['errors'].append('No independently pinned external-receipts.json for current 6000/12000 source')
 blockers=[]
 if len(external['runs'])!=2 or external['errors']:blockers.append('Required current-code 6000/12000 kernel/index receipts have not validated: '+'; '.join(external['errors']))
 blockers.extend(['Independent current-scale original/capsule/context fidelity and rights eligibility review remain missing.','Android execution, complete-source admission and whole-profile budget qualification remain missing.'])
 report={'task':'523-complete-source-selected-invariants-and-context-eligibility-repair-2','status':'FAIL','stage':'external-receipt-validation','start':started,'end':time.time(),'recovered_commit':COMMIT,'recovered_evidence':embed(raw),'historical_verification':verification,'negative_controls':negatives,'current_kernel':{'path':str(cg),'limits':limits},'bus':{'exit':bus.returncode,'stderr':bus.stderr.decode(),'stdout':bus.stdout.decode()},'missing_current_scale_files':missing,'producer_code':launch['code'],'preflight_source':embed(pathlib.Path(__file__).read_bytes()),'prior_aggregate_failure_preserved':True,'source_admission_established':False,'production_launch_qualified':False,'android_execution':False,'commands_skipped':['unchanged seven-source host suite','revised scale production launch','terminal emulator probes'],'unmet_gates':blockers,'external_receipt_identity_validation_implemented':True,'external_receipts':external}
 build=ROOT/'downloads/selected-source-invariants-repair-2/build/build.json'
 if build.is_file():
  b=json.loads(build.read_text());assert b['exit']==0 and b['inputs_unchanged']
  for name,digest in b['source_inputs_before'].items():assert sha((ROOT/name).read_bytes())==digest
  report['fresh_build']=b;report['fresh_build_raw']={name:embed((build.parent/name).read_bytes()) for name in ['stdout','stderr']}

 test=ROOT/'downloads/selected-source-invariants-repair-2/external-v2/result.json'
 controls=json.loads(test.read_text());assert controls['status']=='PASS' and controls['validator_sha256']==sha(pathlib.Path(__file__).with_name('external_receipts.py').read_bytes());assert controls['test_sha256']==sha(pathlib.Path(__file__).with_name('test_external_receipts.py').read_bytes()) and len(controls['negative_controls'])==17 and all(c['rejected'] for c in controls['negative_controls']);report['external_validator_controls']=controls;report['external_validator_source']=embed(pathlib.Path(__file__).with_name('external_receipts.py').read_bytes());report['external_validator_test_source']=embed(pathlib.Path(__file__).with_name('test_external_receipts.py').read_bytes())
 root=pathlib.Path('/home/isa/PocketLore-control/overnight-20261005/selected-source-kernel-probe-result-review-20261006T0509Z');manifest=json.loads((root/'manifest.json').read_text());report['old_probe_raw']={'manifest':embed((root/'manifest.json').read_bytes()),'files':{entry['path']:embed((root/entry['path']).read_bytes()) for entry in manifest['files']}}
 ART.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'FAIL','historical_audit':verification,'missing_scale_files':missing,'kernel':limits,'bus_exit':bus.returncode,'reason':'No qualifying external validation; no unchanged suite replay.'},indent=2));return 1
if __name__=='__main__':sys.exit(main())
