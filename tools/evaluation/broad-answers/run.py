#!/usr/bin/env python3
from pathlib import Path
import datetime,subprocess,json,hashlib,sys
R=Path(__file__).resolve().parents[3];F=Path(__file__).resolve().parent;mode=sys.argv[1] if len(sys.argv)>1 else 'after'
A=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5560']
out=R/'downloads/broad-answers'/datetime.datetime.now(datetime.timezone.utc).strftime(mode+'-%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True);print(out,flush=True)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def run(args,name,data=None):
 p=subprocess.run(list(map(str,args)),input=data,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=1800);(out/name).write_bytes(p.stdout);assert p.returncode==0,name;return p.stdout
run(['bash',R/'tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',F/'source.gradle','-PpocketloreTestRunner=org.pocketlore.app.BroadAnswerInstrumentation'],'build.log')
for name,p in [('app',R/'android/app/build/outputs/apk/debug/app-debug.apk'),('test',R/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk')]:run(A+['install','-r',p],'install-'+name+'.txt')
run(A+['exec-out','run-as','org.pocketlore.app','cat','files/pack-library/catalog.json'],'catalog-before.json')
run(A+['shell','run-as','org.pocketlore.app','mkdir','-p','files/broad-answer-tests'],'mkdir.txt')
for name,p in [('protocol.json',F/'protocol.json'),('retrieval.json',R/'tools/evaluation/broad-reference/protocol.json')]:run(A+['exec-in','run-as','org.pocketlore.app','sh','-c','cat > files/broad-answer-tests/'+name],'copy-'+name+'.txt',p.read_bytes())
run(A+['shell','cmd','connectivity','airplane-mode','enable'],'airplane.txt');run(A+['shell','svc','wifi','disable'],'wifi.txt');run(A+['shell','svc','data','disable'],'data.txt')
run(A+['shell','am','force-stop','org.pocketlore.app'],'stop.txt')
log=run(A+['shell','am','instrument','-w','-e','mode',mode,'org.pocketlore.app.test/org.pocketlore.app.BroadAnswerInstrumentation'],'instrument.txt')
r=json.loads(run(A+['exec-out','run-as','org.pocketlore.app','cat','files/broad-answer-tests/results.json'],'results.json'))
for link in r.get('links',[]):run(A+['exec-out','run-as','org.pocketlore.app','cat','files/broad-answer-tests/'+link['case']+'-citation.png'],link['case']+'-citation.png')
run(A+['exec-out','run-as','org.pocketlore.app','cat','files/pack-library/catalog.json'],'catalog-after.json')
receipt={'apk_sha256':sha(R/'android/app/build/outputs/apk/debug/app-debug.apk'),'model_env_sha256':sha(R/'tools/answers/model.env'),'sources':{str(p.relative_to(R)):sha(p) for p in list((R/'android/app/src/main/java/org/pocketlore/app').glob('*.java'))+list(F.glob('*.java'))+[F/'protocol.json',R/'tools/evaluation/broad-reference/protocol.json']},'records':{p.name:sha(p) for p in out.iterdir()}}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
assert r['status']=='PASS' and b'INSTRUMENTATION_CODE: -1' in log,r.get('failure')
assert (out/'catalog-before.json').read_bytes()==(out/'catalog-after.json').read_bytes(),'Catalog changed'
print('PASS',out)
