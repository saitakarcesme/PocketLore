import subprocess,time,json,pathlib,signal,hashlib
root=pathlib.Path('/home/isa/Projects/PocketLore'); dest=root/'downloads/complete-source-production-safety'/('actual-'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime()));dest.mkdir()
stage='/home/isa/PocketLore-control/overnight-20261005/source-original-staging/run-originals/original-records.sqlite'
base=['python3','tools/packs/complete-source/production.py','--mode','short','--stage',stage,'--ceiling','5999','--seconds','180','--cutoff','1791269964']
receipts=[]
def invoke(name,out,sig=None,resume=False):
 cmd=base+['--out',str(out)]+(['--resume'] if resume else []);start=time.time()
 with (dest/(name+'.log')).open('wb') as f:
  p=subprocess.Popen(cmd,cwd=root,stdout=f,stderr=subprocess.STDOUT)
  delivered=False;probed=False;samples=[]
  while p.poll() is None:
   if out.exists():
    files={}
    for x in out.iterdir():
     try:
      z=x.stat()
      if x.is_file():files[x.name]={'logical':z.st_size,'allocated':z.st_blocks*512}
     except FileNotFoundError:pass
    samples.append({'epoch':time.time(),'files':files})
   if resume and not probed and (out/'status.json').exists():
    current=json.loads((out/'status.json').read_text())
    if current.get('pid')==p.pid and current.get('status')=='RUNNING':
     denied=subprocess.run(cmd,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=5)
     (dest/'concurrent-resume.log').write_bytes(denied.stdout)
     (dest/'concurrent-resume.json').write_text(json.dumps({'command':cmd,'exit':denied.returncode,'error':denied.stdout.decode(),'owner_pid':p.pid,'owner_still_running':p.poll() is None},indent=2)+'\n')
     assert denied.returncode!=0 and b'already active' in denied.stdout and p.poll() is None
     probed=True
   if sig and not delivered:
    try:
     s=json.loads((out/'status.json').read_text())
     if s.get('committed_through',-1)>=63:
      p.send_signal(sig);delivered=True
    except (FileNotFoundError,json.JSONDecodeError):pass
   if time.time()-start>200:p.kill();raise RuntimeError('bounded controller timeout')
   time.sleep(.05)
  code=p.wait()
 (dest/(name+'-storage-samples.json')).write_text(json.dumps(samples)+'\n')
 receipt={'command':cmd,'pid':p.pid,'exit':code,'start':start,'end':time.time(),'signal':signal.Signals(sig).name if sig else None,'signal_delivered':delivered,'status':json.loads((out/'status.json').read_text()),'log_sha256':hashlib.sha256((dest/(name+'.log')).read_bytes()).hexdigest()}
 receipts.append(receipt);(dest/'invocations.json').write_text(json.dumps(receipts,indent=2)+'\n');print(name,code,receipt['status'].get('error',receipt['status']['status']),flush=True)
 return receipt
r=invoke('sigterm',dest/'resumed',signal.SIGTERM);assert r['exit']!=0 and r['signal_delivered']
r=invoke('manual-resume',dest/'resumed',resume=True);assert r['exit']==0
r=invoke('sigxcpu',dest/'sigxcpu',signal.SIGXCPU);assert r['exit']!=0 and r['signal_delivered']
print(dest,flush=True)
