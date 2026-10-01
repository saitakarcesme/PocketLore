"""One coordinator/writer lock, at most two single-threaded shard build workers."""
import concurrent.futures,fcntl,json,os,pathlib,subprocess,sys,time
from common import atomic_json
ROOT=pathlib.Path('/home/isa/PocketLore-control/scale-workers/places');DATA=ROOT/'data';E=pathlib.Path('docs/evidence/scale/places')
lock=(ROOT/'places-build.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
objects=json.loads((E/'overture-objects.json').read_text());complete={};pending={}
def run(i):
 obj=objects[i];src=DATA/pathlib.Path(obj['Key']).name;dest=DATA/f'places-{i:02}.sqlite'
 if not dest.exists():
  with (ROOT/f'build-{i:02}.log').open('a') as log:
   result=subprocess.run([sys.executable,'tools/scale/places/build.py',str(src),str(dest)],stdout=log,stderr=subprocess.STDOUT)
  if result.returncode:raise RuntimeError(f'Shard {i} failed; no unchanged retry')
 if not dest.with_suffix('.report.json').exists():
  from recover_report import recover
  return recover(dest)
 return json.loads(dest.with_suffix('.report.json').read_text())
def checkpoint():
 state={'task':'global-places','status':'building' if len(complete)<16 else 'built_pending_global_dedup_and_evaluation','completed_shards':sorted(complete),'pinned_shards':16,'shard_unique_id_sum_not_global_unique':sum(r['unique_ids'] for r in complete.values()),'bytes':sum(r['bytes'] for r in complete.values()),'first_complete_shard_milestone':bool(complete),'distribution_ready':False,'android_acceptance':False,'physical_acceptance':False,'build_workers':2,'duckdb_threads_per_worker':1,'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
 atomic_json(ROOT/'milestone.json',state);atomic_json(E/'milestone.json',state);atomic_json('LOOP_STATE.json',state);print(json.dumps(state),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 while len(complete)<len(objects):
  for future,i in list(pending.items()):
   if future.done():
    report=future.result();complete[i]=report;atomic_json(E/f'places-{i:02}.report.json',report);del pending[future];checkpoint()
  for i,obj in enumerate(objects):
   if len(pending)==2:break
   if i in complete or i in pending.values():continue
   src=DATA/pathlib.Path(obj['Key']).name
   if src.with_suffix(src.suffix+'.receipt.json').exists():pending[pool.submit(run,i)]=i
  if len(complete)<len(objects):time.sleep(5)
