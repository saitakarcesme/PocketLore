from pathlib import Path
import json,hashlib,subprocess,base64,sys,time
R=Path(__file__).resolve().parents[3];F=Path(__file__).parent;TC=Path('/home/isa/Android/atlas-toolchain/jdk/bin')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def run(out):
 out.mkdir(exist_ok=False,parents=True);classes=out/'classes';classes.mkdir();manifest=json.loads((R/'docs/evidence/source-plan/run/manifest.json').read_text());src=[R/p for p in manifest['sources'] if p.endswith('.java')]+[R/'android/app/src/main/java/org/pocketlore/app/EquationProof.java',R/'android/app/src/main/java/org/pocketlore/app/SemanticPlan.java',F/'ReplayEquation.java',F/'Behavior.java',R/'tools/evaluation/fact-frames/FrameBehavior.java'];subprocess.run([TC/'javac','-d',classes,*src],check=True)
 enc=lambda x:base64.b64encode(x.encode()).decode();controls=json.loads((F/'controls.json').read_text());(out/'controls.tsv').write_text('\n'.join(enc(t)+'\t'+str(expected).lower() for t,expected in controls['cases'])+'\n');subprocess.run([TC/'java','-cp',classes,'org.pocketlore.app.Behavior',out/'controls.tsv'],check=True)
 values=[json.loads(p.read_text()) for p in sorted((R/'docs/evidence/source-plan/run/results').glob('q[0-9][0-9].json'))];rows=[]
 for v in values:rows.append('\t'.join([v['id'],enc(v['question']),enc(v['plan']['raw']),str(v['plan']['tokens']),enc(v['draft']['raw']),str(v['draft']['tokens']),enc(v['plan']['failure']),enc(v['draft']['failure'])]))
 (out/'stages.tsv').write_text('\n'.join(rows)+'\n');start=time.monotonic();subprocess.run([TC/'java','-cp',classes,'org.pocketlore.app.ReplayEquation',R/'docs/evidence/source-plan/run/inputs',out/'stages.tsv',out/'results.json'],check=True)
 receipt={'elapsed_seconds':time.monotonic()-start,'sources':{str(p.relative_to(R)):sha(p) for p in src+[F/'replay.py',F/'controls.json',F/'protocol.json']},'artifacts':{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and 'classes' not in p.parts}}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return out
if __name__=='__main__':run(Path(sys.argv[1]).resolve())
