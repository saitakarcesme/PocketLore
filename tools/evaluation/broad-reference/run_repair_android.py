#!/usr/bin/env python3
from pathlib import Path
import subprocess,json,hashlib,datetime,zipfile,os
R=Path(__file__).resolve().parents[3];F=Path(__file__).resolve().parent;tc=Path(os.environ.get('POCKETLORE_TOOLCHAIN','/home/isa/Android/atlas-toolchain'));adb=[tc/'sdk/platform-tools/adb','-s','emulator-5560'];pack=R/'downloads/broad-reference/rendered-v2/broad-reference.plpack'
out=R/'downloads/broad-reference'/datetime.datetime.now(datetime.timezone.utc).strftime('repair-android-%Y%m%dT%H%M%S%fZ');out.mkdir();print(out,flush=True)
def run(args,name,data=None):
 p=subprocess.run(list(map(str,args)),input=data,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=900);(out/name).write_bytes(p.stdout);assert p.returncode==0,str(out/name);return p.stdout
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert run(adb+['shell','getprop','sys.boot_completed'],'boot.txt').strip()==b'1'
run(['bash',R/'tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',F/'repair.gradle','-PpocketloreTestRunner=org.pocketlore.app.BroadRepairInstrumentation'],'build.log')
for rel in ['debug/app-debug.apk','androidTest/debug/app-debug-androidTest.apk']:run(adb+['install','-r',R/'android/app/build/outputs/apk'/rel],'install-'+Path(rel).name+'.txt')
# Archive only the prior project fixture catalog before deliberate fixture addition, no reset/uninstall.
run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/pack-library/catalog.json'],'catalog-before.json')
run(adb+['shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf'],'model-before.txt')
catalog=json.loads((out/'catalog-before.json').read_text());old='915f82f041f59d3cd0e82a8b6fd9dbdb2d12187c2e969c5891de6e3ad46dd67c'
entries=catalog['collections'];known=[e for e in entries if e.get('sha256')==old or e.get('hash')==old]
if known:
 assert len(entries)==3 and len(known)==1,'Only the known prior project fixture may be replaced'
 run(adb+['shell','am','force-stop','org.pocketlore.app'],'stop-before-fixture.txt')
 for suffix in ['.plpack','.sqlite']:run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/pack-library/'+old+suffix],'archived-'+old+suffix)
 catalog['collections']=[e for e in entries if e not in known]
 run(adb+['exec-in','run-as','org.pocketlore.app','sh','-c','cat > files/pack-library/catalog.json'], 'replace-owned-catalog.txt',(json.dumps(catalog)+'\n').encode())
run(adb+['shell','run-as','org.pocketlore.app','mkdir','-p','files/broad-tests'],'mkdir.txt')
corrupt=out/'corrupt.plpack'
with zipfile.ZipFile(pack) as z,zipfile.ZipFile(corrupt,'w',zipfile.ZIP_DEFLATED) as w:
 for n in z.namelist():
  data=z.read(n)
  if n=='index.sqlite':data=data[:-1]+bytes([data[-1]^1])
  w.writestr(n,data)
for name,p in [('broad-reference.plpack',pack),('corrupt.plpack',corrupt),('protocol.json',F/'protocol.json'),('edition.json',R/'downloads/broad-reference/rendered-v2/build.json')]:run(adb+['exec-in','run-as','org.pocketlore.app','sh','-c','cat > files/broad-tests/'+name],'copy-'+name+'.txt',p.read_bytes())
run(adb+['shell','cmd','connectivity','airplane-mode','enable'],'airplane.txt');run(adb+['shell','svc','wifi','disable'],'wifi.txt');run(adb+['shell','svc','data','disable'],'data.txt')
for mode in ['import','restart']:
 run(adb+['shell','am','force-stop','org.pocketlore.app'],'stop-'+mode+'.txt')
 log=run(adb+['shell','am','instrument','-w','-e','mode',mode,'org.pocketlore.app.test/org.pocketlore.app.BroadRepairInstrumentation'],mode+'-instrumentation.txt')
 r=json.loads(run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/broad-tests/'+mode+'.json'],mode+'.json'));assert r['status']=='PASS' and b'INSTRUMENTATION_CODE: -1' in log,{k:v for k,v in r.items() if k not in ['queries','dialogs']}
 for name in [mode+'-source.png',mode+'-license.png']:run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/broad-tests/'+name],name)
run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/pack-library/catalog.json'],'catalog-after.json');model=run(adb+['shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf'],'model-after.txt');assert model==(out/'model-before.txt').read_bytes()
run(adb+['shell','run-as','org.pocketlore.app','du','-ak','files/pack-library','files/broad-tests','files/model.gguf','cache'],'disk.txt')
apk=R/'android/app/build/outputs/apk/debug/app-debug.apk';receipt={'apk':{'sha256':sha(apk),'bytes':apk.stat().st_size},'pack':{'sha256':sha(pack),'bytes':pack.stat().st_size},'protocol_sha256':sha(F/'protocol.json'),'sources':{str(p.relative_to(R)):sha(p) for p in list((R/'android/app/src/main/java/org/pocketlore/app').glob('*.java'))+[F/'BroadRepairInstrumentation.java']},'records':{p.name:sha(p) for p in out.iterdir() if p.suffix in ['.json','.txt','.log','.png']}}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('PASS',out)
