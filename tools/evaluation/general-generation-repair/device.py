from pathlib import Path
import sys,subprocess,json,hashlib,time,uuid,shutil
R=Path(__file__).resolve().parents[3];F=Path(__file__).parent;sys.path.insert(0,str(F.parent/'reference-expansion'));from capture import capture
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
lease=Path('/home/isa/PocketLore-control/runtime/modern-android/builder-lease.json');grant=lease.read_bytes();assert json.loads(grant)['owner']=='canonical-builder'
a=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5564'];out=R/'downloads/general-generation-repair'/('run-'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'-'+uuid.uuid4().hex[:6]);out.mkdir(parents=True);print(out,flush=True)
def run(cmd,name,timeout=300):
 assert lease.read_bytes()==grant
 raw,receipt=capture(cmd,out/name,cwd=R,timeout=timeout);assert receipt['returncode']==0,(name,raw[-500:]);return raw
status='FAIL'
try:
 inputs={p:sha(R/p) for p in subprocess.check_output(['git','ls-files','android','tools'],cwd=R,text=True).splitlines() if (R/p).is_file()}
 (out/'source.json').write_text(json.dumps(inputs,sort_keys=True,indent=2));source=sha(out/'source.json')
 run(['bash','tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',str(F/'source.gradle'),'-PpocketloreTestRunner=org.pocketlore.app.GeneralIntegrationInstrumentation'],'build.log')
 for label,cmd in [('boot',['cat','/proc/sys/kernel/random/boot_id']),('font',['settings','get','system','font_scale']),('page',['getconf','PAGE_SIZE']),('api',['getprop','ro.build.version.sdk']),('catalog',['run-as','org.pocketlore.app','sha256sum','files/pack-library/catalog.json'])]:run(a+['shell',*cmd],'before-'+label+'.txt')
 apks={};(out/'binaries').mkdir()
 for key,name,pkg in [('app','debug/app-debug.apk','org.pocketlore.app'),('test','androidTest/debug/app-debug-androidTest.apk','org.pocketlore.app.test')]:
  f=R/'android/app/build/outputs/apk'/name;copy=out/'binaries'/f.name;shutil.copy2(f,copy);apks[key]={'sha256':sha(copy),'path':str(copy)}
  run(a+['install','-r',str(copy)],'install-'+key+'.txt');path=run(a+['shell','pm','path',pkg],key+'-path.txt').decode().strip().removeprefix('package:');raw=run(a+['shell','sha256sum',path],key+'-hash.txt');assert raw.decode().split()[0]==apks[key]['sha256']
 run(a+['shell','am','instrument','-w','-r','-e','run_id',out.name,'-e','source_hash',source,'org.pocketlore.app.test/org.pocketlore.app.GeneralIntegrationInstrumentation'],'instrumentation.txt')
 raw=run(a+['exec-out','run-as','org.pocketlore.app','cat','files/general-generation-repair/'+out.name+'/report.json'],'report.json');assert json.loads(raw)['status']=='PASS' and json.loads(raw)['source_hash']==source
 run(a+['exec-out','run-as','org.pocketlore.app','cat','files/general-generation-repair/'+out.name+'/screen.png'],'screen.png')
 for label,cmd in [('boot',['cat','/proc/sys/kernel/random/boot_id']),('font',['settings','get','system','font_scale']),('catalog',['run-as','org.pocketlore.app','sha256sum','files/pack-library/catalog.json'])]:
  run(a+['shell',*cmd],'final-'+label+'.txt');assert (out/('final-'+label+'.txt')).read_bytes()==(out/('before-'+label+'.txt')).read_bytes()
 assert all(sha(R/p)==h for p,h in inputs.items());status='PASS'
finally:(out/'seal.json').write_text(json.dumps({'status':status,'files':{p.name:sha(p) for p in out.iterdir() if p.is_file()}},indent=2)+'\n')
