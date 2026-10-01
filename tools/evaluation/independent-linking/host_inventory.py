"""Record installed evaluation-only package binaries and notices; no app deployment."""
from pathlib import Path
import importlib.metadata as md,hashlib,json,sys,shutil
R=Path(__file__).resolve().parents[3];D=R/'docs/evidence/independent-linking';D.mkdir(exist_ok=True)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
items=[]
for name in ['onnxruntime','tokenizers','numpy']:
 dist=md.distribution(name);files=[];notices=[]
 for f in dist.files or []:
  path=Path(dist.locate_file(f))
  if not path.is_file() or path.suffix=='.pyc':continue
  files.append({'relative':str(f),'bytes':path.stat().st_size,'sha256':sha(path)})
  if any(x in str(f).upper() for x in ['LICENSE','NOTICE','COPYING']):
   dest=D/'host-notices'/name/str(f);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest);notices.append(str(dest.relative_to(R)))
 items.append({'name':name,'version':dist.version,'metadata_license':dist.metadata.get('License-Expression') or dist.metadata.get('License'),'files':files,'notices':notices})
(D/'host-inventory.json').write_text(json.dumps({'python':sys.version,'scope':'Evaluation-only isolated virtual environment, not packaged Android dependencies','packages':items},indent=2)+'\n')
