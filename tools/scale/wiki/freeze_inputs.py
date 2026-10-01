#!/usr/bin/env python3
"""Fresh hashes of explicit public inputs, preserved prototypes and source fixtures."""
import argparse,datetime,json,pathlib,time
from acquire import atomic,digest
p=argparse.ArgumentParser();p.add_argument('lane');p.add_argument('output');a=p.parse_args();lane=pathlib.Path(a.lane).resolve();output=pathlib.Path(a.output);partial=output.with_suffix(output.suffix+'.partial.json')
if output.exists():raise SystemExit('Refuse to replace sealed input evidence')
start=time.monotonic();inventory=json.loads(pathlib.Path('docs/evidence/scale/wiki/english-inventory.json').read_text());items={}
def add(path,kind,expected=None):
 path=pathlib.Path(path)
 if path.is_file():items[str(path.resolve())]={'kind':kind,'expected_sha256':expected}
for item in inventory['files']:
 source=lane/'bulk'/pathlib.Path(item['path']).name
 if not source.is_file():raise RuntimeError('Missing pinned English source')
 add(source,'pinned_finewiki_input',item['lfs']['oid']);add(source.with_suffix(source.suffix+'.receipt.json'),'acquisition_receipt')
for name in ['pageviews-neuml.sqlite','enwiki-20260901-redirect.sql.gz','enwiki-20260901-pages-articles-multistream-index.txt.bz2']:
 source=lane/'bulk'/name
 if not source.is_file():raise RuntimeError('Missing pinned auxiliary input: '+name)
 receipt=source.with_suffix(source.suffix+'.receipt.json');r=json.loads(receipt.read_text());add(source,'pinned_auxiliary_input',r['sha256']);add(receipt,'acquisition_receipt')
for name in ['census.sqlite','census-v2.sqlite','priority-2000000.sqlite','priority-1250000.sqlite','redirects-staging.sqlite']:
 add(lane/name,'preserved_staging_database')
 for suffix in ['-wal','-shm']:add(lane/(name+suffix),'preserved_database_recovery_sidecar')
add(lane/'acquisition-state.json','encyclopedia_acquisition_recovery_state')
add(lane/'bulk/pageviews-range-probe','preserved_acquisition_probe')
for name in ['pilot-full','edition-v2','edition-v4','edition-v5','edition-v6','individual-block-contract-fixture','shared-block-contract-fixture','reblocked-contract-fixture','stop-index-contract-fixture']:
 root=lane/name
 for pattern in ['**/catalog.sqlite','**/articles.blocks','**/measurement.json','**/progress.json','**/orphan-*.blocks']:
  for path in root.glob(pattern):add(path,'preserved_prototype_or_fixture')
add(lane/'edition-v4/redirect-aliases.sqlite','original_alias_database')
add(lane/'bulk/real-source-contract-fixture.parquet','derived_test_fixture_not_a_source_shard')
for dirname in ['alias-normalization-fixture','seal-contract-fixture']:
 for path in (lane/'receipts'/dirname).rglob('*'):
  if path.suffix in ['.sqlite','.blocks','.json']:add(path,'preserved_positive_or_negative_control_fixture')
for path in (lane/'bulk').glob('*.part'):add(path,'incomplete_acquisition_not_used')
for path in (lane/'bulk').glob('*.failures.jsonl'):add(path,'acquisition_failure_receipt')
for dirname in ['query-sources','selected-query-sources']:
 for path in (lane/'receipts'/dirname).glob('*.json'):add(path,'public_source_record_fixture')
for name in ['counterexample-source.json','empty-candidate-real.json','frozen-tail-source-records.json','session-identity.json','selected-query-source-summary.json','git-storage-failure.txt']:add(lane/'receipts'/name,'explicit_task_receipt')
for path in (lane/'receipts').glob('enwiki-20260901-*.verified.json'):add(path,'primary_alias_source_verification')
for pattern in ['acquisition.log','census*.log','counterexample-audit.log','edition-v2*','edition-v4*','edition-v5*','edition-v6*','pageviews*.log','pilot*.log','priority*.log','redirect*.log','selected-source-extraction.log']:
 for path in (lane/'receipts').glob(pattern):
  if path.suffix in ['.log','.json']:add(path,'preserved_prior_execution_receipt')
old=json.loads(partial.read_text()) if partial.exists() else {'files':[]};completed={x['path']:x for x in old['files']};entries=[]
for name,meta in sorted(items.items()):
 path=pathlib.Path(name);before=path.stat();prior=completed.get(name)
 if prior and prior['bytes']==before.st_size and prior['mtime_ns']==before.st_mtime_ns:entry=prior
 else:
  actual=digest(path);after=path.stat()
  if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise RuntimeError('Audit artifact changed during hashing: '+name)
  entry={'path':name,'bytes':after.st_size,'mtime_ns':after.st_mtime_ns,'sha256':actual,'hashed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**meta}
 if meta['expected_sha256'] and entry['sha256']!=meta['expected_sha256']:raise RuntimeError('Pinned input hash mismatch: '+name)
 entries.append(entry);atomic(partial,{'files':entries});print(meta['kind'],path.name,flush=True)
result={'schema':1,'sealed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':entries,'files_count':len(entries),'bytes_hashed':sum(x['bytes'] for x in entries),'fresh_pinned_input_hashes_passed':True,'finewiki_shards':sum(x['kind']=='pinned_finewiki_input' for x in entries),'finewiki_bytes':sum(x['bytes'] for x in entries if x['kind']=='pinned_finewiki_input'),'seconds_this_run':time.monotonic()-start,'scope':'Explicit public corpus inputs, own task receipts and prior prototypes only; no supervisor state, private conversations, holdout or secrets scanned','limits':'Current edition and its active logs are sealed separately after build completion; incomplete acquisition artifacts are evidence only, never ranking inputs'};atomic(output,result);print(json.dumps({k:v for k,v in result.items() if k!='files'},indent=2))
