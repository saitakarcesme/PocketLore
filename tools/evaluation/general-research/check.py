#!/usr/bin/env python3
"""Bounded real Android research and deterministic offline receipt/source validation."""
import json,hashlib,pathlib,subprocess,time,uuid,sys,zipfile,copy,importlib.util
ROOT=pathlib.Path(__file__).resolve().parents[3]
HERE=pathlib.Path(__file__).parent
ADB=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5560']
sys.path.insert(0,str(ROOT/'tools/packs/research-primary'))
from build import build,sha
PACK=ROOT/'downloads/general-research/reviewed-reference.plpack'
FINAL=ROOT/'docs/evidence/general-research/candidate.json'
def inputs():
 names=subprocess.check_output(['git','ls-files','android','tools'],cwd=ROOT).decode().splitlines()
 names+=['docs/evidence/general-research/source-review.json']
 return {n:sha((ROOT/n).read_bytes()) for n in names if (ROOT/n).is_file()}
def verify(out,current=True):
 m=json.loads((out/'manifest.json').read_text());files={p.name:p.read_bytes() for p in out.iterdir() if p.is_file()}
 for n,h in m['files'].items():assert sha(files[n])==h,n
 src=json.loads(files['source-inputs.json']);assert sha(files['source-inputs.json'])==m['source_hash'];assert src['inputs']==m['inputs_after']
 if current:assert inputs()==src['inputs'],'Current build inputs differ from tested candidate'
 for name in ['boot','font','rotation','retained']:assert files[name+'-before.txt']==files[name+'-after.txt'],name
 for pkg in ['app','test']:assert files['installed-'+pkg+'.txt'].decode().split()[0]==m['apks'][pkg]['sha256'];assert files['final-'+pkg+'.txt'].decode().split()[0]==m['apks'][pkg]['sha256']
 for mode in ['install','restart']:
  r=json.loads(files[mode+'.json']);assert r['status']=='PASS' and r['run_id']==m['run_id'] and r['source_hash']==m['source_hash'] and r['pack_sha256']==sha(PACK.read_bytes())
  raw=files['runtime-'+mode+'.txt'].decode();assert 'INSTRUMENTATION_CODE: -1' in raw
  receipt=json.loads(next(s.split('=',1)[1] for s in raw.splitlines() if s.startswith('INSTRUMENTATION_RESULT: receipt=')))
  assert receipt['report_sha256']==sha(files[mode+'.json']) and receipt['run_id']==m['run_id'] and receipt['source_hash']==m['source_hash']
  assert json.loads(files['runtime-'+mode+'.txt.command.json'])['returncode']==0
  for screen in r['screens']:assert files[screen+'.png'].startswith(b'\x89PNG') and len(files[screen+'.txt'])>100
  for row in r['outputs']:
   assert not row['generated'];rendered=row['rendered'].encode('utf-16-le')
   for q in row['quotes']:assert sha(q['text'].encode())==q['sha256'];assert rendered[2*q['display_start']:2*q['display_end']].decode('utf-16-le')==q['text']
 r=json.loads(files['install.json']);cases=json.loads((HERE/'cases.json').read_text());assert [x['id'] for x in r['outputs']]==[x['id'] for x in cases]
 for c,row in zip(cases,r['outputs']):assert row['question']==c['question'];assert not c['absent'] or not row['quotes']
 assert json.loads(files['restart.json'])['outputs'][0]['rendered']==r['outputs'][0]['rendered']
 return m

def device():
 out=ROOT/'downloads/general-research'/('run-'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'-'+uuid.uuid4().hex[:6]);out.mkdir();print(out,flush=True)
 def run(cmd,name,timeout=300,data=None):
  start=time.monotonic()
  try:r=subprocess.run([str(x) for x in cmd],cwd=ROOT,input=data,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
  except subprocess.TimeoutExpired as e:(out/name).write_bytes(e.stdout or b'');(out/(name+'.command.json')).write_text(json.dumps({'returncode':-1,'timeout':timeout}));raise
  (out/name).write_bytes(r.stdout);(out/(name+'.command.json')).write_text(json.dumps({'command':list(map(str,cmd)),'returncode':r.returncode,'elapsed_seconds':time.monotonic()-start}));assert r.returncode==0,(name,r.stdout[-1000:]);return r.stdout
 def shell(cmd,name):return run(ADB+['shell',*cmd],name)
 build(PACK);src={'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),'inputs':inputs(),'workers':2,'gradle_heap':'2GiB; not measured total peak','model_env_sha256':sha((ROOT/'tools/answers/model.env').read_bytes())}
 (out/'source-inputs.json').write_text(json.dumps(src,sort_keys=True,indent=2)+'\n');source_hash=sha((out/'source-inputs.json').read_bytes())
 run(['bash','tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',HERE/'source.gradle','-PpocketloreTestRunner=org.pocketlore.app.GeneralResearchInstrumentation'],'build.log')
 apks={}
 for key,suffix in [('app','debug/app-debug.apk'),('test','androidTest/debug/app-debug-androidTest.apk')]:
  p=ROOT/'android/app/build/outputs/apk'/suffix;apks[key]={'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
 def installed(when):
  for key in apks:
   package='org.pocketlore.app'+('.test' if key=='test' else '');path=shell(['pm','path',package],when+'-path-'+key+'.txt').decode().strip().removeprefix('package:');assert path.startswith('/data/app/') and '\n' not in path;shell(['sha256sum',path],when+'-'+key+'.txt')
 def retained(label):
  cmd='for p in files/model.gguf files/model-selection files/model-library files/scale-library files/attachment-assets; do if [ -e "$p" ]; then find "$p" -type f -exec sha256sum {} \\; ; else echo ABSENT:$p; fi; done | sort'
  shell(['run-as','org.pocketlore.app','sh','-c',"'"+cmd+"'"],'retained-'+label+'.txt')
 for cmd,name in [(['getprop','ro.build.version.sdk'],'api.txt'),(['getconf','PAGE_SIZE'],'pages.txt'),(['cat','/proc/sys/kernel/random/boot_id'],'boot-before.txt'),(['settings','get','system','font_scale'],'font-before.txt'),(['settings','get','system','user_rotation'],'rotation-before.txt')]:shell(cmd,name)
 installed('before');retained('before');shell(['run-as','org.pocketlore.app','du','-sb','.'],'logical-before.txt');shell(['run-as','org.pocketlore.app','du','-sk','.'],'allocated-before.txt')
 for key,info in apks.items():run(ADB+['install','--no-incremental','-r',info['path']],'install-'+key+'.txt')
 installed('installed');directory='files/general-research-'+out.name
 shell(['run-as','org.pocketlore.app','mkdir','-p',directory],'mkdir.txt')
 payloads={'valid.plpack':PACK.read_bytes(),'cases.json':(HERE/'cases.json').read_bytes()}
 with zipfile.ZipFile(PACK) as z:original={n:z.read(n) for n in z.namelist()}
 for change in ['corrupt','rights','offset']:
  f=dict(original);m=json.loads(f['manifest.json'])
  if change=='corrupt':f['passages.tsv']+=b'changed'
  elif change=='rights':m['documents'][0]['license_text']=''
  else:m['documents'][0]['passages'][0]['source_utf16_end']+=1
  f['manifest.json']=json.dumps(m).encode();path=out/(change+'.plpack')
  with zipfile.ZipFile(path,'w') as z:
   for n,b in f.items():z.writestr(n,b)
  payloads[path.name]=path.read_bytes()
 for name,b in payloads.items():run(ADB+['shell','run-as','org.pocketlore.app','sh','-c',"'cat > "+directory+'/'+name+"'"],'provision-'+name+'.txt',data=b)
 try:
  for mode in ['install','restart']:
   if mode=='restart':shell(['am','force-stop','org.pocketlore.app'],'cold-stop.txt')
   run(ADB+['shell','am','instrument','-w','-e','run_id',out.name,'-e','source_hash',source_hash,'-e','mode',mode,'org.pocketlore.app.test/org.pocketlore.app.GeneralResearchInstrumentation'],'runtime-'+mode+'.txt',600)
   raw=run(ADB+['exec-out','run-as','org.pocketlore.app','cat',directory+'/'+mode+'.json'],mode+'.json');report=json.loads(raw)
   for screen in report['screens']:
    for ext in ['.png','.txt']:run(ADB+['exec-out','run-as','org.pocketlore.app','cat',directory+'/'+screen+ext],screen+ext)
   assert report['status']=='PASS',report.get('error')
 finally:
  for cmd,name in [(['cat','/proc/sys/kernel/random/boot_id'],'boot-after.txt'),(['settings','get','system','font_scale'],'font-after.txt'),(['settings','get','system','user_rotation'],'rotation-after.txt')]:shell(cmd,name)
  retained('after');shell(['run-as','org.pocketlore.app','du','-sb','.'],'logical-after.txt');shell(['run-as','org.pocketlore.app','du','-sk','.'],'allocated-after.txt');installed('final')
 m={'run_id':out.name,'serial':'emulator-5560','source_hash':source_hash,'inputs_after':inputs(),'apks':apks,'pack_sha256':sha(PACK.read_bytes()),'pack_bytes':PACK.stat().st_size,'files':{p.name:sha(p.read_bytes()) for p in out.iterdir() if p.is_file() and p.suffix!='.plpack'}};(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');verify(out)
 print('Behavior PASS; source-quality review remains separate:',out)
 return out

def audit():
 candidate=json.loads(FINAL.read_text());out=pathlib.Path(candidate['original_run']);m=verify(out)
 assert sha((out/'manifest.json').read_bytes())==candidate['manifest_sha256']
 build(PACK);assert sha(PACK.read_bytes())==m['pack_sha256']
 for info in m['apks'].values():assert sha(pathlib.Path(info['path']).read_bytes())==info['sha256'],'Changed or missing build APK'
 review=json.loads((ROOT/'docs/evidence/general-research/quality-review.json').read_text());r=json.loads((out/'install.json').read_text());assert review['run_id']==m['run_id']
 for row in r['outputs']:
  assessment=review['cases'][row['id']];assert assessment['rendered_sha256']==sha(row['rendered'].encode());assert assessment['unsupported_attributed_claims']==0
 assert sum(x['complete_useful_source_brief'] for x in review['cases'].values())>=12,'Bounded usefulness gate remains unmet'
 import tempfile,shutil
 rejected=[]
 for name in ['missing','corrupt','stale','boot']:
  with tempfile.TemporaryDirectory() as temp:
   target=pathlib.Path(temp)
   for p in out.iterdir():
    if p.is_file() and p.suffix!='.plpack':shutil.copyfile(p,target/p.name)
   if name=='missing':(target/'install.json').unlink()
   elif name=='corrupt':(target/'runtime-install.txt').write_bytes(b'corrupt')
   elif name=='stale':d=json.loads((target/'install.json').read_text());d['run_id']='stale';(target/'install.json').write_text(json.dumps(d))
   else:(target/'boot-after.txt').write_text('changed')
   try:verify(target)
   except (AssertionError,KeyError,ValueError,FileNotFoundError):rejected.append(name)
   else:raise AssertionError('Mutation accepted '+name)
 print(json.dumps({'status':'PASS','run':m['run_id'],'negative_controls':rejected,'generated_successes':0,'scope':'Frozen public development source briefs; no unseen, physical or bulk rights acceptance'}))
if __name__=='__main__':device() if '--device' in sys.argv else audit()
