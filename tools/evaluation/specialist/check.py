#!/usr/bin/env python3
import pathlib,subprocess,json,hashlib,time,sys,zipfile,copy,tempfile,shutil
ROOT=pathlib.Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools/packs/specialist'));from build import build,LOCK,CACHE,sha
ADB=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5562']
def verify_report(report,run_id,pack_hash):
 assert report.get('run_id')==run_id,'Stale or unbound device report'
 assert report['status']=='PASS',report.get('error')
 assert report['pack_sha256']==pack_hash

def record_command(out,cmd,name,timeout=360,input=None):
 start=time.monotonic()
 try:r=subprocess.run(list(map(str,cmd)),cwd=ROOT,input=input,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
 except subprocess.TimeoutExpired as e:
  (out/name).write_bytes(e.stdout or b'');(out/(name+'.command.json')).write_text(json.dumps({'timeout_seconds':timeout,'elapsed_seconds':time.monotonic()-start})+'\n');raise
 (out/name).write_bytes(r.stdout);(out/(name+'.command.json')).write_text(json.dumps({'returncode':r.returncode,'elapsed_seconds':time.monotonic()-start})+'\n');assert r.returncode==0,(name,r.returncode,r.stdout[-2000:]);return r.stdout

def main():
 out=ROOT/'downloads/specialist'/time.strftime('run-%Y%m%dT%H%M%SZ',time.gmtime());out.mkdir(parents=True)
 def run(cmd,name,timeout=360,input=None):return record_command(out,cmd,name,timeout,input)
 run([sys.executable,'-m','unittest','discover','-s','tools/evaluation/specialist','-p','test_receipts.py'],'receipt-tests.txt')
 pack=out/'valid.plpack';m=build(pack);repeat=out/'repeat.plpack';build(repeat);assert pack.read_bytes()==repeat.read_bytes();assert len(m['documents'])==8
 with zipfile.ZipFile(pack) as z:files={n:z.read(n) for n in z.namelist()}
 rows={r.split('\t')[0]:r.split('\t')[5] for r in files['passages.tsv'].decode().split('\n') if r};lock=json.loads(LOCK.read_text())
 for d,item in zip(m['documents'],lock['documents']):
  raw=(CACHE/(item['repo']+'-'+item['path'].replace('/','_'))).read_bytes();source=raw.decode().encode('utf-16-le');joined=''
  for p in d['passages']:
   span=source[p['source_utf16_start']*2:p['source_utf16_end']*2].decode('utf-16-le');restored=rows[p['id']].replace('\u2028','\n').replace('\u2409','\t');assert span==restored and sha(span.encode())==p['source_span_sha256'];joined+=restored
  assert joined.encode()==raw,'Formula/code or source text lost'
 negatives=[]
 with tempfile.TemporaryDirectory(dir=out) as temp:
  cache=pathlib.Path(temp)/'raw';shutil.copytree(CACHE,cache);target=cache/'EIPs-EIPS_eip-196.md';original=target.read_bytes()
  for change in ['missing-source','changed-source','missing-license']:
   target.write_bytes(original)
   if change=='missing-source':target.unlink()
   elif change=='changed-source':target.write_bytes(original+b'changed')
   else:(cache/'EIPs-LICENSE.md').unlink()
   try:build(pathlib.Path(temp)/'bad.plpack',cache=cache)
   except (ValueError,FileNotFoundError):negatives.append(change)
   else:raise AssertionError(change+' admitted')
 for name in ['corrupt','rights','span']:
  altered=dict(files);doc=copy.deepcopy(m)
  if name=='corrupt':altered['passages.tsv']+=b'corrupt'
  elif name=='rights':doc['documents'][0]['license']=''
  else:doc['documents'][0]['passages'][0]['source_utf16_end']+=1
  altered['manifest.json']=json.dumps(doc).encode()
  with zipfile.ZipFile(out/(name+'.plpack'),'w') as z:
   for n,b in altered.items():z.writestr(n,b)
 (out/'host.json').write_text(json.dumps({'status':'PASS','deterministic':True,'source_roundtrips':len(m['documents']),'negative_checks':negatives,'manifest':m},indent=2)+'\n')
 run(['bash','tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',ROOT/'tools/evaluation/specialist/source.gradle','-PpocketloreTestRunner=org.pocketlore.app.SpecialistInstrumentation'],'build.log')
 before=run(ADB+['shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf','files/scale-library/catalog.json'],'before.txt');run(ADB+['shell','getprop'],'properties.txt');run(ADB+['shell','df','-k','/data'],'disk-before.txt')
 for name in ['debug/app-debug.apk','androidTest/debug/app-debug-androidTest.apk']:run(ADB+['install','-r',ROOT/'android/app/build/outputs/apk'/name],'install-'+pathlib.Path(name).name+'.txt')
 run(ADB+['shell','run-as','org.pocketlore.app','mkdir','-p','files/specialist-tests'],'mkdir.txt')
 for path in [pack,*[out/(n+'.plpack') for n in ['corrupt','rights','span']],ROOT/'tools/evaluation/specialist/protocol.json']:
  run(ADB+['shell','run-as','org.pocketlore.app','sh','-c',"'cat > files/specialist-tests/"+path.name+"'"],'provision-'+path.name+'.txt',input=path.read_bytes())
 for mode in ['install','restart']:
  run(ADB+['shell','am','force-stop','org.pocketlore.app'],'stop-'+mode+'.txt')
  try:run(ADB+['shell','am','instrument','-w','-e','mode',mode,'-e','run_id',out.name,'org.pocketlore.app.test/org.pocketlore.app.SpecialistInstrumentation'],'runtime-'+mode+'.txt',600)
  except (AssertionError,subprocess.TimeoutExpired):
   # Preserve diagnostic bytes even after transport failure; never turn these into a pass.
   diagnostic=subprocess.run(ADB+['exec-out','run-as','org.pocketlore.app','cat','files/specialist-tests/'+mode+'.json'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
   (out/('failed-device-'+mode+'.json')).write_bytes(diagnostic.stdout)
   (out/('failed-device-'+mode+'-capture.json')).write_text(json.dumps({'returncode':diagnostic.returncode,'expected_run_id':out.name,'diagnostic_only':True})+'\n')
   raise
  raw=run(ADB+['exec-out','run-as','org.pocketlore.app','cat','files/specialist-tests/'+mode+'.json'],mode+'.json');r=json.loads(raw);verify_report(r,out.name,sha(pack.read_bytes()))
 after=run(ADB+['shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf','files/scale-library/catalog.json'],'after.txt');assert before==after
 package=run(ADB+['shell','dumpsys','package','org.pocketlore.app'],'package.txt');assert b'android.permission.INTERNET' not in package
 apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk';path=run(ADB+['shell','pm','path','org.pocketlore.app'],'installed.txt').decode().strip().removeprefix('package:');installed=run(ADB+['shell','sha256sum',path],'installed-hash.txt').decode().split()[0];assert installed==sha(apk.read_bytes())
 receipt={'run_id':out.name,'status':'PASS','apk_sha256':installed,'apk_bytes':apk.stat().st_size,'pack_sha256':sha(pack.read_bytes()),'pack_bytes':pack.stat().st_size,'environment':'API35 x86_64 emulator-5562; full existing 31-shard catalog preserved; no model inference or phone qualification','files':{p.name:sha(p.read_bytes()) for p in out.iterdir() if p.is_file() and p.suffix!='.plpack'}}
 # Actual successful report bytes must not validate for another or missing run identity.
 for altered in [dict(r,run_id='different-run'),{k:v for k,v in r.items() if k!='run_id'},dict(r,pack_sha256='0'*64)]:
  try:verify_report(altered,out.name,sha(pack.read_bytes()))
  except AssertionError:pass
  else:raise AssertionError('Stale/unbound/changed report admitted')
 (out/'binding-controls.json').write_text(json.dumps({'different_run':'rejected','missing_run':'rejected','changed_pack':'rejected'})+'\n')
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':'PASS','output':str(out)}))
if __name__=='__main__':main()
