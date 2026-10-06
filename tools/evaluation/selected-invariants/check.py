"""Freeze current raw host evidence; full gate fails on absent revised kernel/scale proof."""
import base64,copy,hashlib,json,pathlib,resource,subprocess,sys,time,uuid,zlib
ROOT=pathlib.Path(__file__).resolve().parents[3];BASE=ROOT/'downloads/selected-source-invariants';ART=ROOT/'docs/evidence/selected-source-invariants-review.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def embedded(path):
 b=path.read_bytes();return {'path':str(path),'bytes':len(b),'sha256':sha(b),'encoding':'zlib+base64','content':base64.b64encode(zlib.compress(b)).decode()}
def code_inputs():
 paths=list((ROOT/'tools/packs/selected-source').glob('*.py'))+list((ROOT/'tools/evaluation/selected-invariants').glob('*.py'))+[ROOT/'tools/packs/source-structure/produce.py',ROOT/'tools/packs/complete-source/production.py',ROOT/'tools/packs/complete-source/compact.py',ROOT/'tools/evaluation/source-structure/host/StructureParserProbe.java',ROOT/'android/app/src/main/java/org/pocketlore/app/SourceStructureParser.java',ROOT/'tools/evaluation/check_selected_source_invariants.sh']
 return {str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in paths}
def validate_raw(file):
 data=zlib.decompress(base64.b64decode(file['content']));assert sha(data)==file['sha256'] and len(data)==file['bytes'],'Corrupt embedded raw file'
def validate_execution(commands,source,expected_source):
 assert source==expected_source,'Stale executed source'
 assert [c['name'] for c in commands]==['revisions','structure_controls','lifecycle','duplicate_body'],'Missing or reordered actual phase'
 for c in commands:
  assert c['exit']==0 and c['end']>=c['start'],'Failed transport/phase'
  for stream in ('stdout','stderr'):
   raw=pathlib.Path(c[stream+'_path']).read_bytes()
   assert sha(raw)==c[stream+'_sha256'],'Changed raw command stream'
def rejected(fn):
 try:fn()
 except (AssertionError,FileNotFoundError):return True
 raise AssertionError('Negative evidence was accepted')
def main():
 run=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'-'+uuid.uuid4().hex[:8];out=BASE/run;out.mkdir(parents=True);code=code_inputs();packet={'run_id':run,'source':code,'status':'FAIL','host_controls_pass':False,'source_admission_established':False,'android_execution':False,'production_launch_qualified':False,'start':time.time(),'commands':[],'failures':[],'unmet_gates':[],'raw':[]}
 try:
  independent=ROOT/'docs/evidence/selected-source-invariants/independent-expectations.json'
  assert sha(independent.read_bytes())=='a543836fbf838ae8670e43deec538fa9d211e43e4bf1ded9d026a75eda9a8489','Frozen independent expectations changed'
  for name,arguments in [('revisions',[]),('structure_controls',[str(out/'structure')]),('lifecycle',[str(out/'lifecycle')]),('duplicate_body',[str(out/'duplicate')])]:
   cmd=['python3',str(pathlib.Path(__file__).with_name(name+'.py'))]+arguments;start=time.time();result=subprocess.run(cmd,cwd=ROOT,capture_output=True,timeout=180);(out/(name+'.stdout')).write_bytes(result.stdout);(out/(name+'.stderr')).write_bytes(result.stderr);record={'name':name,'argv':cmd,'start':start,'end':time.time(),'exit':result.returncode,'stdout_path':str(out/(name+'.stdout')),'stderr_path':str(out/(name+'.stderr')),'stdout_sha256':sha(result.stdout),'stderr_sha256':sha(result.stderr)};packet['commands'].append(record);assert result.returncode==0,name+' failed'
  assert code_inputs()==code,'Executed code changed during check'
  build_path=BASE/'build-final/build.json';build=json.loads(build_path.read_text());assert build['exit']==0 and build['inputs_unchanged']
  for p,digest in build['source_inputs_before'].items():assert sha((ROOT/p).read_bytes())==digest,'Stale build source '+p
  assert sha((ROOT/'android/app/build/outputs/apk/debug/app-debug.apk').read_bytes())==build['apk_sha256'],'Stale APK'
  packet['build']=build
  structure=json.loads((out/'structure/result.json').read_text());assert structure['pass'] and structure['actual_java_parser_sources']==7 and not structure['android_execution'];packet['current_structure']=structure
  files={p.name:{'logical_bytes':p.stat().st_size,'allocated_bytes':p.stat().st_blocks*512,'sha256':sha(p.read_bytes())} for p in (out/'structure/candidate').iterdir() if p.is_file()};packet['current_fixture_final_files']=files;packet['current_fixture_final_total_bytes']=sum(x['logical_bytes'] for x in files.values())
  for name in ('lifecycle','duplicate'):
   result=json.loads((out/name/'result.json').read_text());assert result['pass'] and result['producer_sha256']==code['tools/packs/selected-source/producer.py']
  assert structure['producer_sha256']==code['tools/packs/selected-source/producer.py']
  # Machine-readable negative controls alter actual evidence and must reject.
  marker=embedded(out/'structure/result.json');validate_raw(marker);bad=copy.deepcopy(marker);bad['sha256']='0'*64
  validate_execution(packet['commands'],code,code_inputs())
  changed_source=dict(code);changed_source['tools/packs/selected-source/producer.py']='0'*64
  corrupt_commands=copy.deepcopy(packet['commands']);corrupt_commands[0]['stdout_sha256']='0'*64
  failed_commands=copy.deepcopy(packet['commands']);failed_commands[0]['exit']=1
  packet['artifact_negative_controls']={
   'corrupted_embedded_hash_rejected':rejected(lambda:validate_raw(bad)),
   'missing_required_phase_rejected':rejected(lambda:validate_execution(packet['commands'][:-1],code,code)),
   'stale_source_rejected':rejected(lambda:validate_execution(packet['commands'],changed_source,code)),
   'changed_raw_stream_rejected':rejected(lambda:validate_execution(corrupt_commands,code,code)),
   'failed_transport_rejected':rejected(lambda:validate_execution(failed_commands,code,code))}
  packet['host_controls_pass']=True
  # Do not transfer old shared-cgroup 6k/12k or different-code tiny-kernel evidence.
  packet['unmet_gates']=['No current-source 6000/12000 complete candidate runs under independently captured dedicated 512MiB/swap0/CPU400/Tasks32 kernel limits.','Current user bus is unavailable; shared runner kernel limits are unlimited. No revised scale job was launched.','No independent rights/support review establishing eligible contexts or full originals. Structural reconstruction alone is insufficient.','No qualified Android v3 reader/import/export/restart execution; existing v1 adapter is host preparation.','Full source/whole archive/latest readiness and 1.25M floor/2–3M target, whole 45GB/50GB installed-update and 12GB device profile remain open.']
 except BaseException as e:packet['failures'].append(type(e).__name__+': '+str(e))
 finally:
  packet['end']=time.time();packet['auditor_maxrss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
  # Every current command stream plus previous failed/passing bounded attempt is inspectable in the declared artifact.
  candidates=list(BASE.rglob('*.json'))+list(BASE.rglob('*.stdout'))+list(BASE.rglob('*.stderr'))+list(BASE.glob('*.log'))+list(BASE.glob('*.json'))
  candidates += [ROOT/p for p in code]+list((ROOT/'docs/evidence/selected-source-invariants').glob('*'))+[ROOT/'docs/evidence/selected-source-invariants-launch.json']
  overnight=pathlib.Path('/home/isa/PocketLore-control/overnight-20261005');pins=json.loads((ROOT/'docs/evidence/selected-source-invariants/input-pins.json').read_text())
  for folder,digest in pins.items():
   mf=overnight/folder/'manifest.json';assert sha(mf.read_bytes())==digest
   for name in ['manifest.json','review.json','expected-invariants.json','oracles.json','independent-expectations.json','sample-policy.json','policy.json']:
    p=overnight/folder/name
    if p.is_file():candidates.append(p)
  for directory,seqs in [('source-reader-prerequisite-review-20261006T0323Z',[2956,30000,100000,200000]),('source-reader-genuine-extended-review-20261006T0403Z',[1263712,342233,5010470])]:
   candidates += [overnight/directory/f'original-{seq}.json' for seq in seqs]
  candidates += [overnight/'source-full-readiness-contract.json']
  seen=set()
  for path in candidates:
   if path.is_file() and path not in seen and path.stat().st_size<=4*1024**2:
    # Do not capture this invocation's still-open outer console stream.
    seen.add(path);packet['raw'].append(embedded(path))
  for raw in packet['raw']:validate_raw(raw)
  packet['raw_count']=len(packet['raw']);rendered=json.dumps(packet,indent=2)+'\n';assert len(rendered.encode())<32*1024**2,'Review artifact exceeds bound';ART.write_text(rendered)
  (out/'check-outcome.json').write_text(json.dumps({'exit':1,'packet_sha256':sha(rendered.encode()),'host_controls_pass':packet['host_controls_pass'],'unmet_gates':packet['unmet_gates'],'failures':packet['failures']},indent=2))
 print(json.dumps({'status':packet['status'],'host_controls_pass':packet['host_controls_pass'],'failures':packet['failures'],'unmet_gates':packet['unmet_gates'],'packet':str(ART)},indent=2));return 1
if __name__=='__main__':sys.exit(main())
