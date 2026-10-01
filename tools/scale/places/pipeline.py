"""Finite, resumable local build queue for exactly the pinned 16 official objects.
No supervisor state, GPU, emulator or per-record requests. One private writer lock.
"""
import fcntl,hashlib,json,os,pathlib,subprocess,sys,time
from common import atomic_json
ROOT=pathlib.Path('/home/isa/PocketLore-control/scale-workers/places');DATA=ROOT/'data';E=pathlib.Path('docs/evidence/scale/places')
lock=(ROOT/'places-build.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
objects=json.loads((E/'overture-objects.json').read_text());completed=[]
for i,obj in enumerate(objects):
 src=DATA/pathlib.Path(obj['Key']).name;dest=DATA/f'places-{i:02}.sqlite';receipt=src.with_suffix(src.suffix+'.receipt.json')
 while not receipt.exists():time.sleep(10)
 assert src.stat().st_size==int(obj['Size'])
 if not dest.exists():
  with (ROOT/f'build-{i:02}.log').open('a') as log:
   result=subprocess.run([sys.executable,'tools/scale/places/build.py',str(src),str(dest)],stdout=log,stderr=subprocess.STDOUT)
  if result.returncode:raise RuntimeError(f'Build {i} failed; raw log preserved; no unchanged retry')
 if not dest.with_suffix('.report.json').exists():
  from recover_report import recover
  recover(dest)
 report=json.loads(dest.with_suffix('.report.json').read_text());completed.append(report);atomic_json(E/f'places-{i:02}.report.json',report)
 total=sum(r['unique_ids'] for r in completed)
 state={'task':'global-places','status':'building' if i<15 else 'built_pending_global_dedup_and_evaluation','completed_shards':i+1,'pinned_shards':len(objects),'shard_unique_id_sum_not_global_unique':total,'bytes':sum(r['bytes'] for r in completed),'first_complete_shard_milestone':True,'first_million_shard_unique_ids':total>=1000000,'distribution_ready':False,'android_acceptance':False,'physical_acceptance':False,'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
 atomic_json(ROOT/'milestone.json',state);atomic_json(E/'milestone.json',state);atomic_json('LOOP_STATE.json',state)
 print(json.dumps(state),flush=True)
