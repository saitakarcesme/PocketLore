"""Current canonical UI behavior, data retention and exact installed identity."""
import hashlib,json,os,subprocess,time,pathlib,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[3];ADB=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5560'];PKG='org.pocketlore.app'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 stamp=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime());out=ROOT/'downloads/product-ui/runs'/stamp;out.mkdir(parents=True,exist_ok=False)
 def run(cmd,name,data=None,timeout=400):
  r=subprocess.run([str(x) for x in cmd],cwd=ROOT,input=data,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout);(out/name).write_bytes(r.stdout);assert r.returncode==0,(name,out);return r.stdout
 assert run(ADB+['get-state'],'state.txt').strip()==b'device';run(ADB+['shell','getprop'],'properties.txt')
 run(['python3','tools/evaluation/check_ui_scope.py'],'scope.json')
 before=run(ADB+['shell','run-as',PKG,'sha256sum','files/model.gguf','files/pack-library/catalog.json','files/attachment-assets/tessdata/eng.traineddata','files/attachment-assets/ggml-tiny.en.bin'],'assets-before.txt')
 run(['bash','tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',ROOT/'tools/evaluation/product-ui/source.gradle','-PpocketloreTestRunner=org.pocketlore.app.ProductUiInstrumentation'],'build.log')
 apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk';test=ROOT/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk'
 artifacts={p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in [apk,test]};run(['python3','tools/evaluation/verify_16kb_artifacts.py',apk],'native.json')
 old=json.loads((ROOT/'docs/evidence/attachments/race-fix/artifacts.json').read_text())['payloads']
 with zipfile.ZipFile(apk) as z:
  for name,pin in old.items():
   if name.endswith('.so'):assert hashlib.sha256(z.read(name)).hexdigest()==pin['sha256'],name+' changed native runtime'
 for p in [apk,test]:run(ADB+['install','-r',p],'install-'+p.name+'.txt')
 font=run(ADB+['shell','settings','get','system','font_scale'],'font-before.txt').decode().strip()
 reports=[]
 try:
  for label,scale in [('default','1.0'),('large','2.0')]:
   run(ADB+['shell','settings','put','system','font_scale',scale],'font-'+label+'.txt');mode=stamp+'-'+label
   log=run(ADB+['shell','am','instrument','-w','-e','mode',mode,PKG+'.test/'+PKG+'.ProductUiInstrumentation'],'runtime-'+label+'.txt',timeout=300)
   if b'Process crashed' in log:raise AssertionError('Instrumented process crashed: '+str(out))
   raw=run(ADB+['exec-out','run-as',PKG,'cat','files/product-ui-'+mode+'/report.json'],'report-'+label+'.json');report=json.loads(raw)
   names=run(ADB+['shell','run-as',PKG,'ls','files/product-ui-'+mode],'files-'+label+'.txt').decode().splitlines();folder=out/label;folder.mkdir()
   for name in names:
    if name.endswith(('.png','.txt','.md')):run(ADB+['exec-out','run-as',PKG,'cat','files/product-ui-'+mode+'/'+name],label+'/'+name)
   assert report['status']=='PASS',(out,report.get('error'));assert report['activity_font_scale']==float(scale)
   required=['Actual research persisted','Actual bundled source catalog'] # await labels are not assertion records; assert actual behavioral checks below.
   assert {'Research test invoked no model','Source identity retained','Bookmark persisted','Export retains source, date and note','Share provider rejects writes','Draft restored without relabeling previous answer','Unavailable brief contains no source quotation','Accepted attachment route opens'}.issubset(report['checks'])
   reports.append({'mode':label,'sha256':sha(out/('report-'+label+'.json')),'checks':len(report['checks'])})
  run(ADB+['shell','am','force-stop',PKG],'cold-stop.txt');mode='restart-'+stamp
  run(ADB+['shell','am','instrument','-w','-e','mode',mode,PKG+'.test/'+PKG+'.ProductUiInstrumentation'],'cold-runtime.txt');cold=json.loads(run(ADB+['exec-out','run-as',PKG,'cat','files/product-ui-'+mode+'/report.json'],'cold-report.json'));assert cold['status']=='PASS'
 finally:
  run(ADB+['shell','settings','delete','system','font_scale'] if font=='null' else ADB+['shell','settings','put','system','font_scale',font],'font-restored.txt')
 after=run(ADB+['shell','run-as',PKG,'sha256sum','files/model.gguf','files/pack-library/catalog.json','files/attachment-assets/tessdata/eng.traineddata','files/attachment-assets/ggml-tiny.en.bin'],'assets-after.txt');assert before==after
 path=run(ADB+['shell','pm','path',PKG],'installed-path.txt').decode().strip().removeprefix('package:');installed=run(ADB+['shell','sha256sum',path],'installed-hash.txt').decode().split()[0];assert installed==artifacts['app-debug.apk']['sha256']
 receipt={'status':'PASS','serial':'emulator-5560','artifacts':artifacts,'reports':reports,'cold_restart':True,'saved_assets_unchanged':True,'native_payloads_unchanged':True,'configured_gradle':'2 workers /2GiB heap; not measured total peak','output':str(out)}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
