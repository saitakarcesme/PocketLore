from pathlib import Path
import subprocess,json,base64,tempfile
R=Path(__file__).resolve().parents[3];F=Path(__file__).parent;java=Path('/home/isa/Android/atlas-toolchain/jdk/bin')
with tempfile.TemporaryDirectory() as t:
 d=Path(t);s=json.loads((F/'sources.json').read_text())['sources'];enc=lambda s:base64.b64encode(s.encode()).decode()
 source=d/'sources.tsv';source.write_text(''.join('\t'.join(enc(x[k]) for k in ['id','title','url','date','license','text'])+'\n' for x in s))
 subprocess.run([java/'javac','-d',d,R/'android/app/src/main/java/org/pocketlore/app/ResearchEngine.java',R/'android/app/src/main/java/org/pocketlore/app/GeneralGroundedAnswer.java',F/'Behavior.java'],check=True)
 subprocess.run([java/'java','-Xmx256m','-cp',d,'org.pocketlore.app.Behavior',source],check=True)
