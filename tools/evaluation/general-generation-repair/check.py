from pathlib import Path
import subprocess,tempfile
R=Path(__file__).resolve().parents[3];F=Path(__file__).parent;J=Path('/home/isa/Android/atlas-toolchain/jdk/bin');base=R/'android/app/src/main/java/org/pocketlore/app'
with tempfile.TemporaryDirectory() as tmp:
 sources=[base/(n+'.java') for n in ['ResearchEngine','EvidencePrompt','EvidenceAvailability','AnswerEngine','NativeRuntime','GeneralGroundedAnswer','GroundedGeneration']]
 subprocess.run([J/'javac','-d',tmp,*sources,F/'IntegrationBehavior.java'],check=True)
 subprocess.run([J/'java','-Xmx256m','-cp',tmp,'org.pocketlore.app.IntegrationBehavior'],check=True)
s=(base/'NativePanel.java').read_text();start=s.index('void answer(String question');end=s.index('static android.text.SpannableString linkClaims',start);wiring=s[start:end]
assert 'GroundedGeneration.answer' in wiring and 'GeneralGroundedAnswer.SYSTEM' in wiring and 'GroundedGeneration.UNAVAILABLE' in wiring
assert 'generateClaims(' not in wiring and 'AnswerEngine.answer(' not in wiring
print('PASS: actual NativePanel general chat wiring, no finite claims grammar, no qualified production verifier')
