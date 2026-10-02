"""Explicit5560 bounded meter observation, with immutable inputs and transport identities."""
import copy,hashlib,json,pathlib,subprocess,time,uuid
ROOT=pathlib.Path(__file__).resolve().parents[3]
ADB=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5560']
def sha(b):return hashlib.sha256(b).hexdigest()
def sources():
 names=subprocess.check_output(['git','ls-files','android','tools'],cwd=ROOT).decode().splitlines()
 return {n:sha((ROOT/n).read_bytes()) for n in names if (ROOT/n).is_file()}
def verify(data):
 m=json.loads(data['manifest.json']);r=json.loads(data['receipt.json']);inputs=json.loads(data['source-inputs.json'])
 assert r['status']=='PASS' and r['run_id']==m['run_id']
 assert r['source_manifest_sha256']==sha(data['source-inputs.json'])==m['source_manifest_sha256']
 assert inputs['sources']==m['sources_after_build']
 assert m['serial']=='emulator-5560' and int(data['sdk.txt'])==r['sdk'] and int(data['pages.txt'])==r['page_size']
 assert data['boot-before.txt']==data['boot-after.txt'] and data['font-before.txt']==data['font-after.txt']
 assert data['retained-before.txt']==data['retained-after.txt']
 for name,pin in m['files'].items():assert sha(data[name])==pin,name
 for name,raw in data.items():
  if name.endswith('.command.json'):assert json.loads(raw)['returncode']==0,name
 assert b'INSTRUMENTATION_CODE: -1' in data['runtime.txt'] and b'Process crashed' not in data['runtime.txt']
 assert json.loads(next(line.split('=',1)[1] for line in data['runtime.txt'].decode().splitlines() if line.startswith('INSTRUMENTATION_RESULT: storage_receipt=')))==r
 for pkg,identity in m['apks'].items():
  for phase in ['installed','final']:assert data[phase+'-'+pkg+'.txt'].decode().split()[0]==identity['sha256']
 for phase in ['before','during','hardlink','after']:
  sample=r[phase];seen=set();logical=allocated=covered=0
  for row in sample['stat_rows']:
   dev,ino,size,blocks=map(int,row.split());key=(dev,ino)
   if key in seen:continue
   seen.add(key);logical+=size;allocated+=blocks*512;covered+=max(size,blocks*512)
  assert sample['meter']==sample['covered']==covered and sample['logical']==logical and sample['allocated']==allocated
 assert r['during']['meter']>r['before']['meter']
 required={'actual_storage_application_started','startup_zero_reservations','during_copy_reservation_held','copy_success_release','unknown_symlink_denied','concurrent_one_admitted','concurrent_release','cancel_cleanup_release','failure_cleanup_release','same_process_retry','personal_import_export_startup','personal_release','optional_failure_release','owned_fixture_removed','final_zero_reservations'}
 assert required<=set(r['checks'])
 return r

def main():
 run_id=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'-'+uuid.uuid4().hex[:8];out=ROOT/'downloads/android-storage-meter'/run_id;out.mkdir(parents=True);print(out,flush=True)
 def run(cmd,name,timeout=240):
  try:p=subprocess.run([str(x) for x in cmd],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
  except subprocess.TimeoutExpired as e:
   (out/name).write_bytes(e.stdout or b'');(out/(name+'.command.json')).write_text(json.dumps({'returncode':-1,'timeout':timeout}));raise
  (out/name).write_bytes(p.stdout);(out/(name+'.command.json')).write_text(json.dumps({'returncode':p.returncode,'command':[str(x) for x in cmd]}));assert p.returncode==0,(name,out);return p.stdout
 def shell(cmd,name):return run(ADB+['shell',*cmd],name)
 source={'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),'sources':sources(),'gradle_workers':2,'gradle_heap':'2GiB','tool_inputs':{}}
 for path in ['/home/isa/Android/atlas-toolchain/jdk/release','/home/isa/Android/atlas-toolchain/sdk/platforms/android-35/android.jar']:
  source['tool_inputs'][path]=sha(pathlib.Path(path).read_bytes())
 (out/'source-inputs.json').write_text(json.dumps(source,sort_keys=True,indent=2)+'\n');source_hash=sha((out/'source-inputs.json').read_bytes())
 run(['bash','tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',ROOT/'tools/evaluation/android-storage-meter/source.gradle','-PpocketloreTestRunner=org.pocketlore.app.StorageMeterInstrumentation'],'build.log',300)
 assert sources()==source['sources'],'Build changed frozen source inputs'
 apks={}
 for pkg,relative in [('app','debug/app-debug.apk'),('test','androidTest/debug/app-debug-androidTest.apk')]:
  p=ROOT/'android/app/build/outputs/apk'/relative;apks[pkg]={'path':str(p),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
 (out/'build-artifacts.json').write_text(json.dumps(apks,indent=2))
 assert run(ADB+['get-state'],'state.txt').strip()==b'device'
 for cmd,name in [(['getprop','ro.build.version.sdk'],'sdk.txt'),(['getconf','PAGE_SIZE'],'pages.txt'),(['cat','/proc/sys/kernel/random/boot_id'],'boot-before.txt'),(['settings','get','system','font_scale'],'font-before.txt')]:shell(cmd,name)
 def installed(pkg,label):
  package='org.pocketlore.app'+('.test' if pkg=='test' else '')
  path=shell(['pm','path',package],label+'-path-'+pkg+'.txt').decode().strip().removeprefix('package:');assert path.startswith('/data/app/') and '\n' not in path
  shell(['sha256sum',path],label+'-'+pkg+'.txt')
 for pkg in apks:installed(pkg,'before')
 def retain(label):
  # Hash persistent owned files only; no content or model bytes leave Android.
  shell(['run-as','org.pocketlore.app','sh','-c',"'find files shared_prefs databases -type f -exec sha256sum {} \\; 2>/dev/null | sort'"],'retained-'+label+'.txt')
 retain('before')
 for pkg,item in apks.items():run(ADB+['install','--no-incremental','-r',item['path']],'install-'+pkg+'.txt');installed(pkg,'installed')
 raw=run(ADB+['shell','am','instrument','-r','-w','-e','run_id',run_id,'-e','source_manifest_sha256',source_hash,'org.pocketlore.app.test/org.pocketlore.app.StorageMeterInstrumentation'],'runtime.txt')
 receipt=json.loads(next(line.split('=',1)[1] for line in raw.decode().splitlines() if line.startswith('INSTRUMENTATION_RESULT: storage_receipt=')))
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 shell(['cat','/proc/sys/kernel/random/boot_id'],'boot-after.txt');shell(['settings','get','system','font_scale'],'font-after.txt');retain('after')
 for pkg in apks:installed(pkg,'final')
 shell(['run-as','org.pocketlore.app','du','-sk','.'],'allocated-after.txt');shell(['df','-k','/data'],'df-after.txt')
 m={'run_id':run_id,'serial':'emulator-5560','apks':apks,'source_manifest_sha256':source_hash,'sources_after_build':sources(),'files':{p.name:sha(p.read_bytes()) for p in out.iterdir() if p.is_file()}}
 (out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');data={p.name:p.read_bytes() for p in out.iterdir() if p.is_file()};verify(data)
 negative=[]
 for kind in ['missing','corrupt','stale','test-identity']:
  d=dict(data)
  if kind=='missing':del d['runtime.txt']
  elif kind=='corrupt':d['receipt.json']+=b'x'
  elif kind=='stale':
   r=copy.deepcopy(receipt);r['run_id']='stale';d['receipt.json']=json.dumps(r).encode()
  else:d['installed-test.txt']=b'0'*64
  try:verify(d)
  except (AssertionError,KeyError,ValueError):negative.append(kind)
  else:raise AssertionError('Invalid evidence accepted')
 (out/'negative-controls.json').write_text(json.dumps(negative));print(json.dumps({'status':'PASS','output':str(out)}))
if __name__=='__main__':main()
