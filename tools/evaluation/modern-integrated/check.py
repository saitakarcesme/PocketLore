"""Explicit API37 subset compatibility; no model generation or shared serial defaults."""
import copy,hashlib,json,pathlib,subprocess,sys,time,uuid
ROOT=pathlib.Path(__file__).resolve().parents[3]
ADB=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5564']
PKG='org.pocketlore.app'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def validate(report,run_id):
 assert report['run_id']==run_id and report['status']=='PASS','Stale or failed report'
def verify(out):
 m=json.loads((out/'manifest.json').read_text());assert m['serial']=='emulator-5564' and m['sdk']==37 and m['page_size']==16384
 for name,pin in m['files'].items():assert sha(out/name)==pin,'Missing or changed '+name
 for lane in m['reports']:
  r=json.loads((out/lane['file']).read_text());validate(r,m['run_id'])
  transport=(out/lane['transport']).read_text();assert 'INSTRUMENTATION_CODE: -1' in transport and 'Process crashed' not in transport
  c=json.loads((out/(lane['transport']+'.command.json')).read_text());assert c['returncode']==0
 assert (out/'installed-hash.txt').read_text().split()[0]==m['apk_sha256']
 assert (out/'assets-before.txt').read_bytes()==(out/'assets-after.txt').read_bytes(),'Saved asset identity changed'
 modern=json.loads((out/'native-cards-recognition/report.json').read_text());assert modern['generation_performed'] is False and modern['page_size']==16384 and modern['sdk']==37
 assert modern['model_sha256']=='74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db' and len(modern['reviewed_cards'])==3
 assert {'Precancelled load rejected','Cancel reset close reload releases native state','Missing speech does not start microphone','Missing OCR fails explicitly before image recognition'}.issubset(modern['checks'])
 for label,scale in [('default',1.0),('large',2.0)]:
  r=json.loads((out/f'{label}/report.json').read_text());assert r['sdk']==37 and r['activity_font_scale']==scale
  assert {'Research test invoked no model','Draft restored without relabeling previous answer','Retry destination matches exact source bytes','Activity destruction closes blocked writer','Source opening and note persistence survive blocked destination','Android Back closes keyboard without leaving Research'}.issubset(r['checks'])
  assert (out/f'{label}/research-keyboard.png').stat().st_size>10000 and 'EditText' in (out/f'{label}/research-keyboard-accessibility.txt').read_text()
 d=json.loads((out/'documents/results.json').read_text());assert d['api']==37
 assert {'live_catalog_restored_exactly','personal_library_return_does_not_infer','actual_source_dialog_offsets_owner_exact_text','blocked_export_cancelled'}.issubset(d['checks'])
 assert 'pageSizeCompat=0' in (out/'package-after.txt').read_text()
 assert 'App compatibility' not in (out/'ui.xml').read_text()
 assert 'android.permission.INTERNET' not in (out/'permissions.txt').read_text()
 return m

def main():
 if len(sys.argv)>1:verify(pathlib.Path(sys.argv[1]));print('Verified modern immutable receipts');return
 run_id=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'-'+uuid.uuid4().hex[:8];out=ROOT/'downloads/modern-integrated'/run_id;out.mkdir(parents=True);print(out,flush=True);reports=[]
 def run(cmd,name,data=None,timeout=400):
  p=out/name;p.parent.mkdir(parents=True,exist_ok=True);start=time.monotonic()
  try:r=subprocess.run(list(map(str,cmd)),cwd=ROOT,input=data,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
  except subprocess.TimeoutExpired as e:
   p.write_bytes(e.stdout or b'');pathlib.Path(str(p)+'.command.json').write_text(json.dumps({'timeout_seconds':timeout,'elapsed_seconds':time.monotonic()-start}));raise
  p.write_bytes(r.stdout);pathlib.Path(str(p)+'.command.json').write_text(json.dumps({'returncode':r.returncode,'elapsed_seconds':time.monotonic()-start}));assert r.returncode==0,(name,r.returncode,out);return r.stdout
 def shell(args,name):return run(ADB+['shell']+args,name)
 def capture_assets(label):
  # Exact initial paths: absent values stay explicit, not a setup instruction.
  command="for p in files/model.gguf files/model-selection files/pack-library/catalog.json files/scale-library/catalog.json files/page-size-test/model.gguf files/attachment-assets/tessdata/eng.traineddata files/attachment-assets/ggml-tiny.en.bin; do if [ -f \"$p\" ]; then sha256sum \"$p\"; else echo ABSENT:$p; fi; done"
  shell(['run-as',PKG,'sh','-c',"'"+command+"'"],'assets-'+label+'.txt')
  shell(['run-as',PKG,'du','-sk','.'],'allocated-'+label+'.txt');shell(['run-as',PKG,'du','-sb','.'],'logical-'+label+'.txt');shell(['df','-k','/data'],'df-'+label+'.txt')
 def instrument(cls,folder,remote,extra=()):
  log=folder+'/runtime.txt';failure=None
  try:
   value=run(ADB+['shell','am','instrument','-w','-e','run_id',run_id,*extra,PKG+'.test/'+PKG+'.'+cls],log)
   assert b'INSTRUMENTATION_CODE: -1' in value and b'Process crashed' not in value,'Instrumentation completion missing'
  except Exception as e:failure=e
  # Diagnostics are retained on transport failure; never substitute a recovered PASS.
  try:
   names=shell(['run-as',PKG,'ls',remote],folder+'/files.txt').decode().splitlines()
   for name in names:
    if name.endswith(('.json','.png','.txt','.md')):run(ADB+['exec-out','run-as',PKG,'cat',remote+'/'+name],folder+'/'+name)
  finally:
   if failure:raise failure
  filename='report.json'
  if cls=='DocumentsInstrumentation':filename='restart.json' if 'restart' in extra else 'results.json'
  validate(json.loads((out/folder/filename).read_text()),run_id);reports.append({'file':folder+'/'+filename,'transport':log})
 assert run(ADB+['get-state'],'state.txt').strip()==b'device'
 assert shell(['getprop','sys.boot_completed'],'boot.txt').strip()==b'1'
 assert shell(['getprop','ro.build.version.sdk'],'sdk.txt').strip()==b'37'
 assert shell(['getconf','PAGE_SIZE'],'pages.txt').strip()==b'16384'
 shell(['getprop'],'properties.txt');shell(['dumpsys','package',PKG],'package-before.txt');capture_assets('before')
 run(['bash','tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',ROOT/'tools/evaluation/modern-integrated/source.gradle','-PpocketloreTestRunner=org.pocketlore.app.ModernIntegratedInstrumentation'],'build.log')
 apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk';test=ROOT/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk';apk_hash=sha(apk)
 run(['python3','tools/evaluation/verify_16kb_artifacts.py',apk],'native.json')
 run(['/home/isa/Android/atlas-toolchain/sdk/build-tools/35.0.0/zipalign','-c','-P','16','-v','4',apk],'zipalign.txt')
 run(['/home/isa/Android/atlas-toolchain/sdk/build-tools/35.0.0/aapt','dump','permissions',apk],'permissions.txt')
 for p in [apk,test]:run(ADB+['install','--no-incremental','-r',p],'install-'+p.name+'.txt')
 font=shell(['settings','get','system','font_scale'],'font-before.txt').decode().strip()
 try:
  instrument('ModernIntegratedInstrumentation','native-cards-recognition','files/modern-'+run_id)
  for label,scale in [('default','1.0'),('large','2.0')]:
   shell(['settings','put','system','font_scale',scale],'font-'+label+'.txt');mode=run_id+'-'+label
   instrument('ProductUiInstrumentation',label,'files/product-ui-'+mode,['-e','mode',mode])
  shell(['am','force-stop',PKG],'cold-stop.txt');mode='restart-'+run_id
  instrument('ProductUiInstrumentation','cold','files/product-ui-'+mode,['-e','mode',mode])
 finally:shell(['settings','delete','system','font_scale'] if font=='null' else ['settings','put','system','font_scale',font],'font-restored.txt')
 fixtures=ROOT/'downloads/documents-fixtures';spec=json.loads((ROOT/'docs/evidence/documents/fixtures.json').read_text())
 for package,folder in [(PKG,'files/documents-input'),(PKG+'.test','files')]:
  shell(['run-as',package,'mkdir','-p',folder],'mkdir-'+package+'.txt')
  for name,pin in spec['files'].items():
   p=fixtures/name;assert sha(p)==pin['sha256'] and p.stat().st_size==pin['bytes'];run(ADB+['shell','run-as',package,'sh','-c',"'cat > "+folder+'/'+name+"'"],'fixture-'+package+'-'+name+'.txt',p.read_bytes())
 directory='documents-test-'+run_id
 instrument('DocumentsInstrumentation','documents','files/'+directory,['-e','directory',directory])
 shell(['am','force-stop',PKG],'documents-cold-stop.txt')
 instrument('DocumentsInstrumentation','documents-cold','files/'+directory,['-e','directory',directory,'-e','phase','restart'])
 capture_assets('after');shell(['dumpsys','package',PKG],'package-after.txt');shell(['dumpsys','meminfo',PKG],'memory-after.txt')
 path=shell(['pm','path',PKG],'installed-path.txt').decode().strip().removeprefix('package:');shell(['sha256sum',path],'installed-hash.txt')
 shell(['am','start','-W','-n',PKG+'/.MainActivity'],'final-launch.txt');shell(['uiautomator','dump','/sdcard/modern-integrated.xml'],'ui-dump.txt');run(ADB+['exec-out','cat','/sdcard/modern-integrated.xml'],'ui.xml');run(ADB+['exec-out','screencap','-p'],'final.png')
 m={'serial':'emulator-5564','sdk':37,'page_size':16384,'run_id':run_id,'apk_sha256':apk_hash,'apk_bytes':apk.stat().st_size,'test_sha256':sha(test),'reports':reports,'files':{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}}
 (out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');verify(out)
 # Mutate actual retained artifacts; restoration always preserves original evidence.
 victim=out/reports[0]['file'];original=victim.read_bytes();negative=[]
 try:
  for kind in ['missing','changed','stale']:
   if kind=='missing':victim.unlink()
   elif kind=='changed':victim.write_bytes(original+b'x')
   else:
    r=json.loads(original);r['run_id']='stale';victim.write_text(json.dumps(r))
   try:verify(out)
   except (AssertionError,FileNotFoundError):negative.append(kind)
   else:raise AssertionError('Corrupt receipt accepted')
   victim.write_bytes(original)
  r=json.loads(original);r['run_id']='stale'
  try:validate(r,run_id)
  except AssertionError:negative.append('stale-even-with-rehashed-artifact')
  else:raise AssertionError('Stale run accepted')
 finally:victim.write_bytes(original)
 (out/'negative-controls.json').write_text(json.dumps(negative));verify(out);print(json.dumps({'status':'PASS','output':str(out),'apk_sha256':apk_hash}),flush=True)
if __name__=='__main__':main()
