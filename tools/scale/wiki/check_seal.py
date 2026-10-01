#!/usr/bin/env python3
"""Verify sealed files and exact installed byte total before reader admission."""
import argparse,json,pathlib,time
from acquire import digest,atomic
p=argparse.ArgumentParser();p.add_argument('inventory');p.add_argument('output');a=p.parse_args();path=pathlib.Path(a.inventory);m=json.loads(path.read_text());root=path.parent;start=time.monotonic();failures=[];total=path.stat().st_size
for item in m['files']:
 rel=pathlib.PurePosixPath(item['path'])
 if rel.is_absolute() or '..' in rel.parts:raise ValueError('Invalid manifest path')
 f=root/rel
 if not f.is_file() or f.is_symlink():failures.append({'path':str(rel),'failure':'missing or symbolic link'});continue
 size=f.stat().st_size;total+=size
 if size!=item['bytes'] or digest(f)!=item['sha256']:failures.append({'path':str(rel),'failure':'size or hash mismatch'})
result={'passed':not failures and total==m['installed_total_bytes'] and total<=m['budget_decimal_bytes'],'files':len(m['files']),'failures':failures,'installed_bytes':total,'inventory_sha256':digest(path),'seconds':time.monotonic()-start,'checks':'Fresh installed-file hashes and exact byte total; no source re-extraction or device acceptance'};atomic(a.output,result);print(json.dumps(result,indent=2));raise SystemExit(0 if result['passed'] else 1)
