"""Deterministic composition over immutable scored drafts; no model inference."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
R=Path(__file__).resolve().parents[3];F=Path(__file__).parent;TC=Path('/home/isa/Android/atlas-toolchain/jdk/bin');OLD=R/'docs/evidence/independent-linking/scoring'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def sources():
 m=json.loads((OLD/'manifest.json').read_text())
 return [R/p for p in m['sources'] if p.endswith('.java')]+[R/'android/app/src/main/java/org/pocketlore/app/FactFrames.java',R/'android/app/src/main/java/org/pocketlore/app/GuardedEvidenceLinker.java',F/'GuardedHarness.java']
def run(out):
 out.mkdir(parents=True,exist_ok=False);classes=out/'classes';classes.mkdir();src=sources();subprocess.run([TC/'javac','-d',classes,*src],check=True);start=time.monotonic()
 cmd=[str(TC/'java'),'-Xmx256m','-cp',str(classes),'org.pocketlore.app.GuardedHarness',str(OLD/'inputs'),str(out/'results'),str(OLD/'scores.tsv')]
 with (out/'stdout.txt').open('w') as o,(out/'stderr.txt').open('w') as e:p=subprocess.run(cmd,stdout=o,stderr=e,timeout=120)
 v={'exit_code':p.returncode,'elapsed_seconds':time.monotonic()-start,'command':cmd,'sources':{str(s.relative_to(R)):sha(s) for s in src},'inputs_seal':sha(R/'docs/evidence/independent-linking/SHA256SUMS'),'protocol_sha256':sha(F/'protocol.json'),'artifacts':{str(s.relative_to(out)):sha(s) for s in out.rglob('*') if s.is_file() and 'classes' not in s.parts}}
 (out/'receipt.json').write_text(json.dumps(v,indent=2)+'\n');return p.returncode
if __name__=='__main__':raise SystemExit(run(Path(sys.argv[1]).resolve()))
