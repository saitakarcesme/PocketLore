"""Bounded owned Python worker, no device, archive or model access."""
import json,os,pathlib,signal,subprocess,sys,time
import check
A=check.A

def ticks(pid):return pathlib.Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]
def run(argv,directory,seconds,cancel=lambda:False,inject=None):
 out=pathlib.Path(directory);out.mkdir(exist_ok=False);sources=check.freeze();receipt={'argv':argv,'sources_before':sources,'executable_before':{'sha256':A.filehash(sys.executable),'version':A.version(sys.executable)},'samples':[],'resource_samples':[A.sample('worker-before')],'error':None,'signals':[],'started_ns':time.monotonic_ns(),'timeout_seconds':seconds};p=None;fd=None;start=None;last=0
 def send(sig):
  if p.poll() is None:
   # Held pidfd identifies the owned process even if procfs becomes unreadable.
   if fd is not None:signal.pidfd_send_signal(fd,sig)
   else:p.send_signal(sig) # Popen is the sole waiter; an unreaped child PID cannot be reused.
   receipt['signals'].append({'signal':sig,'at_ns':time.monotonic_ns()})
 def collect():
  check.need(inject!='collection','injected-collection');root=pathlib.Path('/proc',str(p.pid));receipt['samples'].append({'pid':p.pid,'startticks':start,'at_ns':time.monotonic_ns(),'stat':(root/'stat').read_text(),'status':(root/'status').read_text(),'smaps_rollup':(root/'smaps_rollup').read_text(),'namespaces':{k:os.readlink(root/'ns'/k) for k in ['pid','mnt','user']},'supervisor':A.sample('worker-live')})
 try:
  with open(out/'stdout','xb') as stdout,open(out/'stderr','xb') as stderr:
   p=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr);receipt['pid']=p.pid;fd=os.pidfd_open(p.pid);receipt.update(pidfd_open=True,pidfd_info=pathlib.Path('/proc/self/fdinfo',str(fd)).read_text(),injection=inject);check.need(inject!='initial-stat','injected-initial-stat');raw_stat=pathlib.Path('/proc',str(p.pid),'stat').read_text();start=raw_stat.rsplit(')',1)[1].split()[19];receipt.update(startticks=start,initial_stat=raw_stat)
   while p.poll() is None:
    now=time.monotonic()
    check.need(not cancel(),'worker-cancelled')
    if now-last>=0.25:collect();last=now
    if time.monotonic_ns()-receipt['started_ns']>=seconds*10**9:raise TimeoutError('worker-deadline')
    # Reserve8MiB for bounded logs/review; count retained prior runs and journals.
    task_root=check.ROOT/'downloads/indexed-xml-542';total=sum(f.stat().st_size for f in task_root.rglob('*') if f.is_file());check.need(total<=120*1024**2,'task-storage-bound')
    check.need((out/'stdout').stat().st_size<=4*1024**2 and (out/'stderr').stat().st_size<=1024**2,'worker-log-bound');time.sleep(0.02)
 except BaseException as e:receipt['error']=type(e).__name__+': '+str(e)
 finally:
  if p is not None:
   try:
    if p.poll() is None:
     send(signal.SIGTERM)
     try:p.wait(timeout=1)
     except subprocess.TimeoutExpired:send(signal.SIGKILL);p.wait(timeout=2)
    receipt['exit']=p.wait(timeout=1);receipt['reaped']=p.poll() is not None;receipt['process_absent']=not pathlib.Path('/proc',str(p.pid)).exists()
   except Exception as e:receipt['cleanup_error']=str(e);receipt['reaped']=False
  if fd is not None:os.close(fd)
  receipt['ended_ns']=time.monotonic_ns();receipt['resource_samples'].append(A.sample('worker-after'));receipt['sources_after']=check.freeze();receipt['executable_after']={'sha256':A.filehash(sys.executable),'version':A.version(sys.executable)};receipt['streams']={n:{'bytes':(out/n).stat().st_size,'sha256':A.filehash(out/n)} for n in ['stdout','stderr'] if (out/n).exists()};A.atomic(out/'worker.json',receipt)
 return receipt

def build(source,out,cancel=lambda:False):
 r=run([sys.executable,str(check.ROOT/'tools/packs/current-xml/indexed.py'),'build',str(source),str(out)],str(out)+'-worker',185,cancel=cancel)
 check.need(r.get('exit')==0 and r['error'] is None and r['reaped'] and r['process_absent'],'worker-build');return json.loads((pathlib.Path(out)/'index-receipt.json').read_text())
