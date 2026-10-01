#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,sqlite3,subprocess,datetime
R=Path(__file__).resolve().parents[3];F=Path(__file__).resolve().parent;A=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5560'];pack=R/'downloads/broad-reference/rendered-v2/broad-reference.plpack'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
# Two new public source-fidelity queries, separate from unchanged 40-case recall.
c=sqlite3.connect(R/'downloads/broad-reference/rendered-v2/index.sqlite');tests=[]
for ident,q,required in [('991','absolute value 3','[TeX: {\\displaystyle |0|=0}]'),('633','algae 50 metres','50 metres (160 ft)')]:
 row=c.execute('SELECT citation,body FROM passages WHERE document=? AND body LIKE ? ORDER BY pid LIMIT 1',(ident,'%'+required+'%')).fetchone();assert row;tests.append({'question':q,'citation':'p'+sha(pack)+'_'+row[0],'text':row[1],'required':required})
protocol=R/'docs/evidence/broad-reference/repair/fidelity-protocol.json';raw=(json.dumps({'purpose':'Source formula/unit visibility only; no generation success credit','cases':tests},indent=2)+'\n').encode()
if protocol.exists():assert protocol.read_bytes()==raw,'Frozen fidelity protocol changed'
else:protocol.write_bytes(raw)
out=R/'downloads/broad-reference'/datetime.datetime.now(datetime.timezone.utc).strftime('fidelity-%Y%m%dT%H%M%S%fZ');out.mkdir();print(out,flush=True)
def run(args,name,data=None):
 p=subprocess.run(list(map(str,args)),input=data,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=600);(out/name).write_bytes(p.stdout);assert p.returncode==0,name;return p.stdout
run(['bash',R/'tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',F/'repair.gradle','-PpocketloreTestRunner=org.pocketlore.app.FidelityInstrumentation'],'build.log')
run(A+['install','-r',R/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk'],'install.txt');run(A+['exec-in','run-as','org.pocketlore.app','sh','-c','cat > files/broad-tests/fidelity.json'],'copy.txt',raw);run(A+['shell','am','force-stop','org.pocketlore.app'],'stop.txt');log=run(A+['shell','am','instrument','-w','org.pocketlore.app.test/org.pocketlore.app.FidelityInstrumentation'],'instrument.txt');result=json.loads(run(A+['exec-out','run-as','org.pocketlore.app','cat','files/broad-tests/fidelity-result.json'],'result.json'));assert result['status']=='PASS' and b'INSTRUMENTATION_CODE: -1' in log,result
for i in range(2):run(A+['exec-out','run-as','org.pocketlore.app','cat','files/broad-tests/fidelity-'+str(i)+'.png'],'fidelity-'+str(i)+'.png')
receipt={'apk_sha256':sha(R/'android/app/build/outputs/apk/debug/app-debug.apk'),'pack_sha256':sha(pack),'protocol_sha256':sha(protocol),'harness_sha256':sha(F/'FidelityInstrumentation.java'),'records':{p.name:sha(p) for p in out.iterdir()}}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('PASS',out)
