"""547 reviewed compact evidence authority, storage and readonly replay."""
import sys,pathlib,os,json,subprocess,time,copy
ROOT=pathlib.Path(__file__).resolve().parents[3];BASE=pathlib.Path(__file__).parent
sys.path.insert(0,str(ROOT/'tools/evaluation/indexed-replay'))
import contract as R
import semantic as S
import controls as OLD_CONTROLS
RUN=ROOT/'downloads/indexed-semantic-547';LOGS=ROOT/'downloads/indexed-semantic-547-checks'
CAP=1048576;INITIAL='41ba1cceb2292442ab676094cbf5dba720b69d84307eef20acbaef2054e65abc'
need=R.need;sha=R.sha;canonical=R.canonical
ROSTER=['tools/evaluation/indexed-semantic-final/'+n for n in ['core.py','execute.py','check.py','finalize.py','guards.py','authorization.py','initial.json','pre-execution-controls.json','budget-revision.json']]+['tools/evaluation/indexed-replay/'+n for n in ['contract.py','semantic.py','controls.py','initial.json']]+S.RUNTIME+['tools/evaluation/indexed-xml/fixtures.py','tools/evaluation/check_indexed_semantic_final.sh','tools/android-build.sh','tools/release/finalize_apk.py']
def initial():
 p=BASE/'initial.json';return R.consume({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':INITIAL},True)
def files():
 out=[]
 for d in [BASE,RUN,LOGS,ROOT/'tools/evaluation/indexed-replay']:
  if d.exists():out += [p for p in d.rglob('*') if p.is_file()]
 out += [ROOT/p for p in S.RUNTIME[:2]+['tools/evaluation/check_indexed_semantic_final.sh','docs/evidence/indexed-semantic-final.md','docs/evidence/indexed-semantic-final-review.json','FINDINGS.md','docs/RELEASE_GAPS.md'] if (ROOT/p).is_file()]
 out += [pathlib.Path('/home/isa/PocketLore-control/runtime')/n for n in ['547-source-review-request.json','547-source-review-authorization.json'] if (pathlib.Path('/home/isa/PocketLore-control/runtime')/n).is_file()]
 review_root=pathlib.Path('/home/isa/PocketLore-control/continue-20261006/indexed-final-source-recovery')
 for folder in review_root.glob('547-source-clearance-*'):
  if folder.is_dir():out += [p for p in folder.rglob('*') if p.is_file()]
 return sorted(set(out))
def used():return sum(p.stat().st_size for p in files())
def reserve(n):
 need(used()+n<=CAP,'storage-reservation');i=initial();need(i['old544_bytes']+i['old545_bytes']+i['old546_bytes']+used()+n<=8388608,'combined-storage')
def write(p,b):
 reserve(len(b)*2+4096);p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.staging')
 with open(tmp,'xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 os.replace(tmp,p)
def save(p,x):write(p,canonical(x)+b'\n')
def freeze(commit):
 need(len(commit)==40,'source-commit');out={}
 for p in ROSTER:
  b=R.git_bytes(commit,p);r={'path':p,'bytes':len(b),'sha256':sha(b)};R.consume(r);out[p]=r['sha256']
 return out
def old_packet():return json.loads(R.git_bytes('e74b6c31d90d7a0bfa333e577337b34ecf81894f','docs/evidence/indexed-reference-replay-review.json'))
def old_worker(w,name):
 commit=old_packet()['source_commit'];expected={p:sha(R.git_bytes(commit,p)) for p in old_packet()['sources']}
 need(w['sources_before']==w['sources_after']==expected,'historical-worker-source');worker(w,name,historical=True)
def worker(w,name,historical=False):
 need(w['reaped'] and w['process_absent'] and not w.get('cleanup_error'),'worker-reap');need(w['ended_ns']>w['started_ns'],'worker-time');need(w['executable_before']==w['executable_after'],'worker-executable')
 st=dict(l.split(':',1) for l in w['initial_status'].splitlines() if ':' in l)
 need(w['pid']==int(st['Pid'])==int(w['initial_stat'].split(' (')[0]) and w['startticks']==w['initial_stat'].rsplit(')',1)[1].split()[19],'worker-identity');S.samples(w['resource_samples'])
 if not historical:
  exe=pathlib.Path(sys.executable).resolve();need(w['executable_before']=={'path':str(exe),'version':R.version(exe),'sha256':R.hash_file(exe)},'worker-executable-authority')
  need(set(w['initial_namespaces'])=={'mnt','pid','user'} and w['initial_namespaces']==w['resource_samples'][0]['namespaces'],'worker-namespace');need(w['initial_cgroup']==w['resource_samples'][0]['cgroup'],'worker-cgroup');need('Rss:' in w['initial_smaps_rollup'],'worker-smaps');need(w['ended_ns']-w['started_ns']<6*10**9,'worker-lifetime')
 if w['pidfd_open']:
  from guards import pidfd_identity
  pidfd_identity(w['pidfd_info'],w['pid'])
 need(set(w['streams'])=={'stdout','stderr'},'worker-stream-roster')
 for r in w['streams'].values():need(r['bytes']<=16384,'worker-log-bound');R.consume(r)
 for s in w.get('samples',[]):need(s['pid']==w['pid']==int(s['stat'].split(' (')[0]) and s['stat'].rsplit(')',1)[1].split()[19]==w['startticks'],'worker-live')
 if name=='positive':need(w['exit']==0 and w['error'] is None and w['pidfd_open'],'worker-positive')
 elif name=='pidfd':need(not w['pidfd_open'] and 'engineered-pidfd-open-failure' in w['error'] and w['signals']==['POPEN_TERM','POPEN_KILL'] and w['exit']==-9,'worker-pidfd-fallback')
 else:need(('worker-deadline' if name=='hung' else 'engineered-collection-error') in w['error'] and w['signals'],'worker-engineered-error')
def history():
 old=R.consume(R.old_ref(R.OLD/'execution.json'),True);expected=R.stable_historical(old['historical']);actual=S.historical();need(actual==expected,'historical-stable')
 p=old_packet()
 for n,d in p['workers'].items():old_worker(R.consume(d,True),n)
 S.functional(R.consume(R.old_ref(R.OLD/'functional.json'),True))
 # Reconstruct deep raw worker negatives against the genuine immutable positive.
 baseline=R.consume(p['workers']['positive'],True);guards=[]
 for key,value,guard in [('pid',baseline['pid']+1,'worker-identity'),('startticks','0','worker-identity'),('pidfd_info','Pid:\t1\n','pidfd-owner'),('reaped',False,'worker-reap'),('exit',17,'worker-positive')]:
  old_worker(baseline,'positive');changed=copy.deepcopy(baseline);changed[key]=value
  try:worker(changed,'positive',historical=True)
  except R.Refused as x:need(str(x)==guard,'historical-worker-mutation');guards.append({'field':key,'value':value,'guard':guard})
  else:raise R.Refused('historical-worker-mutant-accepted')
 return {'worker_mutations':guards,'functional_authority':R.old_ref(R.OLD/'functional.json'),'stable_sha256':sha(canonical(expected)),'raw_544_execution':R.old_ref(R.OLD/'execution.json'),'old545_packet_commit':'e74b6c31d90d7a0bfa333e577337b34ecf81894f','classification':'HISTORICAL_FAILED_TASKS_NOT_CURRENT_EXECUTION'}
def reference_controls():return OLD_CONTROLS.run()

def artifact(p):
 if p.is_symlink():
  s=p.lstat();b=os.readlink(p).encode();return {'kind':'owned-symlink-control','path':str(p.relative_to(ROOT)),'bytes':len(b),'sha256':sha(b),'target':os.readlink(p),'inode':s.st_ino,'ctime_ns':s.st_ctime_ns}
 return R.descriptor(p)
def verify_artifact(d):
 if d.get('kind')=='owned-symlink-control':
  p=ROOT/d['path'];need(p==RUN/'link-control' and p.is_symlink() and artifact(p)==d and d['target']=='race.json','symlink-control-identity')
  try:R.path(d['path'])
  except R.Refused as x:need(str(x)=='reference-symlink','symlink-control-guard')
  else:raise R.Refused('symlink-accepted')
 else:R.consume(d)
def additional_reference_controls(authority):
 from unittest.mock import patch
 R.consume(authority,True);out=[]
 for name in ['corrupt','deadline','oversized','traversal']:
  R.consume(authority,True);d=copy.deepcopy(authority)
  try:
   if name=='corrupt':d['sha256']='0'*64;R.consume(d,True)
   elif name=='oversized':d['bytes']=33554433;R.consume(d,True)
   elif name=='traversal':d['path']='../outside';R.consume(d,True)
   else:
    with patch.object(R.time,'monotonic',side_effect=[0,31]):R.consume(d,True)
  except R.Refused as x:out.append({'name':name,'guard':str(x)})
  else:raise R.Refused('reference-mutant-accepted')
 need([x['guard'] for x in out]==['reference-content','reference-deadline','reference-size','reference-path'],'additional-reference-guards');return out
