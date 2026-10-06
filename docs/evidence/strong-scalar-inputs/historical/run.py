"""One serial exact-model screen, live kernel receipts, no automatic retries."""
import os,pathlib,json,hashlib,time,subprocess,selectors,signal,resource,sys,importlib.util
from preflight import capture,C
R=pathlib.Path(__file__).resolve().parents[3]
M=pathlib.Path('/home/isa/PocketLore-control/overnight-20261005/strong-model-identity-research/weights-quarantine/Qwen3.6-35B-A3B-UD-Q2_K_XL.gguf')
OUT=R/'downloads/strong-native-host'/('execution-'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime()));OUT.mkdir()
spec=importlib.util.spec_from_file_location('header',R/'tools/runtime/sparse/inspect_header.py');header=importlib.util.module_from_spec(spec);spec.loader.exec_module(header)
report={'preflight':capture(),'cases':[],'scope':'Host native engineering only; no Android/product/quality qualification','errors':[]}
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(4*1024*1024):h.update(b)
 return h.hexdigest()
def restrict():
 resource.setrlimit(resource.RLIMIT_CPU,(150,160));resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.setsid()
def snapshot(p,phase):
 d=pathlib.Path('/proc')/str(p.pid);before=(d/'stat').read_text();smaps=(d/'smaps').read_text();status=(d/'status').read_text();after=(d/'stat').read_text()
 return {'pid':p.pid,'phase':phase,'epoch':time.time(),'monotonic_ns':time.monotonic_ns(),'stat_before':before,'stat_after':after,'smaps':smaps,'status':status,'cgroup':(d/'cgroup').read_text(),'kernel':{n:(C/n).read_text() for n in ['memory.current','memory.peak','memory.events','memory.swap.current','cpu.stat']}}
try:
 report['header']=header.inspect(M);assert report['header']['metadata']['general.architecture']=='qwen35moe' and len(report['header']['tensors'])==733
 before=M.stat();assert before.st_size==12290628576
 started=time.time();sha=digest(M);after=M.stat();assert (before.st_ino,before.st_mtime_ns,before.st_size)==(after.st_ino,after.st_mtime_ns,after.st_size)
 assert sha=='96b9c0af5c77a4ecaabe3983175112b5ece763261c1ece12b2494b692a70dad7'
 report['model']={'path':str(M),'bytes':after.st_size,'sha256':sha,'inode':after.st_ino,'device':f'{os.major(after.st_dev):02x}:{os.minor(after.st_dev):02x}','mtime_ns':after.st_mtime_ns,'hash_started':started,'hash_ended':time.time()}
 # Release this diagnostic hash scan's clean cache; no file mutation, no system-wide cache operation.
 with M.open('rb') as f:os.posix_fadvise(f.fileno(),0,0,os.POSIX_FADV_DONTNEED)
 report['after_identity_preflight']=capture()
 binary=R/'downloads/strong-native-host/host-build/sparse-host';report['binary_sha256']=digest(binary)
 report['source_manifest']={str(p.relative_to(R)):digest(p) for folder in ('tools/runtime/sparse','tools/evaluation/strong-native-host') for p in sorted((R/folder).glob('*')) if p.is_file()}
 freeze=R/'docs/evidence/strong-native-host-fixtures/freeze.json';report['freeze_sha256']=digest(freeze)
 for i in (1,2):
  assert int((C/'memory.current').read_text())<7*1024**3,'Insufficient supervising memory headroom'
  prompt=R/f'docs/evidence/strong-native-host-fixtures/probe-{i}.txt';case={'prompt_sha256':digest(prompt),'started':time.time(),'samples':[],'stopped_reason':None};report['cases'].append(case)
  with M.open('rb') as weights:
   assert os.fstat(weights.fileno()).st_ino==after.st_ino
   argv=[str(binary),'--exact-sparse-diagnostic',f'/proc/self/fd/{weights.fileno()}',sha,str(prompt)];case['argv']=argv
   p=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,pass_fds=(weights.fileno(),),preexec_fn=restrict);case['pid']=p.pid;phase='starting';sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ,'stdout');sel.register(p.stderr,selectors.EVENT_READ,'stderr');streams={'stdout':bytearray(),'stderr':bytearray()};tick=0;term=None
   while p.poll() is None or sel.get_map():
    for key,_ in sel.select(.15):
     b=os.read(key.fileobj.fileno(),65536)
     if not b:sel.unregister(key.fileobj);continue
     streams[key.data].extend(b)
     if key.data=='stderr':
      lines=streams['stderr'].decode(errors='replace').splitlines();phases=[x.split(' ',1)[1] for x in lines if x.startswith('POCKETLORE_PHASE ')];phase=phases[-1] if phases else phase
    now=time.monotonic()
    if p.poll() is None and now-tick>=.4:
     try:
      s=snapshot(p,phase);case['samples'].append(s);current=int(s['kernel']['memory.current']);swap=int(s['kernel']['memory.swap.current'])
      if current>8053063680 or swap:case['stopped_reason']='Measured aggregate memory/swap stop'
     except FileNotFoundError:pass
     tick=now
    if time.time()-case['started']>180:case['stopped_reason']='Wall deadline'
    if case['stopped_reason'] and p.poll() is None:
     if term is None:os.killpg(p.pid,signal.SIGTERM);term=now
     elif now-term>2:os.killpg(p.pid,signal.SIGKILL)
   case.update(exit=p.wait(),ended=time.time(),stdout=streams['stdout'].decode(errors='replace'),stderr=streams['stderr'].decode(errors='replace'))
  if case['exit'] or case['stopped_reason']:raise RuntimeError('Stopped exact model route after first failed execution')
 assert (M.stat().st_ino,M.stat().st_mtime_ns,M.stat().st_size)==(after.st_ino,after.st_mtime_ns,after.st_size)
except Exception as e:report['errors'].append(type(e).__name__+': '+str(e))
finally:
 report['final_preflight']=capture();(OUT/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'path':str(OUT),'errors':report['errors'],'cases':[(c.get('exit'),c.get('stopped_reason')) for c in report['cases']]}));sys.exit(bool(report['errors']))
