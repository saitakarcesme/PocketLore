#!/usr/bin/env python3
"""Bundle sealed first milestones without re-downloading or modifying lane artifacts."""
import hashlib,json,pathlib,zipfile
ROOT=pathlib.Path('/home/isa/PocketLore-control/scale-workers')
OUT=pathlib.Path('downloads/scale-integration');OUT.mkdir(parents=True,exist_ok=True)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def build(kind,base,paths,extra,inventory):
 specs=[dict(path=p,bytes=(base/p).stat().st_size,sha256=sha(base/p)) for p in paths]
 m=dict(version=1,kind=kind,generation_allowed=False,rights_status='unreviewed_source_specific_terms; browse_only',source_inventory_sha256=sha(inventory),installed_bytes=sum(f['bytes'] for f in specs),files=specs,**extra)
 raw=(json.dumps(m,sort_keys=True,indent=2)+'\n').encode();dest=OUT/(kind+'-first.plscale')
 if dest.exists():raise SystemExit('Refusing to overwrite '+str(dest))
 with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as z:
  info=zipfile.ZipInfo('manifest.json',(2026,10,1,0,0,0));z.writestr(info,raw)
  for f in specs:
   info=zipfile.ZipInfo(f['path'],(2026,10,1,0,0,0));info.file_size=f['bytes']
   with (base/f['path']).open('rb') as src,z.open(info,'w',force_zip64=True) as dst:
    for b in iter(lambda:src.read(1024*1024),b''):dst.write(b)
 receipt=dict(manifest_sha256=hashlib.sha256(raw).hexdigest(),archive_bytes=dest.stat().st_size,archive_sha256=sha(dest),manifest=m)
 (OUT/(kind+'-receipt.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(kind,receipt['archive_bytes'],receipt['archive_sha256'],flush=True)
wiki=ROOT/'wiki/edition-v7'
if not (OUT/'wiki-first.plscale').exists():build('wiki',wiki,['000_00000/'+p for p in ('articles.blocks','catalog.sqlite','measurement.json')]+['NOTICE.txt','CC-BY-SA-3.0.txt','CC-BY-SA-4.0.txt','CC0-1.0.txt','provenance.json'],dict(shards=['000_00000'],label='English reference — first shard',documents=413151,full_articles=82022,leads=331129,lane_commit='db58d7015b176b2f4721a9fe9a221c9593456e14'),wiki/'installed-inventory.json')
places=ROOT/'places/data'
if not (OUT/'places-first.plscale').exists():build('places',places,['compact-00.sqlite','cities.sqlite']+[str(p.relative_to(places)) for p in sorted((places/'notices').iterdir()) if p.is_file()],dict(shards=['compact-00.sqlite'],cities='cities.sqlite',label='World places — first shard',source_records=5120674,semantic_unique_entities=None,lane_commit='9a04ac33488a05f61435d62f8be249fd7fe135af'),ROOT/'places/HANDOFF.json')
