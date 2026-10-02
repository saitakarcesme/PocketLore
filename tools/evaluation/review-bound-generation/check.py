from pathlib import Path
import subprocess,tempfile
R=Path(__file__).resolve().parents[3];F=Path(__file__).parent;J=Path('/home/isa/Android/atlas-toolchain/jdk/bin');base=R/'android/app/src/main/java/org/pocketlore/app'
with tempfile.TemporaryDirectory() as tmp:
 sources=[base/(n+'.java') for n in ['ResearchEngine','EvidencePrompt','EvidenceAvailability','AnswerEngine','NativeRuntime','GeneralGroundedAnswer','GroundedGeneration','ReviewedAnswerVerifier']]
 subprocess.run([J/'javac','-d',tmp,*sources,F/'Behavior.java'],check=True)
 subprocess.run([J/'java','-Xmx128m','-cp',tmp,'org.pocketlore.app.Behavior'],check=True)
print('Review contract only: no production authority, semantic support or selected-model Android proof')
