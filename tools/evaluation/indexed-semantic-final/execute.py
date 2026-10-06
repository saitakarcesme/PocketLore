"""One source-frozen compact delta, with no archive or model operations."""
import sys,os,pathlib,subprocess,signal,time,copy,json
import core as C
import guards,authorization
R=C.R;S=C.S

def child(name,source):
 out=C.RUN/name;out.mkdir();p=None;fd=None
 exe=pathlib.Path(sys.executable).resolve();identity={'path':str(exe),'version':R.version(exe),'sha256':R.hash_file(exe)}
 w={'sources_before':source,'executable_before':identity,'resource_samples':[S.A.sample('before')],'started_ns':time.monotonic_ns(),'signals':[],'samples':[],'error':None}
 try:
  with open(out/'stdout','xb') as stdout,open(out/'stderr','xb') as stderr:
   code='import time;print("owned positive",flush=True);time.sleep(.1)' if name=='positive' else 'import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);print("ready",flush=True);time.sleep(10)'
   p=subprocess.Popen([str(exe),'-c',code],stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr);proc=pathlib.Path('/proc')/str(p.pid);raw=(proc/'stat').read_text();w.update(pid=p.pid,pidfd_open=False,initial_stat=raw,initial_status=(proc/'status').read_text(),startticks=raw.rsplit(')',1)[1].split()[19])
   w.update(initial_namespaces={n:os.readlink(proc/'ns'/n) for n in ['mnt','pid','user']},initial_cgroup=(proc/'cgroup').read_text(),initial_smaps_rollup=(proc/'smaps_rollup').read_text())
   if name=='pidfd':
    end=time.monotonic()+1
    while (out/'stdout').stat().st_size==0 and time.monotonic()<end:time.sleep(.01)
    raise OSError('engineered-pidfd-open-failure')
   fd=os.pidfd_open(p.pid);w.update(pidfd_open=True,pidfd_info=pathlib.Path('/proc/self/fdinfo',str(fd)).read_text());p.wait(timeout=3)
 except BaseException as e:w['error']=type(e).__name__+': '+str(e)
 finally:
  if p is not None:
   try:
    if p.poll() is None:
     (signal.pidfd_send_signal(fd,signal.SIGTERM) if fd is not None else p.terminate());w['signals'].append('PIDFD_TERM' if fd is not None else 'POPEN_TERM')
     try:p.wait(timeout=.3)
     except subprocess.TimeoutExpired:(signal.pidfd_send_signal(fd,signal.SIGKILL) if fd is not None else p.kill());w['signals'].append('PIDFD_KILL' if fd is not None else 'POPEN_KILL');p.wait(timeout=2)
    w.update(exit=p.wait(timeout=1),reaped=True,process_absent=not pathlib.Path('/proc',str(p.pid)).exists())
   except BaseException as e:w['cleanup_error']=type(e).__name__+': '+str(e)
  if fd is not None:os.close(fd)
  w.update(ended_ns=time.monotonic_ns(),executable_after={'path':str(exe),'version':R.version(exe),'sha256':R.hash_file(exe)},streams={n:R.descriptor(out/n) for n in ['stdout','stderr']});w['resource_samples'].append(S.A.sample('after'));w['sources_after']=C.freeze(SOURCE_COMMIT);C.save(out/'receipt.json',w)
 C.worker(w,name);return R.descriptor(out/'receipt.json')

def capture(commit):
 global SOURCE_COMMIT
 SOURCE_COMMIT=commit;source=C.freeze(commit);permission=authorization.verify(commit);C.reserve(200000);C.RUN.mkdir(exist_ok=False)
 C.save(C.RUN/'attempt.json',{'source_commit':commit,'sources':source,'session':os.environ.get('CODEX_THREAD_ID','unavailable'),'planned_reserved_bytes':200000})
 e={'source_commit':commit,'sources_before':source,'samples':[S.A.sample('before')],'status':'FAILED','errors':[],'authorization':permission}
 try:
  C.need(int(next(l.split()[1] for l in open('/proc/meminfo') if l.startswith('MemAvailable:')))*1024>=11*1024**3,'available-memory')
  e['historical']=C.history();e['semantic_controls']=guards.controls();e['descriptor_controls']=C.reference_controls()
  reference=R.manifest()['references']['authored'];_,ctx=R.consume(reference,True,observe=True);R.validate_context(ctx,reference);bad=copy.deepcopy(ctx);old=bad['version']['inode'];bad['version']['inode']+=1;bad['fdinfo']=bad['fdinfo'].replace('ino:\t'+str(old),'ino:\t'+str(old+1))
  try:R.validate_context(bad,reference)
  except R.Refused as x:e['context_guard']=str(x)
  else:raise R.Refused('context-mutant-accepted')
  e['extra_reference_controls']=C.additional_reference_controls(reference)
  e['context']={'reference':reference,'raw':ctx,'mutation':{'inode_delta':1}};C.need(e['context_guard']=='context-authority-version','context-guard')
  a=C.RUN/'race.json';b=C.RUN/'replacement.json';C.save(a,{'original':True});C.save(b,{'replacement':True});d=R.descriptor(a);R.consume(d,True)
  try:R.consume(d,True,between=lambda:os.replace(b,a))
  except R.Refused as x:e['race_guard']=str(x)
  else:raise R.Refused('race-accepted')
  C.need(e['race_guard']=='reference-replaced','race-guard');e['race_authority']=d;os.symlink('race.json',C.RUN/'link-control');C.verify_artifact(C.artifact(C.RUN/'link-control'))
  f=R.consume(R.old_ref(R.OLD/'functional.json'),True);r=S.I.Reader(R.OLD/'functional/current');e['queries']=[]
  try:
   r.admit(R.OLD/'functional/original',f['source_sha256'],f['index_sha256'])
   for q in R.POLICY['queries']:
    result=r.search(q);S.V.validate_hits(S.A,result['hits'],S.F.oracle_rows(8),q);e['queries'].append({'query':q,'hits':result['hits']})
   result=r.search('Common',limit=1);hits=list(result['hits'])
   while result['cursor']:result=r.search('Common',limit=1,cursor=result['cursor']);hits+=result['hits']
   S.V.validate_hits(S.A,hits,S.F.oracle_rows(8),'Common');e['pagination']=hits;e['export']=r.export(hits[0]['id'],C.RUN/'export');guards.export_identity(R.consume(R.descriptor(C.RUN/'export/original.wikitext')),R.consume(R.descriptor(C.RUN/'export/metadata.json'),True),e['export'],hits[0])
   e['refusals']={}
   for kind,q in [('short','a'),('cancel','Common')]:
    if kind=='cancel':r.cancel=lambda:True
    try:r.search(q)
    except S.A.Refused as x:e['refusals'][kind]=str(x)
    else:raise R.Refused('query-refusal-missing')
  finally:r.close()
  e['workers']={name:child(name,source) for name in ['positive','pidfd']}
  try:C.reserve(C.CAP)
  except R.Refused as x:e['storage_guard']=str(x)
  else:raise R.Refused('overflow-accepted')
  e['status']='PASS'
 except BaseException as x:e['errors'].append(type(x).__name__+': '+str(x));raise
 finally:
  e['sources_after']=C.freeze(commit);e['samples'].append(S.A.sample('after'));C.save(C.RUN/'delta.json',e)
if __name__=='__main__':capture(sys.argv[1])
