"""Copy completed text evidence only. Never overwrite differing historical receipts."""
from pathlib import Path
import sys,shutil,json,hashlib
R=Path(__file__).resolve().parents[3];E=R/'docs/evidence/independent-linking'
def copy(source,target):
 for p in sorted(source.rglob('*')):
  if not p.is_file() or 'classes' in p.parts:continue
  dest=target/p.relative_to(source);dest.parent.mkdir(parents=True,exist_ok=True)
  if dest.exists():assert dest.read_bytes()==p.read_bytes(),f'Refusing changed evidence {dest}'
  else:shutil.copyfile(p,dest)
if __name__=='__main__':
 new=R/sys.argv[1];score=R/sys.argv[2];assert json.loads((new/'receipt.json').read_text())['exit_code']==0;assert (score/'score-receipt.json').is_file() and (score/'final/linked.json').is_file()
 copy(new,E/'new-run');copy(score,E/'scoring');print('Sealed completed generation and classifier text artifacts')
