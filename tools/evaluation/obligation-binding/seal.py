"""Archive finished text evidence without binaries, accepting only byte-identical reuse."""
from pathlib import Path
import hashlib,json,shutil,sys
R=Path(__file__).resolve().parents[3];E=R/'docs/evidence/obligation-binding'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
for src,name in [(Path(sys.argv[1]),'run'),(Path(sys.argv[2]),'history')]:
 receipt=json.loads((src/'receipt.json').read_text());assert receipt['exit_code']==0 and not receipt['killed']
 for rel,h in receipt['artifacts'].items():assert sha(src/rel)==h,rel
 for p in sorted(src.rglob('*')):
  if not p.is_file() or 'classes' in p.parts:continue
  out=E/name/p.relative_to(src);out.parent.mkdir(parents=True,exist_ok=True)
  if out.exists():assert out.read_bytes()==p.read_bytes(),'Refusing divergent overwrite: '+str(out)
  else:shutil.copyfile(p,out)
apk=R/'android/app/build/outputs/apk/debug/app-debug.apk';(E/'build.json').write_text(json.dumps({'apk':str(apk.relative_to(R)),'bytes':apk.stat().st_size,'sha256':sha(apk)},indent=2)+'\n')
print('Sealed finished main and historical text runs; models and class/native/APK binaries excluded')
