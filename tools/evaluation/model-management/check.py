"""Serial real Android import/selection; exact assets and behavioral receipts, no network."""
import hashlib,json,pathlib,subprocess,time,sys
ROOT=pathlib.Path(__file__).resolve().parents[3]
ADB=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5560']
PKG='org.pocketlore.app'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def verify(folder):
 r=json.loads((folder/'receipt.json').read_text())
 for name,h in r['hashes'].items():assert sha(folder/name)==h,name
 for mode in ['import','select']:
  report=json.loads((folder/(mode+'.json')).read_text());assert report['status']=='PASS',report
 assert json.loads((folder/'select.json').read_text())['unverified_token_output'] is not None
 return r

def main():
 resume=len(sys.argv)>1
 out=pathlib.Path(sys.argv[1]) if resume else ROOT/'downloads/model-management'/time.strftime('%Y%m%dT%H%M%SZ',time.gmtime());out.mkdir(parents=True,exist_ok=resume)
 def run(cmd,name,timeout=360):
  p=subprocess.run(list(map(str,cmd)),cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout);(out/name).write_bytes(p.stdout);assert p.returncode==0,(name,p.stdout[-2000:].decode(errors='replace'));return p.stdout
 def stream(path,package,destination,label):
  with path.open('rb') as f:
   p=subprocess.run(ADB+['shell','run-as',package,'sh','-c',"'cat > "+destination+"'"],stdin=f,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=240)
  (out/label).write_bytes(p.stdout);assert p.returncode==0,(label,p.stdout)
 baseline=ROOT/'downloads/answers/model/qwen2.5-0.5b-instruct-q4_k_m.gguf';optional=ROOT/'downloads/synthesis/model/qwen2.5-1.5b-instruct-q4_k_m.gguf'
 assert sha(baseline)=='74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db';pin=json.loads((ROOT/'tools/evaluation/model-capability/qwen25.json').read_text());assert sha(optional)==pin['sha256']
 if not resume:
  run(ADB+['get-state'],'device.txt');run(ADB+['shell','getprop'],'properties.txt');run(ADB+['shell','df','-k','/data'],'disk-before.txt')
  preserved=['files/model.gguf','files/pack-library/catalog.json','files/attachment-assets/tessdata/eng.traineddata','files/attachment-assets/ggml-tiny.en.bin']
  before=run(ADB+['shell','run-as',PKG,'sha256sum']+preserved,'saved-before.txt')
  run(['bash','tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',ROOT/'tools/evaluation/model-management/source.gradle','-PpocketloreTestRunner=org.pocketlore.app.ModelManagementInstrumentation'],'build.log')
  apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk';test=ROOT/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk'
  for f in [apk,test]:run(ADB+['install','-r',f],'install-'+f.name+'.txt')
  run(ADB+['shell','run-as',PKG+'.test','mkdir','-p','files'],'fixture-directory.txt')
  stream(baseline,PKG+'.test','files/baseline.gguf','baseline-transfer.txt')
  try:
   run(ADB+['shell','am','instrument','-w','-e','mode','import',PKG+'.test/'+PKG+'.ModelManagementInstrumentation'],'import-runtime.txt')
   report=run(ADB+['exec-out','run-as',PKG,'cat','files/model-management-import.json'],'import.json');assert json.loads(report)['status']=='PASS',report
  finally:run(ADB+['shell','run-as',PKG+'.test','rm','-f','files/baseline.gguf'],'remove-test-input.txt')
 else:
  before=(out/'saved-before.txt').read_bytes();assert json.loads((out/'import.json').read_text())['status']=='PASS'
  apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk';test=ROOT/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk'
 # Install the already pinned optional object once; do not duplicate it in a provider cache.
 destination='files/model-library/'+pin['sha256']+'.gguf'
 if not resume:
  run(ADB+['shell','run-as',PKG,'test','!','-e',destination],'optional-not-preexisting.txt')
  stream(optional,PKG,destination,'optional-transfer.txt')
 else:assert run(ADB+['shell','run-as',PKG,'sha256sum',destination],'resumed-optional-hash.txt').decode().split()[0]==pin['sha256']
 run(ADB+['shell','run-as',PKG,'du','-k','.'],'disk-with-optional.txt')
 run(ADB+['shell','am','instrument','-w','-e','mode','select',PKG+'.test/'+PKG+'.ModelManagementInstrumentation'],'select-runtime.txt')
 report=run(ADB+['exec-out','run-as',PKG,'cat','files/model-management-select.json'],'select.json');assert json.loads(report)['status']=='PASS',report
 after=run(ADB+['shell','run-as',PKG,'sha256sum']+preserved,'saved-after.txt');assert before==after
 run(ADB+['shell','dumpsys','package',PKG],'package.txt');assert 'android.permission.INTERNET' not in (out/'package.txt').read_text()
 run(ADB+['shell','df','-k','/data'],'disk-after.txt')
 path=run(ADB+['shell','pm','path',PKG],'installed-path.txt').decode().strip().removeprefix('package:');actual=run(ADB+['shell','sha256sum',path],'installed-hash.txt').decode().split()[0];assert actual==sha(apk)
 r={'status':'PASS','environment':'API35 x86_64 emulator-5560, not phone/quality acceptance','apk_sha256':actual,'apk_bytes':apk.stat().st_size,'test_apk_sha256':sha(test),'protocol_sha256':sha(ROOT/'tools/evaluation/model-management/protocol.json'),'baseline_sha256':sha(baseline),'optional_sha256':pin['sha256'],'hashes':{p.name:sha(p) for p in out.iterdir() if p.is_file()}}
 (out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');verify(out)
 original=(out/'select.json').read_bytes()
 try:
  (out/'select.json').write_bytes(original+b' ')
  try:verify(out);raise RuntimeError('Changed receipt accepted')
  except AssertionError:pass
  (out/'select.json').unlink()
  try:verify(out);raise RuntimeError('Missing receipt accepted')
  except FileNotFoundError:pass
 finally:(out/'select.json').write_bytes(original)
 print(json.dumps({'output':str(out),'status':'PASS','changed_missing_receipts_rejected':True}))
if __name__=='__main__':main()
