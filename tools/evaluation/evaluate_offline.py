#!/usr/bin/env python3
"""Destructive only to PocketLore on emulator-5560: archive, uninstall, fresh offline cycles."""
from pathlib import Path
import datetime,hashlib,json,os,shutil,subprocess,tarfile,time,zipfile
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'downloads/offline'/datetime.datetime.now(datetime.timezone.utc).strftime('run-%Y%m%dT%H%M%SZ');OUT.mkdir(parents=True)
print(OUT,flush=True)
tc=Path(os.environ.get('POCKETLORE_TOOLCHAIN','/home/isa/Android/atlas-toolchain'));adb=[tc/'sdk/platform-tools/adb','-s','emulator-5560'];checks=[]
def run(args,name,input=None,allow_fail=False):
 p=subprocess.run(list(map(str,args)),input=input,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(OUT/name).parent.mkdir(parents=True,exist_ok=True);(OUT/name).write_bytes(p.stdout)
 if p.returncode and not allow_fail:print(p.stdout.decode(errors='replace'));p.check_returncode()
 return p.stdout
def shell(args,name,allow_fail=False):return run(adb+['shell',*args],name,allow_fail=allow_fail)
def record(phase):
 p=OUT/'phase.tmp';p.write_text(json.dumps({'phase':phase,'checks':checks}));p.replace(OUT/'phase.json')
def radio(tag):
 values={k:shell(['settings','get','global',k],f'{tag}-{k}.txt').decode().strip() for k in ['airplane_mode_on','wifi_on','mobile_data']}
 assert values=={'airplane_mode_on':'1','wifi_on':'0','mobile_data':'0'},values
 return values
def instrument(mode,label):
 r=shell(['am','instrument','-w','-e','mode',mode,'org.pocketlore.app.test/org.pocketlore.app.OfflineInstrumentation'],label+'-instrumentation.txt')
 raw=run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/offline-result.json'],label+'-result.json');report=json.loads(raw)
 assert b'INSTRUMENTATION_CODE: -1' in r and report['status']=='PASS',report
 expected=6 if mode=='fresh' else 12
 assert len(report['checks'])==expected,(expected,report['checks'])
 radio(label);return report
def install(label):
 for i,p in enumerate(apks):run(adb+['install',p],f'{label}-install-{i}.txt')
def remove(label):
 for package in ['org.pocketlore.app.test','org.pocketlore.app']:
  installed=shell(['pm','path',package],label+'-path-'+package+'.txt',allow_fail=True).strip()
  if installed:assert b'Success' in run(adb+['uninstall',package],label+'-uninstall-'+package+'.txt')
 assert not shell(['pm','path','org.pocketlore.app'],label+'-absent.txt',allow_fail=True).strip()
def model_ui(label):
 run(['python3',ROOT/'tools/answers/ui-smoke.py','--adb',adb[0],'--serial','emulator-5560','--model',model,'--out',OUT/label],label+'.log')
 assert json.loads((OUT/label/'result.json').read_text())['status']=='pass'
def pack_ui(label):
 run(['python3',ROOT/'tools/packs/ui_smoke.py','--adb',adb[0],'--serial','emulator-5560','--pack',pack,'--bad',bad,'--out',OUT/label],label+'.log')
 assert json.loads((OUT/label/'result.json').read_text())['result']=='PASS'
assert shell(['getprop','sys.boot_completed'],'boot.txt').strip()==b'1'
assert shell(['getprop','ro.product.cpu.abi'],'abi.txt').strip()==b'x86_64'
shell(['getprop','ro.build.fingerprint'],'fingerprint.txt')
model=ROOT/'downloads/answers/model/qwen2.5-0.5b-instruct-q4_k_m.gguf';pack=ROOT/'downloads/packs/english-reference.plpack'
assert hashlib.sha256(model.read_bytes()).hexdigest()=='74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db'
assert hashlib.sha256(pack.read_bytes()).hexdigest()=='567e9bbbaab896826809ec20f81ae1c4b3f421b011931edae0989d28cfce10ea'
bad=OUT/'corrupt.plpack'
with zipfile.ZipFile(pack) as z,zipfile.ZipFile(bad,'w',zipfile.ZIP_DEFLATED) as o:
 for n in z.namelist():
  b=z.read(n)
  if n=='passages.tsv':b=b.replace(b'water',b'wrong',1)
  o.writestr(n,b)
run(['bash',ROOT/'tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-PpocketloreTestRunner=org.pocketlore.app.OfflineInstrumentation'],'build.log')
apks=[ROOT/'android/app/build/outputs/apk/debug/app-debug.apk',ROOT/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk']
for p in apks:shutil.copyfile(p,OUT/p.name)
permissions=run([tc/'sdk/build-tools/35.0.0/aapt','dump','permissions',apks[0]],'permissions.txt').decode()
assert not any(p in permissions for p in ['android.permission.INTERNET','android.permission.ACCESS_NETWORK_STATE','android.permission.CHANGE_NETWORK_STATE','android.permission.ACCESS_WIFI_STATE'])
deps=run(['bash',ROOT/'tools/android-build.sh',':app:dependencies','--configuration','debugRuntimeClasspath'],'runtime-dependencies.txt').decode()
assert 'No dependencies' in deps and not any(p in deps.lower() for p in ['play-services','firebase','okhttp','retrofit'])
for package in ['com.google.android.gms','com.android.vending']:
 assert not shell(['pm','list','packages',package],'package-'+package+'.txt').strip()
checks.append('APK permissions/runtime dependencies and no installed Play Services');record('artifact-audit')
# Preserve old emulator app files before either authorized uninstall. Backup is never committed.
if shell(['pm','path','org.pocketlore.app'],'original-package.txt',allow_fail=True).strip():
 shell(['am','force-stop','org.pocketlore.app'],'stop-before-backup.txt')
 shell(['run-as','org.pocketlore.app','du','-ak','files','cache','code_cache'],'original-files.txt')
 archive=OUT/'original-app-data.tar'
 with archive.open('wb') as out, (OUT/'backup-stderr.txt').open('wb') as err:
  subprocess.run(adb+['exec-out','run-as','org.pocketlore.app','tar','-cf','-','files','cache','code_cache'],stdout=out,stderr=err,check=True)
 with tarfile.open(archive) as tar:
  entries=tar.getmembers();assert entries and all(not e.name.startswith('/') and '..' not in Path(e.name).parts for e in entries)
 with archive.open('rb') as f:backup_hash=hashlib.file_digest(f,'sha256').hexdigest()
 (OUT/'backup-identity.json').write_text(json.dumps({'bytes':archive.stat().st_size,'sha256':backup_hash,'members':len(entries),'scope':'Original PocketLore app files/cache/code_cache; retained ignored, not restored automatically'},indent=2)+'\n')
 checks.append('original app data archived and tar verified');record('backup-complete')
for key in ['airplane_mode_on','wifi_on','mobile_data']:shell(['settings','get','global',key],'original-'+key+'.txt')
shell(['cmd','connectivity','airplane-mode','enable'],'airplane-enable.txt');shell(['svc','wifi','disable'],'wifi-disable.txt');shell(['svc','data','disable'],'data-disable.txt');radio('offline-start')
for cycle in [1,2]:
 label=f'cycle-{cycle}';record(label+'-before-uninstall');remove(label);install(label);record(label+'-fresh-installed')
 instrument('fresh',label+'-fresh');checks.append(label+' verified empty install and no-model fallback')
 model_ui(label+'-model-ui');checks.append(label+' local SAF model import/hash/restart/source inspection')
 if cycle==1:
  instrument('loaded',label+'-loaded');checks.append('real offline answer invocation, abstention, cancel and recreation')
  run(['python3',ROOT/'tools/evaluation/offline_corrupt_model_ui.py','--adb',adb[0],'--out',OUT/'corrupt-model-ui'],'corrupt-model-ui.log');checks.append('corrupt GGUF rejection and import-dialog cancellation retain saved hash')
 pack_ui(label+'-pack-ui');checks.append(label+' SAF pack import/restart/corrupt rejection/NPS inspection');radio(label+'-complete');record(label+'-complete')
summary={'status':'PASS','environment':'Existing AOSP x86_64 emulator, fresh app installs; not physical Android/GrapheneOS','checks':checks,'artifacts':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [*apks,model,pack]},'final_state':'Second clean installation with locally imported model/pack; airplane mode on, Wi-Fi/mobile data off; old app data archived, not restored','limitations':'Offline execution and control behavior, not research-quality acceptance; no packet capture or physical-radio test'}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');record('complete');print(json.dumps(summary,indent=2))
