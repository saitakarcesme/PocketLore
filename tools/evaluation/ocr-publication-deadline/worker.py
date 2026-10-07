"""Parent-launch-only deadline helper worker. Never start this in the builder service."""
import argparse,time,resource,signal
from common import *
def limits():
 resource.setrlimit(resource.RLIMIT_CPU,(20,25));resource.setrlimit(resource.RLIMIT_FSIZE,(262144,262144));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
def main():
 start=time.monotonic()
 ap=argparse.ArgumentParser();ap.add_argument('--request',required=True);a=ap.parse_args();need(a.request==str(REQUEST),'request-path')
 req_desc,raw=identity(REQUEST,True);request=json.loads(raw);need(request['taskid']==TASK and request['unit']==UNIT and request['properties']==PROPERTIES,'request-settings')
 source_before=frozen(request['source_commit']);need(source_before==request['sources'] and digest(canonical(source_before))==request['roster_sha256'],'request-sources')
 compiled=json.loads(subprocess.check_output(['git','show',request['source_commit']+':tools/evaluation/ocr-publication-deadline/build-inputs.json'],cwd=ROOT));input_contract(request['inputs'],compiled['inputs'])
 build_desc,build_bytes=identity(BUILD_RECEIPT,True);build_authority(build_desc,request['build_receipt'],json.loads(build_bytes),source_before)
 versions_before=source_versions();need(versions_before==request['source_versions'],'source-version-authority')
 inputs={k:identity(v['path']) for k,v in request['inputs'].items()};input_contract(inputs,request['inputs'])
 initial=kernel();kernel_contract(initial);owner=process(os.getpid());need(owner['affinity']==[0,1,2,3],'worker-affinity');need(not RUN.exists(),'single-attempt');need(inventory()+2097152<8388608,'storage-before-run');RUN.mkdir(parents=True)
 p=None;fd=None;reaped=False;usage=None;exit_code=None;error=None;secondary=[];child=None;fdinfo=None;cleanup=[]
 save(RUN/'before.json',{'request':req_desc,'source_commit':request['source_commit'],'sources':source_before,'inputs':inputs,'kernel':initial,'owner':owner,'argv':command(),'monotonic':start})
 try:
  with open(RUN/'stdout','xb') as out,open(RUN/'stderr','xb') as err:
   p=subprocess.Popen(command(),stdout=out,stderr=err,preexec_fn=limits,cwd=RUN)
   child=process(p.pid);fd=os.pidfd_open(p.pid);fdinfo=pathlib.Path('/proc/self/fdinfo',str(fd)).read_text();pidfd_owner(fdinfo,p.pid)
   need(child['cgroup']==owner['cgroup'] and child['namespace']==owner['namespace'],'child-group')
   while True:
    pid,status,u= os.wait4(p.pid,os.WNOHANG)
    if pid:
     reaped=True;exit_code=os.waitstatus_to_exitcode(status);p.returncode=exit_code;usage={k:getattr(u,k) for k in ['ru_utime','ru_stime','ru_maxrss','ru_minflt','ru_majflt']};break
    need(time.monotonic()-start<40,'worker-wall');time.sleep(.01)
 except BaseException as e:error=repr(e)
 finally:
  if p is not None and not reaped:
   try:
    for sig,wait in [(signal.SIGTERM,1),(signal.SIGKILL,3)]:
     try:
      if fd is not None:signal.pidfd_send_signal(fd,sig)
      else:os.kill(p.pid,sig) # Exclusive wait4 owner; unreaped child cannot recycle its PID.
      cleanup.append(sig.name)
     except ProcessLookupError:pass
     end=time.monotonic()+wait
     while time.monotonic()<end:
      pid,status,u=os.wait4(p.pid,os.WNOHANG)
      if pid:
       reaped=True;exit_code=os.waitstatus_to_exitcode(status);p.returncode=exit_code;usage={k:getattr(u,k) for k in ['ru_utime','ru_stime','ru_maxrss','ru_minflt','ru_majflt']};break
      time.sleep(.01)
     if reaped:break
   except BaseException as e:secondary.append('cleanup:'+repr(e))
  if fd is not None:
   try:os.close(fd)
   except BaseException as e:secondary.append('pidfd-close:'+repr(e))
  def observe(fn):
   try:return fn()
   except BaseException as e:secondary.append('observation:'+repr(e));return None
  result={'request_sha256':req_desc['sha256'],'source_commit':request['source_commit'],'source_versions_before':versions_before,'source_versions_after':observe(source_versions),'sources_before':source_before,'sources_after':observe(sources),'inputs_before':inputs,'inputs_after':observe(lambda:{k:identity(v['path']) for k,v in inputs.items()}),'kernel_before':initial,'kernel_after':observe(kernel),'owner_before':owner,'owner_after':observe(lambda:process(os.getpid())),'child':child,'pidfd_info':fdinfo,'elapsed':time.monotonic()-start,'rusage':usage,'exit':exit_code,'error':error,'secondary_errors':secondary,'reaped':reaped,'absent':p is not None and not pathlib.Path('/proc',str(p.pid)).exists(),'cleanup':cleanup,'stdout':observe(lambda:identity(RUN/'stdout')),'stderr':observe(lambda:identity(RUN/'stderr'))}
  save(RUN/'result.json',result)
 need(error is None and not secondary and exit_code==0 and reaped,'worker-failed')
if __name__=='__main__':
 try:main()
 except BaseException as e:
  # Parent must persist original service stderr, including failures before output admission.
  import sys
  print(json.dumps({'taskid':TASK,'worker_error':repr(e),'pid':os.getpid(),'phase':'preflight-or-execution','monotonic':time.monotonic()}),file=sys.stderr,flush=True)
  raise
