"""Read only sealed lane handoffs; hash actual artifacts without using stale launcher HEAD."""
from pathlib import Path
import json,hashlib,time,subprocess
R=Path(__file__).resolve().parents[3];L=Path('/home/isa/PocketLore-control/scale-workers');E=R/'docs/evidence/scale-integration'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
rows=[];start=time.monotonic()
for lane in ['wiki','places','android']:
 h=json.loads((L/lane/'HANDOFF.json').read_text());paths=[]
 if lane=='wiki':
  inv=json.loads((L/lane/'edition-v7/installed-inventory.json').read_text());paths=[dict(x,path=str(L/lane/'edition-v7'/x['path'])) for x in inv['files']]
 elif lane=='places':paths=h['assets']+h['license_texts']
 else:paths=h['artifacts']+h['source_reader_contracts']
 for item in paths:
  p=Path(item['path']);assert p.stat().st_size==item['bytes'],str(p);got=sha(p);assert got==item['sha256'],str(p);rows.append({'lane':lane,'path':str(p),'bytes':p.stat().st_size,'sha256':got});print(lane,p.name,'verified',flush=True)
(E/'artifact-checks.json').write_text(json.dumps({'elapsed_seconds':time.monotonic()-start,'artifacts':rows,'scope':'Actual selected handoff installed-set and Android artifact/source hashes; source archives retain lane receipts; no phone installation inferred'},indent=2)+'\n')
