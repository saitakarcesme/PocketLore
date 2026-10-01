#!/usr/bin/env python3
"""Authorized project-fixture-only archive and fresh offline installation on existing emulator."""
from pathlib import Path
import json,hashlib,subprocess,datetime,tarfile,os,argparse
R=Path(__file__).resolve().parents[3];F=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--resume',type=Path);args=parser.parse_args()
out=args.resume.resolve() if args.resume else R/'downloads/release-broad'/datetime.datetime.now(datetime.timezone.utc).strftime('run-%Y%m%dT%H%M%S%fZ')
out.mkdir(parents=True,exist_ok=True);print(out,flush=True)
tc=Path(os.environ.get('POCKETLORE_TOOLCHAIN','/home/isa/Android/atlas-toolchain'));adb=[tc/'sdk/platform-tools/adb','-s','emulator-5560']
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def run(args,name,input=None,optional=False):
 p=subprocess.run(list(map(str,args)),input=input,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=900);(out/name).write_bytes(p.stdout)
 if p.returncode and not optional:raise RuntimeError(str(out/name))
 return p.stdout
def shell(args,name,**kw):return run(adb+['shell']+args,name,**kw)
protocol=json.loads((F/'protocol.json').read_text());assets=[R/'downloads/answers/model/qwen2.5-0.5b-instruct-q4_k_m.gguf',R/'downloads/packs/english-reference.plpack',R/'downloads/science/science-supplement-2026-10-01-v1.plpack',R/'downloads/broad-reference/rendered-v2/broad-reference.plpack']
for p,k in zip(assets,['model_sha256','reference_sha256','science_sha256','broad_sha256']):assert sha(p)==protocol['expected'][k]
if not args.resume:
 assert shell(['getprop','sys.boot_completed'],'boot.txt').strip()==b'1';assert shell(['getprop','ro.product.cpu.abi'],'abi.txt').strip()==b'x86_64';shell(['getprop','ro.build.fingerprint'],'fingerprint.txt')
 run(['bash',R/'tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',F/'source.gradle','-PpocketloreTestRunner=org.pocketlore.app.ReleaseBroadInstrumentation'],'build.log')
 apk=R/'android/app/build/outputs/apk/debug/app-debug.apk';test=R/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk'
 shell(['am','force-stop','org.pocketlore.app'],'stop-before-backup.txt')
 with (out/'original-app-data.tar').open('wb') as f,(out/'backup-stderr.txt').open('wb') as err:subprocess.run(list(map(str,adb+['exec-out','run-as','org.pocketlore.app','tar','-cf','-','files','cache','code_cache'])),stdout=f,stderr=err,check=True)
 with tarfile.open(out/'original-app-data.tar') as t:members=t.getmembers();assert members and all(not x.name.startswith('/') and '..' not in Path(x.name).parts for x in members)
 (out/'backup-receipt.json').write_text(json.dumps({'bytes':(out/'original-app-data.tar').stat().st_size,'sha256':sha(out/'original-app-data.tar'),'members':len(members),'scope':'PocketLore fixture files/cache only; ignored archive; not restored'},indent=2)+'\n')
 for pkg in ['org.pocketlore.app.test','org.pocketlore.app']:run(adb+['uninstall',pkg],'uninstall-'+pkg+'.txt')
 assert not shell(['pm','path','org.pocketlore.app'],'absent-package.txt',optional=True).strip()
 for p in [apk,test]:run(adb+['install',p],'install-'+p.name+'.txt')
 shell(['cmd','connectivity','airplane-mode','enable'],'airplane-enable.txt');shell(['svc','wifi','disable'],'wifi-disable.txt');shell(['svc','data','disable'],'data-disable.txt')
def instrument(mode):
 shell(['am','force-stop','org.pocketlore.app'],'stop-'+mode+'.txt')
 log=shell(['am','instrument','-w','-e','mode',mode,'org.pocketlore.app.test/org.pocketlore.app.ReleaseBroadInstrumentation'],mode+'-instrumentation.txt')
 raw=run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/release-tests/'+mode+'.json'],mode+'.json');result=json.loads(raw)
 assert b'INSTRUMENTATION_CODE: -1' in log and result['status']=='PASS',result
 for d in result['dialogs']:run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/release-tests/'+d['file']],mode+'-'+d['file'])
 return result
apk=R/'android/app/build/outputs/apk/debug/app-debug.apk'
fresh=json.loads((out/'fresh.json').read_text()) if args.resume else instrument('fresh')
assert fresh['empty_model_and_catalog']
if not (out/'model-ui/result.json').exists():run(['python3',F/'import_model_ui.py','--adb',adb[0],'--serial','emulator-5560','--model',assets[0],'--out',out/'model-ui','--import-only'],'model-ui.log')
for label,p in zip(['reference','science','broad'],assets[1:]):
 if not (out/(label+'-ui/result.json')).exists():run(['python3',F/'import_pack_ui.py','--adb',adb[0],'--serial','emulator-5560','--pack',p,'--out',out/(label+'-ui')],label+'-ui.log')
combined=instrument('combined');disabled=instrument('disabled');enabled=instrument('enabled')
radio={k:shell(['settings','get','global',k],k+'.txt').decode().strip() for k in ['airplane_mode_on','wifi_on','mobile_data']};assert radio=={'airplane_mode_on':'1','wifi_on':'0','mobile_data':'0'}
for pkg in ['com.google.android.gms','com.android.vending']:assert not shell(['pm','list','packages',pkg],pkg+'.txt').strip()
perms=run([tc/'sdk/build-tools/35.0.0/aapt','dump','permissions',apk],'permissions.txt');assert b'uses-permission:' not in perms
deps=run(['bash',R/'tools/android-build.sh',':app:dependencies','--configuration','debugRuntimeClasspath'],'runtime-dependencies.txt');assert b'No dependencies' in deps
saved=shell(['run-as','org.pocketlore.app','sha256sum','files/model.gguf'],'saved-model.txt').decode().split()[0];assert saved==protocol['expected']['model_sha256']
cat=json.loads(run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/pack-library/catalog.json'],'catalog.json'));assert len(cat['collections'])==3 and all(e['active'] for e in cat['collections'])
for e in cat['collections']:assert shell(['run-as','org.pocketlore.app','sha256sum','files/pack-library/'+e['sha256']+'.plpack'],'pack-'+e['sha256']+'.txt').decode().split()[0]==e['sha256']
summary={'schema':3,'status':'PASS','environment':'Existing AOSP x86_64 emulator; fresh offline multi-pack installation, not physical acceptance','protocol_sha256':sha(F/'protocol.json'),'artifacts':{str(p.relative_to(R)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in [apk,*assets]},'radio':radio,'saved_model_sha256':saved,'catalog':cat,'fresh_empty':fresh['empty_model_and_catalog'],'distinct_processes':len({r['pid'] for r in [fresh,combined,disabled,enabled]})==4,'final_collections':enabled['collections'],'final_documents':enabled['documents'],'final_passages':enabled['passages'],'limitations':'One fresh install, actual SAF imports and source buttons; support assessed separately. No physical, clean-machine, production signing or natural OOM claim.'}
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
