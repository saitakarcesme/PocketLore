"""Prebound serial probes with PID-starttime-owned termination and durable failure."""
import argparse,json,os,pathlib,signal,subprocess,time,uuid
from contract import ROOT,SOURCES,BINARIES,identity,source_manifest,source_contract,process_stat,version
BASE=ROOT/'downloads/native-cache-repair-2'
MODEL=pathlib.Path('/home/isa/PocketLore-control/overnight-20261005/strong-model-identity-research/weights-quarantine/Qwen3.6-35B-A3B-UD-Q2_K_XL.gguf')
def group_path():
 return pathlib.Path('/sys/fs/cgroup')/pathlib.Path('/proc/self/cgroup').read_text().split('0::')[1].strip().lstrip('/')
def kernel():
 p=group_path();d={n:(p/n).read_text() for n in ['memory.current','memory.peak','memory.max','memory.swap.max','memory.events','memory.stat','memory.swap.current','cpu.max','cpu.stat','pids.max','pids.current']};d['path']=str(p);st=p.stat();d['group_identity']={'path':str(p),'device':st.st_dev,'inode':st.st_ino,'raw_cgroup':pathlib.Path('/proc/self/cgroup').read_text()};d['observed_ns']=time.monotonic_ns();d['affinity_cpus']=sorted(os.sched_getaffinity(0));d['meminfo']=pathlib.Path('/proc/meminfo').read_text();return d
def preflight():
 d=kernel();assert int(next(l.split()[1] for l in d['meminfo'].splitlines() if l.startswith('MemAvailable:')))*1024>=11*1024**3
 assert int(d['memory.max'])<=9663676416 and int(d['memory.swap.max'])==0 and int(d['pids.max'])<=512
 q,p=map(int,d['cpu.max'].split());assert q>0 and q<=2*p
 assert int(d['memory.current'])<8053063680 and len(d['affinity_cpus'])<=4
 return d
def live(pid):
 p=pathlib.Path(f'/proc/{pid}');d={n:(p/n).read_text() for n in ['stat','status','smaps_rollup','cgroup']}
 d.update(pid=pid,monotonic_ns=time.monotonic_ns(),epoch=time.time(),namespaces={n:os.readlink(p/'ns'/n) for n in ['mnt','pid','user']})
 k=kernel();d['group_identity']=k['group_identity'];d['kernel_observed_ns']=k['observed_ns'];d.update({n:k[n] for n in ['memory.current','memory.peak','memory.events','memory.stat','memory.swap.current','cpu.stat','pids.current']});return d
def reap(proc,start,events,pidfd=None):
 # Popen retains ownership of this direct child, preventing PID reuse before wait.
 if proc.poll() is None:
  # A held pidfd, acquired before any reap, identifies the same kernel task
  # even when procfs is unavailable. Never make cleanup depend on another read.
  events.append({'action':'TERM','pid':proc.pid,'startticks':start,'monotonic_ns':time.monotonic_ns()});
  try:
   if pidfd is not None:signal.pidfd_send_signal(pidfd,signal.SIGTERM)
   else:proc.terminate()
  except ProcessLookupError:pass
  try:proc.wait(timeout=.5)
  except subprocess.TimeoutExpired:
   # Popen is the sole waiter; a direct child cannot reuse its PID before reap.
   events.append({'action':'KILL','pid':proc.pid,'startticks':start,'monotonic_ns':time.monotonic_ns()});
   try:
    if pidfd is not None:signal.pidfd_send_signal(pidfd,signal.SIGKILL)
    else:proc.kill()
   except ProcessLookupError:pass
   proc.wait(timeout=3)
 else:proc.wait(timeout=1)
 assert proc.poll() is not None
 events.append({'action':'REAPED','pid':proc.pid,'exit':proc.returncode,'monotonic_ns':time.monotonic_ns()})
def execute(argv,out,seconds=330,inject_read_error=False,inject_start_error=False,inject_after_error=False):
 out.mkdir(parents=True,exist_ok=False);report={'limits':{'wall_seconds':seconds,'log_bytes':4194304,'samples':1000,'sample_bytes':33554432},'argv':argv,'start_ns':time.monotonic_ns(),'samples':[],'cleanup':[]};proc=None;start=None;pidfd=None
 # The caller has frozen all source/derivation inputs. Bind the actual executable
 # independently here before spawn and retain its held stat/hash after all cleanup.
 executable=pathlib.Path(argv[0])
 try:
  report['kernel_before']=kernel()
  report['event_contract']='no-new-memory-failure-v1'
  report['executable_before']=identity(executable)
  with (out/'stdout.log').open('w') as log:
   proc=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT)
   # Kernel pidfd ownership remains valid even if initial procfs reads fail.
   pidfd=os.pidfd_open(proc.pid);report['pidfd_opened']=True;report['pidfd_fdinfo']=pathlib.Path(f'/proc/self/fdinfo/{pidfd}').read_text()
   if inject_start_error:raise OSError('Engineered initial stat failure')
   # proc cannot be reaped elsewhere: direct child and sole writer.
   start=process_stat(pathlib.Path(f'/proc/{proc.pid}/stat').read_text())[1];report.update(pid=proc.pid,startticks=start)
   while proc.poll() is None:
    try:s=live(proc.pid)
    except (FileNotFoundError,ProcessLookupError) as error:
     # procfs can vanish before waitpid reports an exiting direct child.
     # Preserve the failed read and require bounded confirmation of real exit.
     terminal={'error':repr(error),'pid':proc.pid,'startticks':start,'monotonic_ns':time.monotonic_ns()}
     report.setdefault('terminal_reads',[]).append(terminal)
     try:terminal['confirmed_exit']=proc.wait(timeout=.05)
     except subprocess.TimeoutExpired:raise error
     terminal['confirmed_ns']=time.monotonic_ns();break
    s['phase']='running'
    if executable.name=='native-cache-controls':
     prefix=pathlib.Path(argv[4]);s['phase']='hash-or-setup'
     if pathlib.Path(str(prefix)+'-resident.json').exists():s['phase']='resident-observation-present'
     if pathlib.Path(str(prefix)+'-released.json').exists():s['phase']='release-observation-present'
    if len(report['samples'])>=1000:raise RuntimeError('Sample count bound')
    if (out/'stdout.log').stat().st_size>4194304:raise RuntimeError('Combined stream bound')
    if sum(len(json.dumps(x)) for x in report['samples'])+len(json.dumps(s))>33554432:raise RuntimeError('Sample byte bound')
    if int(s['memory.swap.current'])!=0:raise RuntimeError('Swap stop')
    report['samples'].append(s)
    (out/'progress.json').write_text(json.dumps(report))
    if inject_read_error:raise OSError('Engineered observation read failure')
    if int(s['memory.current'])>=8053063680:raise RuntimeError('7.5GiB execution aggregate stop')
    if (time.monotonic_ns()-report['start_ns'])/1e9>seconds:raise TimeoutError('Owned child deadline')
    time.sleep(.05)
 except Exception as e:report['failure']=type(e).__name__+': '+str(e)
 finally:
  try:
   if proc is not None:
    reap(proc,start,report['cleanup'],pidfd);report['exit']=proc.returncode
    report['pid']=proc.pid
  except Exception as e:report['cleanup_failure']=repr(e)
  if pidfd is not None:os.close(pidfd)
  report['end_ns']=time.monotonic_ns()
  try:
   if inject_after_error:raise OSError('Engineered post-run identity read failure')
   report['executable_after']=identity(executable)
   if report['executable_before']!=report['executable_after']:report['failure']='Executable mutation'
  except Exception as e:report['post_identity_failure']=repr(e);report['failure']='Post-run identity unavailable'
  try:report['kernel_after']=kernel()
  except Exception as e:report['kernel_after_error']=repr(e)
  (out/'execution.json').write_text(json.dumps(report,indent=2))
 return report

def freeze():
 preflight();source=source_manifest();binary={p:identity(ROOT/p) for p in BINARIES}
 src=pathlib.Path((BASE/'source-path.txt').read_text().strip());manifest=identity(src.parent/'native-manifest.json',True)
 frozen={'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,timeout=10).strip(),'source':source,'binary':binary,'derivation':manifest,'source_path':str(src),'created_ns':time.monotonic_ns(),'kernel':kernel()}
 p=BASE/'frozen.json';assert not p.exists(),'Never replace a frozen candidate';p.write_text(json.dumps(frozen,indent=2));return frozen

def probe(kind):
 frozen=json.loads((BASE/'frozen.json').read_text());source_contract(frozen['source'])
 for p,v in frozen['binary'].items():assert identity(ROOT/p)==v,p
 assert identity(pathlib.Path(frozen['source_path']).parent/'native-manifest.json',True)==frozen['derivation']
 preflight();policy=json.loads((ROOT/'docs/evidence/native-cache-inputs/repair-2/policy.json').read_text())
 out=BASE/(kind+'-'+uuid.uuid4().hex[:8]);out.mkdir()
 if kind=='model':
  # One exclusive durable guard for this repair; failures cannot silently retry.
  fd=os.open(BASE/'model-attempt.json',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
  with os.fdopen(fd,'w') as f:json.dump({'run':str(out),'source':frozen['source'],'payload_charged':policy['charged_payload'],'full_hash_passes':1},f)
  path=MODEL;size=policy['model_bytes'];digest=policy['model_sha256'];offset=policy['offset']
 else:
  path=out/'fixture.bin';path.write_bytes(bytes(range(256))*16384);size=4194304;digest=identity(path)['sha256'];offset=0
 before=version(path);argv=[str(ROOT/BINARIES[0]),str(path),digest,str(size),str(out/'native'),str(offset)]
 r=execute(argv,out/'process');r['input_before']=before;r['input_after']=version(path if path.exists() else pathlib.Path(str(path)+'.retained-renamed'));r['input_identity_expected']={'sha256':digest,'size':size,'offset':offset}
 r['frozen']=frozen;r['post_source']=source_manifest();r['post_binary']={p:identity(ROOT/p) for p in BINARIES};r['kind']=kind;r['output']=str(out)
 r['raw']={p.name:p.read_text() for p in sorted(out.glob('native*')) if p.is_file()}
 r['stdout']=(out/'process/stdout.log').read_text();r['prebound_sources_unchanged']=r['post_source']==frozen['source'];r['prebound_binaries_unchanged']=r['post_binary']==frozen['binary']
 if kind=='model' and before!=r['input_after']:r['failure']='Model input version changed'
 (out/'receipt.json').write_text(json.dumps(r,indent=2));(BASE/(kind+'-receipt-path.txt')).write_text(str(out/'receipt.json'))
 print(str(out/'receipt.json'));return 1 if r.get('failure') or r.get('cleanup_failure') or r['exit'] or not r['prebound_sources_unchanged'] or not r['prebound_binaries_unchanged'] else 0
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('mode',choices=['freeze','fixture','model']);args=a.parse_args()
 if args.mode=='freeze':freeze()
 else:raise SystemExit(probe(args.mode))
