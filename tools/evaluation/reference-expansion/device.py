#!/usr/bin/env python3
"""Explicit task480/5564 lease required; never chooses another device or starts services."""
import json,hashlib,pathlib,subprocess,time,uuid,sys,zipfile,shutil
ROOT=pathlib.Path(__file__).resolve().parents[3];HERE=pathlib.Path(__file__).parent
ADB=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5564']
sys.path.insert(0,str(ROOT/'tools/packs/reference-expansion'))
from build import build,sha
from verify import verify_run
PACK=ROOT/'downloads/reference-expansion/reference-expansion.plpack'
CURRENT_OUT=None
def inputs():
 names=subprocess.check_output(['git','ls-files','android','tools'],cwd=ROOT).decode().splitlines()
 return {n:sha((ROOT/n).read_bytes()) for n in names if (ROOT/n).is_file()}
def device(lease_path):
 lease=json.loads(pathlib.Path(lease_path).read_text());assert lease.get("task_id") in {"480-expand-reviewed-reference-coverage-20261002a","480-expand-reviewed-reference-coverage-20261002a-repair-1"} and lease.get("serial")=="emulator-5564" and lease.get("exclusive") is True,"A new coordinator-issued exclusive task480/5564 lease is required"
 assert lease.get("expires_epoch",0)>time.time(),"Lease has expired"
 out=ROOT/'downloads/reference-expansion'/('run-'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'-'+uuid.uuid4().hex[:6]);out.mkdir();globals()["CURRENT_OUT"]=out;print(out,flush=True)
 def run(cmd,name,timeout=300,data=None):
  start=time.monotonic()
  if list(map(str,cmd[:3]))==ADB:assert lease['expires_epoch']>time.time(),'Exclusive lease expired; do not continue device commands'
  try:r=subprocess.run([str(x) for x in cmd],cwd=ROOT,input=data,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
  except subprocess.TimeoutExpired as e:(out/name).write_bytes(e.stdout or b'');(out/(name+'.command.json')).write_text(json.dumps({'returncode':-1,'timeout':timeout}));raise
  (out/name).write_bytes(r.stdout);(out/(name+'.command.json')).write_text(json.dumps({'command':list(map(str,cmd)),'returncode':r.returncode,'elapsed_seconds':time.monotonic()-start}));assert r.returncode==0,(name,r.stdout[-1000:]);return r.stdout
 def shell(cmd,name):return run(ADB+['shell',*cmd],name)
 build(PACK);src={'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),'inputs':inputs(),'workers':2,'gradle_heap':'2GiB; not measured total peak','model_env_sha256':sha((ROOT/'tools/answers/model.env').read_bytes())}
 (out/'source-inputs.json').write_text(json.dumps(src,sort_keys=True,indent=2)+'\n');source_hash=sha((out/'source-inputs.json').read_bytes())
 run(['bash','tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',HERE/'source.gradle','-PpocketloreTestRunner=org.pocketlore.app.ReferenceExpansionInstrumentation'],'build.log')
 apks={}
 for key,suffix in [('app','debug/app-debug.apk'),('test','androidTest/debug/app-debug-androidTest.apk')]:
  p=ROOT/'android/app/build/outputs/apk'/suffix;binary=out/'binaries';binary.mkdir(exist_ok=True);saved=binary/p.name;shutil.copyfile(p,saved);apks[key]={'path':str(saved),'bytes':saved.stat().st_size,'sha256':sha(saved.read_bytes())}
 def installed(when):
  for key in apks:
   package='org.pocketlore.app'+('.test' if key=='test' else '');path=shell(['pm','path',package],when+'-path-'+key+'.txt').decode().strip().removeprefix('package:');assert path.startswith('/data/app/') and '\n' not in path;shell(['sha256sum',path],when+'-'+key+'.txt')
 def retained(label):
  cmd='for p in files/model.gguf files/model-selection files/model-library files/scale-library files/attachment-assets files/page-size-test/model.gguf; do if [ -e "$p" ]; then find "$p" -type f -exec sha256sum {} \\; ; else echo ABSENT:$p; fi; done | sort'
  shell(['run-as','org.pocketlore.app','sh','-c',"'"+cmd+"'"],'retained-'+label+'.txt')
 for cmd,name in [(['getprop','ro.build.version.sdk'],'api.txt'),(['getconf','PAGE_SIZE'],'pages.txt'),(['cat','/proc/sys/kernel/random/boot_id'],'boot-before.txt'),(['settings','get','system','font_scale'],'font-before.txt'),(['settings','get','system','user_rotation'],'rotation-before.txt')]:shell(cmd,name)
 assert (out/'api.txt').read_text().strip()=='37' and (out/'pages.txt').read_text().strip()=='16384'
 (out/'lease.json').write_text(json.dumps(lease,sort_keys=True)+'\n')
 installed('before');retained('before');shell(['run-as','org.pocketlore.app','du','-sb','.'],'logical-before.txt');shell(['run-as','org.pocketlore.app','du','-sk','.'],'allocated-before.txt');shell(['run-as','org.pocketlore.app.test','du','-sb','.'],'provider-logical-before.txt');shell(['run-as','org.pocketlore.app.test','du','-sk','.'],'provider-allocated-before.txt')
 for key,info in apks.items():
  owned='/data/local/tmp/reference480-'+out.name+'-'+key+'.apk'
  run(ADB+['push',info['path'],owned],'stage-'+key+'.txt');assert shell(['sha256sum',owned],'stage-'+key+'-hash.txt').decode().split()[0]==info['sha256']
  shell(['pm','install','-r',owned],'install-'+key+'.txt');shell(['rm',owned],'remove-owned-stage-'+key+'.txt')
 installed('installed');directory='files/reference-expansion-'+out.name
 shell(['run-as','org.pocketlore.app','mkdir','-p',directory],'mkdir.txt')
 payloads={'valid.plpack':PACK.read_bytes(),'cases.json':json.dumps(json.loads((HERE/'development.json').read_text())['cases']).encode()}
 with zipfile.ZipFile(PACK) as z:original={n:z.read(n) for n in z.namelist()}
 for change in ['corrupt','rights','offset','identity','license','source-text','fractional-offset','missing-binding','trailing-text']:
  f=dict(original);m=json.loads(f['manifest.json'])
  if change=='corrupt':f['passages.tsv']+=b'changed'
  elif change=='rights':m['documents'][0]['rights_status']='needs-evidence'
  elif change=='offset':m['documents'][0]['passages'][0]['source_utf16_start']+=1
  elif change=='identity':m['documents'][0]['source_identity']='wrong-source'
  elif change=='license':m['licenses']['cc-by-sa-4']['text']=''
  elif change=='source-text':m['documents'][0]['source_text']+='changed'
  elif change=='fractional-offset':m['documents'][0]['passages'][0]['source_utf16_end']+=0.5
  elif change=='missing-binding':del m['documents'][0]['passages'][0]['source_utf16_start']
  elif change=='trailing-text':
   m['documents'][0]['source_text']+=' unbound tail';m['documents'][0]['source_text_sha256']=sha(m['documents'][0]['source_text'].encode())
  f['manifest.json']=json.dumps(m).encode();path=out/(change+'.plpack')
  with zipfile.ZipFile(path,'w') as z:
   for n,b in f.items():z.writestr(n,b)
  payloads[path.name]=path.read_bytes()
 for name,b in payloads.items():run(ADB+['shell','run-as','org.pocketlore.app','sh','-c',"'cat > "+directory+'/'+name+"'"],'provision-'+name+'.txt',data=b)
 shell(['run-as','org.pocketlore.app.test','mkdir','-p',directory],'provider-mkdir.txt')
 run(ADB+['shell','run-as','org.pocketlore.app.test','sh','-c',"'cat > "+directory+"/valid.plpack'"],'provider-copy.txt',data=PACK.read_bytes())
 shell(['run-as','org.pocketlore.app','du','-sb','.'],'logical-staged.txt');shell(['run-as','org.pocketlore.app','du','-sk','.'],'allocated-staged.txt')
 shell(['run-as','org.pocketlore.app.test','du','-sb','.'],'provider-logical-staged.txt');shell(['run-as','org.pocketlore.app.test','du','-sk','.'],'provider-allocated-staged.txt')
 try:
  for mode in ['install','restart']:
   if mode=='restart':shell(['am','force-stop','org.pocketlore.app'],'cold-stop.txt')
   run(ADB+['shell','am','instrument','-w','-e','run_id',out.name,'-e','source_hash',source_hash,'-e','mode',mode,'org.pocketlore.app.test/org.pocketlore.app.ReferenceExpansionInstrumentation'],'runtime-'+mode+'.txt',600)
   raw=run(ADB+['exec-out','run-as','org.pocketlore.app','cat',directory+'/'+mode+'.json'],mode+'.json');report=json.loads(raw)
   for screen in report['screens']:
    for ext in ['.png','.txt']:run(ADB+['exec-out','run-as','org.pocketlore.app','cat',directory+'/'+screen+ext],screen+ext)
   assert report['status']=='PASS',report.get('error')
 finally:
  for cmd,name in [(['cat','/proc/sys/kernel/random/boot_id'],'boot-after.txt'),(['settings','get','system','font_scale'],'font-after.txt'),(['settings','get','system','user_rotation'],'rotation-after.txt')]:shell(cmd,name)
  retained('after');shell(['run-as','org.pocketlore.app','du','-sb','.'],'logical-after.txt');shell(['run-as','org.pocketlore.app','du','-sk','.'],'allocated-after.txt');installed('final');shell(['run-as','org.pocketlore.app.test','du','-sb','.'],'provider-logical-after.txt');shell(['run-as','org.pocketlore.app.test','du','-sk','.'],'provider-allocated-after.txt')
 m={'run_id':out.name,'serial':'emulator-5564','source_hash':source_hash,'inputs_after':inputs(),'apks':apks,'pack_sha256':sha(PACK.read_bytes()),'pack_bytes':PACK.stat().st_size,'files':{p.name:sha(p.read_bytes()) for p in out.iterdir() if p.is_file() and p.suffix!='.plpack'}};(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');verify_run(out)
 print('Behavior PASS; source-quality review remains separate:',out)
 return out

if __name__=="__main__":
 if len(sys.argv)!=2:raise SystemExit("Supply the new coordinator-issued task480 exclusive5564 lease JSON; no implicit device access")
 status='FAIL'
 try:device(sys.argv[1]);status='PASS'
 finally:
  if CURRENT_OUT is not None:
   seal={'status':status,'files':{p.name:sha(p.read_bytes()) for p in CURRENT_OUT.iterdir() if p.is_file() and p.name!='invocation-seal.json'},'classification':'Retain this invocation even on failure; no previous run may replace it'}
   (CURRENT_OUT/'invocation-seal.json').write_text(json.dumps(seal,indent=2)+'\n')
