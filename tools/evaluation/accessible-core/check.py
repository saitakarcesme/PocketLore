"""Fresh5560 manual-comparison feature checks; no model execution or downloads."""
import hashlib,json,pathlib,subprocess,time,uuid,copy
ROOT=pathlib.Path(__file__).resolve().parents[3]
ADB=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5560']
def sha(b):return hashlib.sha256(b).hexdigest()
def sources():
 names=subprocess.check_output(['git','ls-files','android','tools'],cwd=ROOT).decode().splitlines()
 return {n:sha((ROOT/n).read_bytes()) for n in names if (ROOT/n).is_file()}
def verify(d):
 m=json.loads(d['manifest.json']);src=json.loads(d['source-inputs.json']);assert src['sources']==m['sources_after']
 assert sha(d['source-inputs.json'])==m['source_hash']
 for n in ['boot','font','rotation','auto-rotation']:assert d[n+'-before.txt']==d[n+'-after.txt'],n
 assert d['retained-before.txt']==d['retained-after.txt']
 for n,h in m['files'].items():assert sha(d[n])==h,n
 r=json.loads(d['report.json']);assert r['status']=='PASS' and r['run_id']==m['run_id'] and r['source_manifest_sha256']==m['source_hash']
 raw=d['runtime.txt'].decode();assert 'INSTRUMENTATION_CODE: -1' in raw
 assert json.loads(next(s.split('=',1)[1] for s in raw.splitlines() if s.startswith('INSTRUMENTATION_RESULT: accessible_receipt=')))==r
 assert json.loads(d['runtime.txt.command.json'])['returncode']==0
 for pkg,info in m['apks'].items():
  for when in ['installed','final']:assert d[when+'-'+pkg+'.txt'].decode().split()[0]==info['sha256']
 assert len(r['states'])==72 and len(set(r['states']))==72
 assert all(x['ratio']>=4.5 for x in r['contrast'])
 for name in r['states']:
  assert d[name+'.png'].startswith(b'\x89PNG') and len(d[name+'.png'])>10000
  assert len(d[name+'.txt'])>100
 assert {'original_records_retained','MainActivity_preferences_restored','SourceReaderActivity_preferences_restored','rotation_unfrozen'}<=set(r['checks'])
 return m

def main():
 id=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'-'+uuid.uuid4().hex[:8];out=ROOT/'downloads/accessible-core'/id;out.mkdir(parents=True);print(out,flush=True)
 def run(cmd,name,timeout=240):
  try:p=subprocess.run([str(x) for x in cmd],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
  except subprocess.TimeoutExpired as e:(out/name).write_bytes(e.stdout or b'');(out/(name+'.command.json')).write_text(json.dumps({'returncode':-1,'timeout':timeout}));raise
  (out/name).write_bytes(p.stdout);(out/(name+'.command.json')).write_text(json.dumps({'command':[str(x) for x in cmd],'returncode':p.returncode}));assert p.returncode==0,(name,out);return p.stdout
 def shell(cmd,name):return run(ADB+['shell',*cmd],name)
 fixture=ROOT/'docs/evidence/accessible-core/fixtures.json';assert sha(fixture.read_bytes())=='6879c894690345d7765dcd8a80c89c6921ec66143e30978d8a5ed65fc792ab3a'
 src={'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),'sources':sources(),'fixture_sha256':sha(fixture.read_bytes()),'gradle_workers':2,'gradle_heap':'2GiB','sdk_jar_sha256':sha(pathlib.Path('/home/isa/Android/atlas-toolchain/sdk/platforms/android-35/android.jar').read_bytes())}
 (out/'source-inputs.json').write_text(json.dumps(src,sort_keys=True,indent=2)+'\n');source_hash=sha((out/'source-inputs.json').read_bytes())
 run(['bash','tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',ROOT/'tools/evaluation/accessible-core/source.gradle','-PpocketloreTestRunner=org.pocketlore.app.AccessibleInstrumentation'],'build.log',300);assert sources()==src['sources']
 apks={}
 for pkg,path in [('app','debug/app-debug.apk'),('test','androidTest/debug/app-debug-androidTest.apk')]:
  p=ROOT/'android/app/build/outputs/apk'/path;apks[pkg]={'path':str(p),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
 (out/'apks.json').write_text(json.dumps(apks,indent=2))
 assert run(ADB+['get-state'],'state.txt').strip()==b'device'
 for cmd,name in [(['getprop','ro.build.version.sdk'],'sdk.txt'),(['getconf','PAGE_SIZE'],'pages.txt'),(['cat','/proc/sys/kernel/random/boot_id'],'boot-before.txt'),(['settings','get','system','font_scale'],'font-before.txt'),(['settings','get','system','user_rotation'],'rotation-before.txt'),(['settings','get','system','accelerometer_rotation'],'auto-rotation-before.txt')]:shell(cmd,name)
 def installed(pkg,label):
  path=shell(['pm','path','org.pocketlore.app'+('.test' if pkg=='test' else '')],label+'-path-'+pkg+'.txt').decode().strip().removeprefix('package:');assert path.startswith('/data/app/') and '\n' not in path;shell(['sha256sum',path],label+'-'+pkg+'.txt')
 def retain(label):
  command="for p in files/model.gguf files/model-selection files/model-library files/pack-library files/scale-library files/attachment-assets; do if [ -e \\\"$p\\\" ]; then find \\\"$p\\\" -type f -exec sha256sum {} \\\\; ; else echo ABSENT:$p; fi; done | sort"
  command=command.replace('\\"','"').replace('\\\\;','\\;')
  shell(['run-as','org.pocketlore.app','sh','-c',"'"+command+"'"],'retained-'+label+'.txt')
 def disk(label):
  for flags,kind in [('sb','logical'),('sk','allocated')]:shell(['run-as','org.pocketlore.app','du','-'+flags,'.'],kind+'-'+label+'.txt')
 for pkg in apks:installed(pkg,'before')
 retain('before');disk('before')
 for pkg,item in apks.items():run(ADB+['install','--no-incremental','-r',item['path']],'install-'+pkg+'.txt');installed(pkg,'installed')
 try:
  raw=run(ADB+['shell','am','instrument','-r','-w','-e','run_id',id,'-e','source_manifest_sha256',source_hash,'org.pocketlore.app.test/org.pocketlore.app.AccessibleInstrumentation'],'runtime.txt',600)
  report=json.loads(next(line.split('=',1)[1] for line in raw.decode().splitlines() if line.startswith('INSTRUMENTATION_RESULT: accessible_receipt=')));(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
  for name in report['states']:
   for ext in ['.png','.txt']:run(ADB+['exec-out','run-as','org.pocketlore.app','cat','files/accessible-check-'+id+'/'+name+ext],name+ext)
 finally:
  shell(['cat','/proc/sys/kernel/random/boot_id'],'boot-after.txt')
  for setting,name in [('font_scale','font'),('user_rotation','rotation'),('accelerometer_rotation','auto-rotation')]:
   observed=shell(['settings','get','system',setting],name+'-observed-after.txt');original=(out/(name+'-before.txt')).read_bytes().strip().decode()
   if observed.strip().decode()!=original:
    command=['settings','delete','system',setting] if original=='null' else ['settings','put','system',setting,original]
    shell(command,name+'-recovery.txt')
   shell(['settings','get','system',setting],name+'-after.txt')
  retain('after');disk('after')
 for pkg in apks:installed(pkg,'final')
 m={'run_id':id,'serial':'emulator-5560','source_hash':source_hash,'sources_after':sources(),'apks':apks,'files':{p.name:sha(p.read_bytes()) for p in out.iterdir() if p.is_file()}}
 (out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');d={p.name:p.read_bytes() for p in out.iterdir() if p.is_file()};verify(d);negative=[]
 for kind in ['missing','corrupt','stale','changed-test']:
  bad=dict(d)
  if kind=='missing':del bad['runtime.txt']
  elif kind=='corrupt':bad['report.json']+=b'x'
  elif kind=='stale':r=json.loads(bad['report.json']);r['run_id']='stale';bad['report.json']=json.dumps(r).encode()
  else:bad['installed-test.txt']=b'0'*64
  try:verify(bad)
  except (AssertionError,KeyError,ValueError):negative.append(kind)
  else:raise AssertionError(kind)
 (out/'negative-controls.json').write_text(json.dumps(negative));print(json.dumps({'status':'PASS','output':str(out)}))
if __name__=='__main__':main()
