from pathlib import Path
import json,shutil,sys
R=Path(__file__).resolve().parents[3];E=R/'docs/evidence/fact-frames'
def copy(src,dst):
 for p in sorted(src.rglob('*')):
  if not p.is_file() or 'classes' in p.parts:continue
  q=dst/p.relative_to(src);q.parent.mkdir(parents=True,exist_ok=True)
  if q.exists():assert q.read_bytes()==p.read_bytes(),'Refusing evidence overwrite: '+str(q)
  else:shutil.copyfile(p,q)
for arg,name in zip(sys.argv[1:],['new-run','replay']):
 source=(R/arg).resolve();assert json.loads((source/'receipt.json').read_text())['exit_code']==0;copy(source,E/name)
