#!/usr/bin/env python3
"""Build v2 content-addressed manifests/deltas from sealed local bytes; no downloads.

Use --base previous-manifest.json for an atomic replacement of one collection.
Only changed content enters the archive. Provider copies remain separate budget costs.
"""
import argparse,hashlib,json,pathlib,zipfile
LANES=pathlib.Path('/home/isa/PocketLore-control/scale-workers')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('kind',choices=['wiki','places']);ap.add_argument('--base',type=pathlib.Path);ap.add_argument('--output',required=True,type=pathlib.Path);ap.add_argument('--archive',action='store_true');a=ap.parse_args()
 old=json.loads(a.base.read_text()) if a.base else None
 known={f['sha256'] for f in old['files']} if old else set()
 if a.kind=='wiki':
  root=LANES/'wiki/edition-v7';inventory=root/'installed-inventory.json';allfiles=json.loads(inventory.read_text())['files'];shards=sorted({f['path'].split('/')[0] for f in allfiles if f['path'].endswith('/catalog.sqlite')});specs=allfiles
  import sqlite3
  counts=[0,0,0]
  for sh in shards:
   with sqlite3.connect('file:'+str(root/sh/'catalog.sqlite')+'?mode=ro&immutable=1',uri=True) as c:
    vals=c.execute("select count(*),sum(tier='full'),sum(tier='lead') from articles").fetchone()
   counts=[x+y for x,y in zip(counts,vals)]
  extra=dict(shards=shards,documents=counts[0],full_articles=counts[1],leads=counts[2],aliases='redirect-aliases.sqlite')
 else:
  root=LANES/'places/data';inventory=LANES/'places/HANDOFF.json';assets=json.loads(inventory.read_text())['assets'];specs=[]
  for f in assets:
   p=pathlib.Path(f['path'])
   if p.name.startswith('compact-') or p.name=='cities.sqlite' or 'notices' in p.parts:specs.append(dict(path=str(p.relative_to(root)),bytes=f['bytes'],sha256=f['sha256']))
  # Notices not separately listed in the handoff are included with fresh receipts.
  paths={f['path'] for f in specs}
  for p in sorted((root/'notices').glob('*')):
   if p.is_file() and str(p.relative_to(root)) not in paths:specs.append(dict(path=str(p.relative_to(root)),bytes=p.stat().st_size,sha256=sha(p)))
  import sqlite3
  shards=sorted(f['path'] for f in specs if f['path'].startswith('compact-'));count=0
  for sh in shards:
   with sqlite3.connect('file:'+str(root/sh)+'?mode=ro&immutable=1',uri=True) as c:count+=c.execute('select sum(records) from block').fetchone()[0]
  extra=dict(shards=shards,source_records=count,cities='cities.sqlite',semantic_unique_entities=None)
 fs=[]
 for f in specs:
  p=root/f['path'];assert p.stat().st_size==f['bytes'] and sha(p)==f['sha256'],p
  fs.append(dict(path=f['path'],bytes=f['bytes'],sha256=f['sha256'],payload=f['sha256'] not in known))
 m=dict(version=2,kind=a.kind,collection_key='sealed-'+a.kind,label='Sealed '+a.kind+' — all shards, browse only',replaces=sha(a.base) if a.base else '',generation_allowed=False,rights_status='unreviewed_source_specific_terms; browse_only',source_inventory_sha256=sha(inventory),installed_bytes=sum(f['bytes'] for f in fs),files=fs,**extra)
 raw=(json.dumps(m,sort_keys=True,indent=2)+'\n').encode();a.output.parent.mkdir(parents=True,exist_ok=True)
 with a.output.open('xb') as out:out.write(raw)
 if a.archive:
  with zipfile.ZipFile(a.output.with_suffix('.plscale'),'x',compression=zipfile.ZIP_STORED,allowZip64=True) as z:
   z.writestr('manifest.json',raw)
   for f in fs:
    if f['payload']:z.write(root/f['path'],f['path'])
 print(json.dumps({'manifest':str(a.output),'sha256':sha(a.output),'installed_bytes':m['installed_bytes'],'incoming_payload_bytes':sum(f['bytes'] for f in fs if f['payload']),'shared_bytes':sum(f['bytes'] for f in fs if not f['payload'])}))
if __name__=='__main__':main()
