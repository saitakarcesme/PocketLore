#!/usr/bin/env python3
"""Hash the explicit installed set and acquisition receipts; never scan private control files."""
import argparse,datetime,json,pathlib,sys,time
from acquire import atomic,digest
p=argparse.ArgumentParser();p.add_argument('lane');p.add_argument('edition');p.add_argument('--require-shards',type=int,default=15);a=p.parse_args();lane=pathlib.Path(a.lane).resolve();root=lane/a.edition
manifest=root/'installed-inventory.json'
if manifest.exists():raise SystemExit('Refuse to replace sealed inventory')
shards=sorted(root.glob('*/measurement.json'))
if len(shards)!=a.require_shards:raise SystemExit('Incomplete shard inventory')
start=time.monotonic();files=[]
for m in shards:
 measurement=json.loads(m.read_text())
 if not measurement['source_complete']:raise SystemExit('Unfinished shard')
 files.extend([m,m.parent/'catalog.sqlite',m.parent/'articles.blocks'])
files.extend(sorted(root.glob('*.txt')));files.extend(sorted(root.glob('*.sqlite')));files.extend(p for p in sorted(root.glob('*.json')) if p!=manifest)
entries=[]
for f in sorted(set(files)):
 before=f.stat();h=digest(f);after=f.stat()
 if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise RuntimeError('File changed during sealing')
 entries.append({'path':str(f.relative_to(root)),'bytes':after.st_size,'sha256':h});print(f.name,after.st_size,flush=True)
inputs=[]
for f in sorted((lane/'bulk').glob('*.receipt.json')):
 receipt=json.loads(f.read_text());source=pathlib.Path(str(f).removesuffix('.receipt.json'))
 if not source.exists() or source.stat().st_size!=receipt['bytes']:raise RuntimeError('Acquired input size mismatch')
 inputs.append({'path':str(source),'bytes':receipt['bytes'],'sha256':receipt['sha256'],'receipt':str(f),'receipt_sha256':digest(f),'verification':'SHA-256 at acquisition; size rechecked at sealing; original receipt bound'})
result={'schema':1,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'edition':a.edition,'platform':'LLMRig Linux staging only','files':entries,'installed_payload_bytes':sum(x['bytes'] for x in entries),'inventory_self_bytes':0,'installed_total_bytes':0,'budget_decimal_bytes':22000000000,'budget_passed':False,'acquired_sources':inputs,'source_dataset_revision':'8bd13e72e6a002407649b3e898535f42ceb1aeb9','source_contract':'docs/evidence/scale/wiki/ANDROID_READER_SCHEMA.md','seconds_hashing':time.monotonic()-start,'limits':['Inventory is integrity metadata, not publisher authentication','No Android, human, distribution-rights or rival acceptance','Input hashes reference preserved acquisition checks; installed files freshly hashed']}
# Self size, but deliberately no self hash: handoff binds the inventory hash externally.
for _ in range(12):
 raw=(json.dumps(result,indent=2)+'\n').encode();size=len(raw);total=result['installed_payload_bytes']+size
 if result['inventory_self_bytes']==size and result['installed_total_bytes']==total and result['budget_passed']==(total<=result['budget_decimal_bytes']):break
 result.update({'inventory_self_bytes':size,'installed_total_bytes':total,'budget_passed':total<=result['budget_decimal_bytes']})
else:raise RuntimeError('Inventory size did not stabilize')
atomic(manifest,result);assert manifest.stat().st_size==result['inventory_self_bytes'];print(json.dumps({'manifest':str(manifest),'sha256':digest(manifest),'installed_bytes':result['installed_total_bytes'],'budget_passed':result['budget_passed']},indent=2));sys.exit(0 if result['budget_passed'] else 1)
