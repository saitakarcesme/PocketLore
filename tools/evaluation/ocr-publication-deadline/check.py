"""Pure read-only raw execution and current reproducible content validation."""
import zipfile,copy
from common import *
def expected_lines():
 cases=read(ROOT/'tools/evaluation/attachment-utf16/cases.json');lines=[]
 for _ in range(3):
  for c in cases['valid']:
   lines+=['REFUSE\tinvalid-after-'+c['name']+'\tjava.io.IOException','VALID\t'+c['name']+'\t'+','.join(map(str,c['units']))+'\t'+c['hex']]
  lines+=['REFUSE\t'+n+'\tjava.io.IOException' for n in cases['invalid']]
  lines+=['BOUNDARY\t65536\t65536']
  lines+=['REFUSE\t'+n+'\t'+('java.lang.IllegalStateException' if n=='pending-exception' else 'java.io.IOException') for n in ['oversize','missing-terminator','null-producer','cancel','pending-exception']]
 prefix=['positive-before-boundary','exact-boundary-refusal','negative-elapsed-refusal','wraparound-elapsed','cancel-before-start','interrupt-refusal','queue-consumes-budget','late-init','late-recognition','late-conversion','late-hash','late-ui','uncancelled-stale-owner','old-owner-new-owner','hash-positive','hash-mismatch','stream-cancel','stream-expiry','lock-expiry-and-release','lock-cancel','native-relative-nanoseconds','native-floor-milliseconds','native-expired','native-cancel','native-backward-clock','native-invalid-budget-0','native-invalid-budget--1','native-invalid-budget-30000000001','native-invalid-budget-9223372036854775807']
 return ['PASS '+n for n in prefix]+lines+['COMPLETE\t3','DEADLINE_COMPLETE 29']
def validate_output(stdout,stderr):
 need(stdout.decode('utf-8').splitlines()==expected_lines() and stderr==b'','deadline-output-oracle')

def process_check(p):
 need(p['pid']==int(p['stat'].split()[0]),'process-pid');fields=dict(l.split(':',1) for l in p['status'].splitlines() if ':' in l);need(int(fields['Pid'])==p['pid'] and ticks(p)>0,'process-startticks');return fields

def validate_raw(r,before,request,inputs):
 need(r['source_versions_before']==r['source_versions_after']==request['source_versions'],'raw-source-versions')
 need(r['source_commit']==request['source_commit'] and r['sources_before']==r['sources_after']==request['sources'],'raw-source')
 need(r['inputs_before']==r['inputs_after']==inputs,'raw-inputs')
 need(before['inputs']==inputs and before['sources']==request['sources'] and before['argv']==command(),'raw-before')
 need(r['exit']==0 and r['error'] is None and not r['secondary_errors'] and r['reaped'] and r['absent'] and 0<r['elapsed']<=60,'execution')
 for k in [r['kernel_before'],r['kernel_after']]:kernel_contract(k)
 first,last=r['kernel_before'],r['kernel_after'];need(first==before['kernel'] and first['path']==last['path'] and first['inode']==last['inode'],'kernel-identity')
 events=[]
 for k in [first,last]:
  e={a:int(b) for a,b in (l.split() for l in k['memory.events'].splitlines())};need(set(e)>={'max','oom','oom_kill'} and all(v>=0 for v in e.values()),'event-shape');events.append(e)
 need(set(events[0])==set(events[1]) and all(events[1][k]>=events[0][k] for k in events[0]),'event-monotonic')
 need(all(events[1][k]==events[0][k] for k in ['max','oom','oom_kill']),'event-failure')
 need(0<int(first['memory.peak'])<=int(last['memory.peak'])<=536870912,'whole-run-peak')
 owner=r['owner_before'];after=r['owner_after'];child=r['child']
 for p in [owner,after,child]:process_check(p)
 need(owner==before['owner'] and owner['pid']==after['pid'] and ticks(owner)==ticks(after),'owner-lifetime')
 need(owner['cgroup']==after['cgroup']==child['cgroup']==first['raw_cgroup'] and owner['namespace']==after['namespace']==child['namespace'],'namespace-cgroup')
 need(owner['affinity']==after['affinity']==child['affinity']==[0,1,2,3],'affinity')
 pidfd_owner(r['pidfd_info'],child['pid'])
 need(next(l for l in child['limits'].splitlines() if l.startswith('Max cpu time')).split()[-3:]==['20','25','seconds'],'child-cpu-limit')
 u=r['rusage'];need(0<=u['ru_utime']+u['ru_stime']<=25 and 0<u['ru_maxrss']*1024<=536870912,'child-rusage')

def current_build(actual,expected):
 # Captured inode/version stays in raw receipt; replacement build content must match.
 need(content(actual['apk'])==content(expected['apk']),'apk-content')
 need(set(actual['libraries'])=={'arm64-v8a','x86_64'} and actual['libraries']==expected['libraries'],'abi-content')
 need(actual['sources']==expected['sources'],'build-source')

def controls(r,before,request,inputs,captured):
 outcomes=[]
 def refuses(name,expected,positive,negative):
  positive()
  try:negative()
  except ValueError as e:
   need(str(e)==expected,'wrong-control-guard:'+name);outcomes.append({'case':name,'guard':str(e)})
  else:raise ValueError('accepted-corruption:'+name)
 baseline=lambda:validate_raw(r,before,request,inputs)
 for name,mutate,guard in [
  ('kernel-memory',lambda x:x['kernel_after'].__setitem__('memory.max','9663676416'),'kernel-memory.max'),
  ('pid-prefix',lambda x:x.__setitem__('pidfd_info','Pid:\t'+str(x['child']['pid'])+'0\n'),'pidfd-owner'),
  ('source',lambda x:x.__setitem__('sources_after',{}),'raw-source'),
  ('failed-exit',lambda x:x.__setitem__('exit',1),'execution')]:
  bad=copy.deepcopy(r);mutate(bad);refuses(name,guard,baseline,lambda:validate_raw(bad,before,request,inputs))
 build_positive=lambda:current_build(captured,captured)
 for name,key,guard in [('apk-bytes','apk','apk-content'),('abi','libraries','abi-content'),('build-source','sources','build-source')]:
  bad=copy.deepcopy(captured)
  if key=='apk':bad[key]['sha256']='0'*64
  else:bad[key]={}
  refuses(name,guard,build_positive,lambda:current_build(bad,captured))
 metadata=copy.deepcopy(captured);metadata['apk']['version']=[0,0,0,0,0];current_build(metadata,captured)
 for role in ['java','libjvm','library','class','cases_json','cases_tsv']:
  bad=copy.deepcopy(inputs);bad[role]['sha256']='0'*64
  # Both mutable request/receipt copies may agree; the independently committed compilation authority does not.
  refuses('rebound-'+role,'input-authority',lambda:input_contract(inputs,inputs),lambda:input_contract(bad,inputs))
 return outcomes

def accounting_contract():
 from accounting import scan_roots,MANDATORY_ROOTS
 detail=inventory_detail();need(detail['charged_bytes']<8388608,'combined-storage')
 for row in read(BASE/'accounting-baseline.json')['records']:
  b=subprocess.check_output(['git','show',row['commit']+':'+row['path']],cwd=ROOT);need(len(b)==row['bytes'] and digest(b)==row['sha256'],'old-source-authority')
 scan_roots(MANDATORY_ROOTS,MANDATORY_ROOTS)
 for roots in [MANDATORY_ROOTS[:-1],MANDATORY_ROOTS[:-1]+(pathlib.Path('/home/isa/PocketLore-control/continue-20261006/ocr-publication-deadline'),)]:
  scan_roots(MANDATORY_ROOTS,MANDATORY_ROOTS)
  try:scan_roots(roots,MANDATORY_ROOTS)
  except ValueError as e:need(str(e)=='mandatory-root-roster','accounting-negative')
  else:raise ValueError('accepted-accounting-root')
 owned=OUT/'accounting-controls';need((owned/'mandatory/sentinel').read_bytes()==b'authored sentinel\n','accounting-sentinel');need((owned/'mandatory/failed-review').read_bytes()==b'authored refusal\ngrowth\n','accounting-growth')
 need(sum(x['bytes'] for x in scan_roots((owned/'mandatory',),(owned/'mandatory',)).values())==42,'accounting-bytes')
 missing=(owned/'absent-required',)
 try:scan_roots(missing,missing)
 except ValueError as e:need(str(e)=='mandatory-root-missing','missing-root-guard')
 else:raise ValueError('accepted-missing-root')

def main():
 accounting_contract()
 packet=read(ROOT/'docs/evidence/ocr-publication-deadline-review.json');commit=packet['source_commit'];src=frozen(commit)
 request=read(REQUEST,packet['request']);need(request['sources']==src and request['source_commit']==commit and digest(canonical(src))==request['roster_sha256'],'request-source')
 parent=read(RESULT,packet['parent_result']);need(parent['taskid']==TASK and parent['source_commit']==commit and parent['request_sha256']==packet['request']['sha256'] and parent['verdict']=='continue','parent-result')
 need(parent['properties']==PROPERTIES and parent['worker_argv']==request['worker_argv'],'parent-service-properties')
 build_inputs=json.loads(subprocess.check_output(['git','show',commit+':tools/evaluation/ocr-publication-deadline/build-inputs.json'],cwd=ROOT))
 input_contract(request['inputs'],build_inputs['inputs'])
 need(build_inputs['exit_codes']==[0,0] and build_inputs['compiled_sources']=={p:src[p] for p in ['android/attachments-native/text_transport.h','android/attachments-native/ocr_deadline.h','android/app/src/main/java/org/pocketlore/app/OcrDeadline.java','tools/evaluation/attachment-utf16/bridge.cpp','tools/evaluation/attachment-utf16/Transport.java','tools/evaluation/ocr-publication-deadline/bridge.cpp','tools/evaluation/ocr-publication-deadline/DeadlineProbe.java']},'compilation-provenance')
 for d in build_inputs['compile_logs'].values():need(identity(d['path'])==d,'compile-logs')
 for k,d in request['inputs'].items():need(identity(d['path'])==d,'immutable-'+k)
 need(set(packet['raw'])=={'before','result','stdout','stderr'},'raw-roster')
 for k,d in packet['raw'].items():need(d['path']==str(RUN/({'before':'before.json','result':'result.json'}.get(k,k))),'raw-path');need(identity(d['path'])==d,'raw-version')
 before=read(RUN/'before.json',packet['raw']['before']);r=read(RUN/'result.json',packet['raw']['result'])
 need(r['request_sha256']==packet['request']['sha256'] and before['request']==packet['request'],'raw-request')
 validate_raw(r,before,request,build_inputs['inputs'])
 need(r['stdout']==packet['raw']['stdout'] and r['stderr']==packet['raw']['stderr'],'raw-streams')
 _,stdout=identity(RUN/'stdout',True,262144);_,stderr=identity(RUN/'stderr',True,262144)
 validate_output(stdout,stderr)
 for old,new in [(b'PASS exact-boundary-refusal',b'PASS expired-published'),(b'PASS uncancelled-stale-owner',b'PASS stale-published'),(b'DEADLINE_COMPLETE 29',b'DEADLINE_COMPLETE 28')]:
  validate_output(stdout,stderr);bad=stdout.replace(old,new);need(bad!=stdout,'output-mutation')
  try:validate_output(bad,stderr)
  except ValueError as error:need(str(error)=='deadline-output-oracle','output-negative-guard')
  else:raise ValueError('accepted-output-mutation')
 need(packet['build_receipt']==request['build_receipt'],'build-request-authority')
 captured=read(BUILD_RECEIPT,packet['build_receipt']);build_authority(identity(BUILD_RECEIPT),request['build_receipt'],captured,src)
 for name in ['path','source','hash','exit']:
  build_authority(identity(BUILD_RECEIPT),request['build_receipt'],captured,src)
  d=copy.deepcopy(request['build_receipt']);expected=copy.deepcopy(d);record=copy.deepcopy(captured)
  if name=='path':d['path']=expected['path']=str(OUT/'android-build-final.json');guard='build-receipt-path'
  elif name=='source':record['sources']={};guard='build-receipt-source'
  elif name=='hash':d['sha256']='0'*64;guard='build-receipt-descriptor'
  else:record['exit']=1;guard='build-receipt-exit'
  try:build_authority(d,expected,record,src)
  except ValueError as e:need(str(e)==guard,'build-negative-guard')
  else:raise ValueError('accepted-build-mutation')
 apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk';libs={}
 with zipfile.ZipFile(apk) as z:
  for abi,machine in [('arm64-v8a',183),('x86_64',62)]:
   data=z.read('lib/'+abi+'/libpocketlore_attachments.so');need(data[:4]==b'\x7fELF' and int.from_bytes(data[18:20],'little')==machine,'abi-machine');libs[abi]=digest(data)
 current_build({'apk':identity(apk),'libraries':libs,'sources':src},captured)
 need(inventory()<8388608,'combined-storage')
 outcomes=controls(r,before,request,build_inputs['inputs'],captured)
 print(json.dumps({'semantic_controls':outcomes,'metadata_only_current_build':'accepted without modifying raw capture'}))
 print('HOST_DEADLINE_HELPERS_PASS_ANDROID_RECOGNITION_UNEXECUTED')
if __name__=='__main__':main()
