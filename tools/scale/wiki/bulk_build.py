#!/usr/bin/env python3
"""Bounded finite bulk dispatch, durable receipts and idempotent completed shards."""
import argparse,concurrent.futures,datetime,fcntl,json,pathlib,shutil,sqlite3,subprocess,sys,time
from acquire import atomic,digest
p=argparse.ArgumentParser();p.add_argument('lane');p.add_argument('--priority',required=True);p.add_argument('--edition',default='edition-v2');p.add_argument('--workers',type=int,choices=[1,2],default=1);p.add_argument('--start',type=int,default=0);p.add_argument('--end',type=int,default=15);p.add_argument('--supplement',choices=['screened','fragments','lean'],default='screened');p.add_argument('--format',choices=['v2','v3'],default='v2');p.add_argument('--index-policy',choices=['verbatim','reader_stopwords_v1'],default='verbatim');p.add_argument('--compression-level',type=int,default=3);a=p.parse_args();lane=pathlib.Path(a.lane);edition=lane/a.edition;edition.mkdir(exist_ok=True);inventory=json.loads(pathlib.Path('docs/evidence/scale/wiki/english-inventory.json').read_text());dispatch_lock=(edition/'dispatch.lock').open('w');fcntl.flock(dispatch_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
def immutable_copy(source,target):
 if target.exists():
  if digest(source)!=digest(target):raise RuntimeError('Edition notice/license differs; preserve completed cache and choose a new edition')
 else:shutil.copyfile(source,target)
immutable_copy(pathlib.Path('tools/scale/wiki/NOTICE.txt'),edition/'NOTICE.txt')
for license_file in pathlib.Path('tools/scale/wiki').glob('CC*.txt'):immutable_copy(license_file,edition/license_file.name)
priority_hash=digest(a.priority);dispatch_commit=subprocess.check_output(['tools/scale/wiki/git.sh','rev-parse','HEAD'],text=True).strip();driver_hash=digest(__file__)
items=inventory['files'][a.start:a.end]
def build(item):
 name=pathlib.Path(item['path']).name;out=edition/name.removesuffix('.parquet');result=out/'measurement.json'
 if result.exists():
  m=json.loads(result.read_text())
  if m['source_sha256']!=item['lfs']['oid'] or not m['source_complete']:raise RuntimeError('Completed source identity mismatch')
  with sqlite3.connect(f'file:{out / "catalog.sqlite"}?mode=ro',uri=True) as db:cfg=json.loads(db.execute("SELECT value FROM checkpoints WHERE key='config'").fetchone()[0])
  if cfg['priority_sha256']!=priority_hash or cfg['schema']!=(3 if a.format=='v3' else 1) or cfg.get('compression_level')!=a.compression_level or cfg.get('supplement')!=a.supplement or cfg.get('index_policy','verbatim')!=a.index_policy:raise RuntimeError('Completed build configuration mismatch')
  return m
 log=lane/'receipts'/(a.edition+'-'+name+f'-{time.time_ns()}.log');started=datetime.datetime.now(datetime.timezone.utc).isoformat();begin=time.monotonic()
 cmd=[sys.executable,'tools/scale/wiki/build_v3.py' if a.format=='v3' else 'tools/scale/wiki/build.py','--source',str(lane/'bulk'/name),'--out',str(out),'--sha256',item['lfs']['oid'],'--mode','tiered','--priority',a.priority,'--priority-sha',priority_hash,'--supplement',a.supplement,'--compression-level',str(a.compression_level)]
 if a.format=='v3':cmd.extend(['--index-policy',a.index_policy])
 with log.open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 receipt={'repo_commit_at_dispatch':dispatch_commit,'driver_sha256':driver_hash,'command':cmd,'started_utc':started,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'wall_seconds':time.monotonic()-begin,'exit_code':r.returncode,'log':str(log)};atomic(log.with_suffix('.execution.json'),receipt)
 if r.returncode:raise RuntimeError(f'Shard failed without automatic retry: {name}; preserved {log}')
 return json.loads(result.read_text())
with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
 for result in pool.map(build,items):print(json.dumps(result),flush=True)
complete=sorted(edition.glob('*/measurement.json'));measurements=[json.loads(x.read_text()) for x in complete]
summary={'edition':a.edition,'source_revision':inventory['revision'],'priority_sha256':priority_hash,'shards_complete':len(complete),'source_rows':sum(m['source_rows'] for m in measurements),'full':sum(m['counts'].get('full',0) for m in measurements),'lead':sum(m['counts'].get('lead',0) for m in measurements),'excluded_rows':sum(m['counts'].get('excluded',0) for m in measurements),'pack_bytes_before_aliases':sum(m['installed_bytes'] for m in measurements)+(edition/'NOTICE.txt').stat().st_size,'installed_budget_bytes':22000000000,'max_process_rss_kib':max(m['peak_rss_kib'] for m in measurements),'max_arrow_batch_bytes':max(m['max_arrow_batch_bytes'] for m in measurements),'acceptance':'Host staging only; distribution and Android acceptance open'}
atomic(edition/'summary.json',summary);atomic(lane/'milestone.json',summary);print(json.dumps(summary,indent=2),flush=True)
