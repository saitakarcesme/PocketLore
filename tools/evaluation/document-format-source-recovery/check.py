"""Pure read-only raw execution and current reproducible content validation."""
import zipfile,copy
from common import *
def refusal(encoded,expected_class=None):
 import base64,re
 try:value=json.loads(base64.b64decode(encoded,validate=True))
 except Exception:raise ValueError('refusal-json')
 need(isinstance(value,dict) and set(value)=={'schema','causes','termination'} and value['schema']=='actual-exception-v1','refusal-schema')
 chain=value['causes'];need(isinstance(chain,list) and 1<=len(chain)<=8,'refusal-chain')
 for item in chain:
  need(isinstance(item,dict) and set(item)=={'class','message'} and isinstance(item['class'],str) and re.fullmatch(r'[A-Za-z_$][A-Za-z0-9_.$]*',item['class']) is not None,'refusal-class')
  message=item['message'];need(message is None or isinstance(message,str) and len(message.encode('utf-16-le','surrogatepass'))//2<=4096,'refusal-message')
 need(value['termination'] in ['end','cycle','depth'] and (value['termination']!='depth' or len(chain)==8),'refusal-termination')
 if expected_class is not None:need(chain[0]['class']==expected_class,'refusal-class-binding')
 return value

def validate_output(raw,cases):
 import base64
 lines=raw.decode('utf-8').splitlines();pos=0
 for case in cases:
  row=lines[pos].split('\t');pos+=1;name=case['name'];need(row[1]==name,'case-order')
  if case['expected_text_sha256'] is None:
   need(row[0]=='REFUSE' and len(row)==5 and row[2],'expected-refusal');refusal(row[3],row[2])
  else:
   need(row[0]=='PASS' and row[2]==case['expected_text_sha256'] and int(row[3])==case['expected_utf16_length'] and int(row[4])>0,'exact-text')
   if case['independent_spans'] is not None:
    exact=lines[pos].split('\t');pos+=1;need(exact[:2]==['EXACT',name],'exact-row');text=base64.b64decode(exact[2]).decode('utf-8');spans=base64.b64decode(exact[3]).decode('utf-8');need(digest(text.encode())==case['expected_text_sha256'],'independent-text')
    expected=''.join(str(a)+'\t'+str(z)+'\t'+base64.b64encode(loc.encode()).decode()+'\n' for a,z,loc in case['independent_spans']);need(spans==expected and digest(spans.encode())==row[5],'independent-spans')
  timing=lines[pos].split('\t');pos+=1;need(timing[:2]==['TIME',name] and 0<int(timing[2])<=20_000_000_000,'case-time')
 need(lines[pos].startswith('PASS: six provider MIME matches/generic cases and six mismatches;') and lines[pos+1]=='COMPLETE\t'+str(len(cases))  ,'complete-policy')
 pos+=2
 central=read(BASE/'central-cases.json')['cases']
 for case in central:
  row=lines[pos].split('\t');pos+=1;need(len(row)==5 and row[:3]==['CENTRAL',case['name'],'PASS' if case['accept'] else 'REFUSE'] and 0<int(row[4])<20_000_000_000,'central-outcome')
  if case['accept']:need(row[3]==case['payload_sha256'],'central-byte-oracle')
  else:refusal(row[3])
 need(lines[pos]=='CENTRAL_COMPLETE\t'+str(len(central)) and pos+1==len(lines),'central-complete')

def refusal_controls(raw):
 import base64
 rows=[line.split('\t') for line in raw.decode().splitlines() if line.startswith('REFUSE\t')]
 need(bool(rows),'refusal-baseline');row=rows[0];positive=refusal(row[3],row[2]);out=[]
 for name,guard,mutate in [
  ('missing-message','refusal-class',lambda v:v['causes'][0].pop('message')),
  ('nonstring-message','refusal-message',lambda v:v['causes'][0].__setitem__('message',7)),
  ('wrong-class','refusal-class-binding',lambda v:v['causes'][0].__setitem__('class','java.lang.AssertionError')),
  ('empty-causes','refusal-chain',lambda v:v.__setitem__('causes',[])),
  ('unknown-termination','refusal-termination',lambda v:v.__setitem__('termination','invented'))]:
  refusal(row[3],row[2]);bad=copy.deepcopy(positive);mutate(bad)
  encoded=base64.b64encode(canonical(bad)).decode()
  try:refusal(encoded,row[2])
  except ValueError as e:need(str(e)==guard,'refusal-control-guard');out.append({'case':name,'guard':str(e)})
  else:raise ValueError('accepted-refusal-corruption')
 print(json.dumps({'actual_refusal_controls':out}))

def process_check(p):
 need(p['pid']==int(p['stat'].split()[0]),'process-pid');fields=dict(l.split(':',1) for l in p['status'].splitlines() if ':' in l);need(int(fields['Pid'])==p['pid'] and ticks(p)>0,'process-startticks');return fields

def validate_raw(r,before,request,inputs):
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
 need(content(actual['test_apk'])==content(expected['test_apk']),'test-apk-content')
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
 for name,key,guard in [('apk-bytes','apk','apk-content'),('test-apk','test_apk','test-apk-content'),('build-source','sources','build-source')]:
  bad=copy.deepcopy(captured)
  if key in ['apk','test_apk']:bad[key]['sha256']='0'*64
  else:bad[key]={}
  refuses(name,guard,build_positive,lambda:current_build(bad,captured))
 metadata=copy.deepcopy(captured);metadata['apk']['version']=[0,0,0,0,0];current_build(metadata,captured)
 for role in ['java','libjvm','cases_json','cases_tsv']:
  bad=copy.deepcopy(inputs);bad[role]['sha256']='0'*64
  # Both mutable request/receipt copies may agree; the independently committed compilation authority does not.
  refuses('rebound-'+role,'input-authority',lambda:input_contract(inputs,inputs),lambda:input_contract(bad,inputs))
 return outcomes

def main():
 packet=read(ROOT/'docs/evidence/document-format-source-recovery-review.json');commit=packet['source_commit'];src=frozen(commit)
 request=read(REQUEST,packet['request']);need(request['sources']==src and request['source_commit']==commit and digest(canonical(src))==request['roster_sha256'],'request-source')
 parent=read(RESULT,packet['parent_result']);need(parent['taskid']==TASK and parent['source_commit']==commit and parent['request_sha256']==packet['request']['sha256'] and parent['verdict']=='continue','parent-result')
 need(parent['properties']==PROPERTIES and parent['worker_argv']==request['worker_argv'],'parent-service-properties')
 build_inputs=json.loads(subprocess.check_output(['git','show',commit+':tools/evaluation/document-format-source-recovery/build-inputs-554.json'],cwd=ROOT))
 input_contract(request['inputs'],build_inputs['inputs'])
 need(build_inputs['exit_codes']==[0] and all(src[p]==d for p,d in build_inputs['compiled_sources'].items()),'compilation-provenance')
 for d in build_inputs['compile_logs'].values():need(identity(d['path'])==d,'compile-logs')
 for k,d in request['inputs'].items():need(identity(d['path'])==d,'immutable-'+k)
 need(set(packet['raw'])=={'before','result','stdout','stderr'},'raw-roster')
 for k,d in packet['raw'].items():need(d['path']==str(RUN/({'before':'before.json','result':'result.json'}.get(k,k))),'raw-path');need(identity(d['path'])==d,'raw-version')
 before=read(RUN/'before.json',packet['raw']['before']);r=read(RUN/'result.json',packet['raw']['result'])
 need(r['request_sha256']==packet['request']['sha256'] and before['request']==packet['request'],'raw-request')
 validate_raw(r,before,request,build_inputs['inputs'])
 need(r['stdout']==packet['raw']['stdout'] and r['stderr']==packet['raw']['stderr'],'raw-streams')
 _,stdout=identity(RUN/'stdout',True,262144);_,stderr=identity(RUN/'stderr',True,262144)
 validate_output(stdout,read(BASE/'cases.json')['cases']);need(stderr==b'','java-stderr')
 refusal_controls(stdout)
 need(r['elapsed']>=20,'actual-deadline-control')
 need(list((RUN/'staging').iterdir())==[],'staging-cleanup')
 captured=read(OUT/'android-build-final.json',packet['build_receipt']);need(captured['exit']==0 and captured['sources']==src,'build-execution')
 apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk';test=ROOT/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk'
 current_build({'apk':identity(apk),'test_apk':identity(test),'sources':src},captured)
 need(inventory()<8388608,'combined-storage')
 from accounting import verify_old_snapshot
 verify_old_snapshot()
 from accounting_controls import validate
 print(json.dumps({'accounting_controls':validate()}))
 outcomes=controls(r,before,request,build_inputs['inputs'],captured)
 print(json.dumps({'semantic_controls':outcomes,'metadata_only_current_build':'accepted without modifying raw capture'}))
 print('HOST_PRODUCTION_PARSER_PASS_ANDROID_WORKFLOWS_UNEXECUTED')
if __name__=='__main__':main()
