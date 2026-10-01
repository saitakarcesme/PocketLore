"""Build every pinned source into compact SQLite with two single-threaded workers."""
import concurrent.futures,json,pathlib,subprocess,sys,time,fcntl
import pyarrow.parquet as pq
from common import atomic_json
ROOT=pathlib.Path('/home/isa/PocketLore-control/scale-workers/places');D=ROOT/'data';E=pathlib.Path('docs/evidence/scale/places');objects=json.loads((E/'overture-objects.json').read_text())
lock=(ROOT/'places-build.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
def run(i):
 source=D/pathlib.Path(objects[i]['Key']).name;dest=D/f'compact-{i:02}.sqlite'
 while not source.with_suffix(source.suffix+'.receipt.json').exists():time.sleep(10)
 if not dest.exists():
  with (ROOT/f'compact-{i:02}.log').open('a') as log:r=subprocess.run([sys.executable,'tools/scale/places/compact.py',str(source),str(dest)],stdout=log,stderr=subprocess.STDOUT)
  if r.returncode:raise RuntimeError('Compact build failed; preserved, no automatic retry')
 report=json.loads(dest.with_suffix('.report.json').read_text());assert report['raw_records']==pq.ParquetFile(source).metadata.num_rows;assert report['eligible_records']+report['rejected']==report['raw_records'];assert pq.ParquetFile(dest.with_suffix('.keys.parquet')).metadata.num_rows==report['eligible_records'];atomic_json(E/f'compact-{i:02}.report.json',report);return report

completed={}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 futures={pool.submit(run,i):i for i in range(16)}
 for future in concurrent.futures.as_completed(futures):
  i=futures[future];completed[i]=future.result()
  state={'task':'global-places','format':2,'status':'building_lossless_blocks','completed_shards':sorted(completed),'eligible_source_records_not_global_unique':sum(r['eligible_records'] for r in completed.values()),'bytes':sum(r['bytes'] for r in completed.values()),'field_or_region_loss':False,'physical_acceptance':False,'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
  atomic_json(ROOT/'milestone.json',state);atomic_json(E/'milestone.json',state);atomic_json('LOOP_STATE.json',state);print(json.dumps(state),flush=True)
reports=[completed[i] for i in range(16)]
summary={'shards':16,'eligible_records':sum(r['eligible_records'] for r in reports),'bytes':sum(r['bytes'] for r in reports),'budget_bytes':4000000000,'within_provisional_budget':sum(r['bytes'] for r in reports)<=4000000000,'field_or_region_loss':False,'max_inflated_block_bytes':max(r['max_actual_inflated_block_bytes'] for r in reports),'max_worker_rss_KiB':max(r['max_rss_KiB'] for r in reports),'phone_acceptance':False};atomic_json(E/'compact-summary.json',summary);print(json.dumps(summary),flush=True)
