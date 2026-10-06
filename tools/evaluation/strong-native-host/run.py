"""One guarded serial scalar screen; durable failed cases, no automatic retry."""
import json,os,pathlib,resource,subprocess,time,sys,re
from support import R,O,MODEL,POLICY,BINARIES,identity,version,source_check,sources,owned,atomic,freeze,process_stat,collect_outputs
from preflight import capture

def restrict():
 resource.setrlimit(resource.RLIMIT_CPU,(150,160));resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_FSIZE,(4194304,4194304))
def run_case(i,frozen):
 out=O/f'case-{i}';out.mkdir(exist_ok=False)
 case={'number':i,'clock_ticks':os.sysconf('SC_CLK_TCK'),'samples':[],'cleanup':[],'start_ns':time.monotonic_ns(),'raw':{},'full_hash_policy':'One native File::open streaming verification before loader; no Python model hash'}
 atomic(out/'attempt.json',{'number':i,'start_ns':case['start_ns']})
 proc=None;pidfd=None;start=None
 try:
  case['preflight']=capture()
  source_check(frozen['source']);case['binary_before']=identity(R/BINARIES[1]);assert case['binary_before']==frozen['binary'][BINARIES[1]]
  case['model_before']=version(MODEL);assert case['model_before']['size']==12290628576
  case['prompt']=identity(R/f'docs/evidence/strong-native-host-fixtures/probe-{i}.txt',True)
  with MODEL.open('rb') as weights,(out/'stdout').open('wb') as stdout,(out/'stderr').open('wb') as stderr:
   case['parent_fd']={'fd':weights.fileno(),'stat':version('/proc/self/fd/'+str(weights.fileno()))}
   argv=[str(R/BINARIES[1]),'--exact-sparse-diagnostic',f'/proc/self/fd/{weights.fileno()}','96b9c0af5c77a4ecaabe3983175112b5ece763261c1ece12b2494b692a70dad7',str(R/f'docs/evidence/strong-native-host-fixtures/probe-{i}.txt')]
   case['argv']=argv;env=dict(os.environ,POCKETLORE_OBSERVATIONS=str(out))
   proc=subprocess.Popen(argv,stdout=stdout,stderr=stderr,pass_fds=(weights.fileno(),),env=env,preexec_fn=restrict)
   pidfd=os.pidfd_open(proc.pid);case['pidfd_fdinfo']=pathlib.Path(f'/proc/self/fdinfo/{pidfd}').read_text();case['pid']=proc.pid
   start=process_stat(pathlib.Path(f'/proc/{proc.pid}/stat').read_text())[1];case['startticks']=start
   phase='starting';last_phase=None;last_maps=0;sample_bytes=0
   while proc.poll() is None:
    now=time.monotonic_ns()
    if now-case['start_ns']>=180_000_000_000:raise TimeoutError('180-second case wall deadline')
    for n,cap in [('stdout',1048576),('stderr',4194304)]:
     if (out/n).stat().st_size>cap:raise RuntimeError('Bounded output limit')
    tail=(out/'stderr').read_bytes()[-65536:].decode(errors='replace');phases=re.findall(r'^POCKETLORE_PHASE (\S+)',tail,re.M)
    if phases:phase=phases[-1]
    try:
     s=owned.live(proc.pid);s['phase']=phase;s['limits']=pathlib.Path(f'/proc/{proc.pid}/limits').read_text()
     if phase!=last_phase or now-last_maps>1_000_000_000:
      s['smaps']=pathlib.Path(f'/proc/{proc.pid}/smaps').read_text();last_maps=now
     last_phase=phase
    except (FileNotFoundError,ProcessLookupError):
     if proc.poll() is not None:break
     raise
    sample_bytes+=len(json.dumps(s).encode());case['samples'].append(s)
    if sample_bytes>67108864 or len(case['samples'])>2048:raise RuntimeError('Bounded sample limit')
    if int(s['memory.current'])>=8053063680 or int(s['memory.swap.current']):raise RuntimeError('7.5GiB aggregate/swap stop')
    time.sleep(.1)
 except Exception as e:case['failure']=type(e).__name__+': '+str(e)
 finally:
  try:
   if proc is not None:owned.reap(proc,start,case['cleanup'],pidfd);case['exit']=proc.returncode
  except Exception as e:case['cleanup_failure']=repr(e)
  if pidfd is not None:os.close(pidfd)
  case['end_ns']=time.monotonic_ns()
  collect_outputs(out,case)
  try:
   case['binary_after']=identity(R/BINARIES[1]);case['post_source']=sources();case['kernel_after']=owned.kernel()
   if 'model_before' in case:case['model_after']=version(MODEL)
   if 'binary_before' in case:assert case['binary_before']==case['binary_after']
   if 'model_before' in case:assert case['model_before']==case['model_after']
   if frozen:assert case['post_source']==frozen['source']
  except Exception as e:case['post_identity_failure']=repr(e);case['failure']='Changed/unavailable final identities'
  atomic(out/'receipt.json',case)
 return case

def main():
 if len(sys.argv)>1 and sys.argv[1]=='freeze':freeze();return 0
 frozen=json.loads((O/'frozen.json').read_text());source_check(frozen['source'])
 # Atomic single ownership guard; no resumed/retried case in this task.
 with (O/'screen-attempt.json').open('x') as f:json.dump({'frozen':identity(O/'frozen.json'),'pid':os.getpid(),'time_ns':time.monotonic_ns()},f)
 report={'frozen':frozen,'cases':[],'not_run':[1,2],'errors':[],'android_execution':False,'product_qualified':False}
 try:
  from validate import validate_case
  for i in [1,2]:
   case=run_case(i,frozen);report['cases'].append(case);report['not_run'].remove(i)
   atomic(O/'screen.json',report)
   validate_case(case,frozen) # First failure stops the entire screen.
 except Exception as e:report['errors'].append(type(e).__name__+': '+str(e))
 finally:atomic(O/'screen.json',report)
 print(json.dumps({'cases':len(report['cases']),'not_run':report['not_run'],'errors':report['errors']}));return int(bool(report['errors']))
if __name__=='__main__':raise SystemExit(main())
