#!/usr/bin/env python3
import hashlib,json,pathlib,subprocess,sys,time,uuid,shutil
ROOT=pathlib.Path(__file__).resolve().parents[3];HERE=pathlib.Path(__file__).parent
sys.path.insert(0,str(HERE.parent/'reference-expansion'))
from capture import capture
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ADB=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5564']
lease=pathlib.Path('/home/isa/PocketLore-control/runtime/modern-android/builder-lease.json');grant=lease.read_bytes();owner=json.loads(grant)
assert owner['device']=='emulator-5564' and owner['owner']=='canonical-builder'
out=ROOT/'downloads/federated'/('run-'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'-'+uuid.uuid4().hex[:6]);out.mkdir(parents=True);print(out,flush=True)
def run(cmd,name,data=None,timeout=300,allow=False):
 if cmd[:3]==ADB:assert lease.read_bytes()==grant
 raw,r=capture(cmd,out/name,cwd=ROOT,data=data,timeout=timeout)
 if not allow:assert r['returncode']==0 and not r['timed_out'],(name,r,raw[-1000:])
 return raw
def shell(args,name):return run(ADB+['shell',*args],name)
def inputs():return {n:sha(ROOT/n) for n in subprocess.check_output(['git','ls-files','android','tools'],cwd=ROOT).decode().splitlines() if (ROOT/n).is_file()}
def identity(when):
 for key,pkg in [('app','org.pocketlore.app'),('test','org.pocketlore.app.test')]:
  path=shell(['pm','path',pkg],when+'-'+key+'-path.txt').decode().strip().removeprefix('package:');assert path.startswith('/data/app/') and '\n' not in path
  shell(['sha256sum',path],when+'-'+key+'-hash.txt')
 for label,cmd in [('boot',['cat','/proc/sys/kernel/random/boot_id']),('font',['settings','get','system','font_scale']),('rotation',['settings','get','system','user_rotation']),('logical',['run-as','org.pocketlore.app','du','-sb','.']),('allocated',['run-as','org.pocketlore.app','du','-sk','.'])]:shell(cmd,when+'-'+label+'.txt')
 shell(['run-as','org.pocketlore.app','sh','-c',"'for p in files/model.gguf files/model-selection files/page-size-test/model.gguf; do if [ -f \"$p\" ]; then sha256sum \"$p\"; else echo ABSENT:$p; fi; done'"],when+'-models.txt')
status='FAIL'
try:
 src={'commit':subprocess.check_output(['git','rev-parse','HEAD']).decode().strip(),'inputs':inputs()};(out/'source.json').write_text(json.dumps(src,sort_keys=True,indent=2)+'\n');source=sha(out/'source.json')
 run(['bash','tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',str(HERE/'source.gradle'),'-PpocketloreTestRunner=org.pocketlore.app.FederatedInstrumentation'],'build.log')
 apks={};(out/'binaries').mkdir()
 for key,path in [('app','debug/app-debug.apk'),('test','androidTest/debug/app-debug-androidTest.apk')]:
  target=out/'binaries'/pathlib.Path(path).name;shutil.copyfile(ROOT/'android/app/build/outputs/apk'/path,target);apks[key]={'path':str(target),'sha256':sha(target),'bytes':target.stat().st_size}
 assert shell(['getprop','ro.build.version.sdk'],'api.txt').strip()==b'37';assert shell(['getconf','PAGE_SIZE'],'pages.txt').strip()==b'16384';identity('before')
 for key,info in apks.items():
  remote='/data/local/tmp/federated-'+out.name+'-'+key+'.apk';run(ADB+['push',info['path'],remote],'push-'+key+'.txt');assert shell(['sha256sum',remote],'stage-'+key+'.txt').decode().split()[0]==info['sha256'];shell(['pm','install','-r',remote],'install-'+key+'.txt');shell(['rm',remote],'remove-stage-'+key+'.txt')
 identity('installed');d='files/federated-'+out.name;shell(['run-as','org.pocketlore.app','mkdir','-p',d],'mkdir.txt')
 protocol=json.loads((HERE/'development.json').read_text());assets={'development.json':HERE/'development.json'}
 for name,s in zip(['expanded.plpack','science.plpack'],protocol['sources']):
  p=ROOT/s['path'];assert sha(p)==s['sha256'];assets[name]=p
 for name,p in assets.items():run(ADB+['shell','run-as','org.pocketlore.app','sh','-c',"'cat > "+d+'/'+name+"'"],'copy-'+name+'.txt',p.read_bytes())
 provider='files/reference-expansion-'+out.name;shell(['run-as','org.pocketlore.app.test','mkdir','-p',provider],'provider-dir.txt');run(ADB+['shell','run-as','org.pocketlore.app.test','sh','-c',"'cat > "+provider+"/science.plpack'"],'provider-science.txt',assets['science.plpack'].read_bytes())
 for mode in ['install','restart']:
  if mode=='restart':shell(['am','force-stop','org.pocketlore.app'],'cold-stop.txt')
  run(ADB+['shell','am','instrument','-w','-e','run_id',out.name,'-e','source_hash',source,'-e','mode',mode,'org.pocketlore.app.test/org.pocketlore.app.FederatedInstrumentation'],mode+'-raw.txt',timeout=300,allow=True)
  raw=run(ADB+['exec-out','run-as','org.pocketlore.app','cat',d+'/'+mode+'.json'],mode+'.json');report=json.loads(raw)
  for screen in report['screens']:
   for ext in ['.png','.txt']:run(ADB+['exec-out','run-as','org.pocketlore.app','cat',d+'/'+screen+ext],screen+ext)
  assert json.loads((out/(mode+'-raw.txt.command.json')).read_text())['returncode']==0
  assert report['status']=='PASS',report.get('error')
 identity('final');assert inputs()==src['inputs'];(out/'manifest.json').write_text(json.dumps({'run_id':out.name,'source_hash':source,'apks':apks,'files':{p.name:sha(p) for p in out.iterdir() if p.is_file()}},indent=2)+'\n');status='PASS'
finally:
 (out/'seal.json').write_text(json.dumps({'status':status,'files':{p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='seal.json'}},indent=2)+'\n')
