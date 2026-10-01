"""Real, serial local JNI acceptance; immutable per-run failures and raw outputs."""
import hashlib,json,os,subprocess,time,zipfile,tempfile,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];ADB='/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb';SERIAL=os.environ.get('POCKETLORE_ATTACHMENTS_SERIAL','emulator-5560')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def verify(p,pin):assert p.is_file() and p.stat().st_size==pin['bytes'] and sha(p)==pin['sha256'],f'Missing/changed asset {p}'
def alignment(data):
 assert data[:5]==b'\x7fELF\x02';off=struct.unpack_from('<Q',data,32)[0];size,count=struct.unpack_from('<HH',data,54);segments=[struct.unpack_from('<IIQQQQQQ',data,off+i*size) for i in range(count)];loads=[s for s in segments if s[0]==1];assert loads and all(s[7]>=16384 and (s[2]-s[3])%16384==0 for s in loads)
def main():
 fixture=json.loads((ROOT/'docs/evidence/attachments/fixtures.json').read_text());models=json.loads((ROOT/'tools/attachments/models.json').read_text());inputs={n:ROOT/'downloads/attachments/fixtures'/n for n in fixture['files']}
 for n,p in inputs.items():verify(p,fixture['files'][n])
 photo=json.loads((ROOT/'docs/evidence/attachments/photo-supplement.json').read_text());inputs['photo.jpg']=ROOT/'downloads/attachments/fixtures/photo.jpg';verify(inputs['photo.jpg'],photo['files']['photo.jpg'])
 for kind,pin in models.items():p=ROOT/'downloads/attachments'/('models/'+pin['file'] if kind=='speech' else pin['file']);verify(p,pin);inputs[pin['file']]=p
 with tempfile.TemporaryDirectory() as tmp:
  p=Path(tmp)/'asset';p.write_bytes(b'changed')
  for stage in ['changed','missing']:
   if stage=='missing':p.unlink()
   try:verify(p,models['ocr'])
   except AssertionError:pass
   else:raise AssertionError('Invalid asset accepted')
 stamp=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime());out=ROOT/'downloads/attachments/runs'/stamp;out.mkdir(parents=True,exist_ok=False);adb=[ADB,'-s',SERIAL]
 def run(cmd,name,data=None,timeout=300):
  r=subprocess.run(list(map(str,cmd)),cwd=ROOT,input=data,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout);(out/name).write_bytes(r.stdout);assert r.returncode==0,f'{name}: {out}';return r.stdout
 assert run(adb+['get-state'],'state.txt').strip()==b'device';run(adb+['shell','getprop'],'properties.txt')
 before=run(adb+['shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf','files/pack-library/catalog.json'],'saved-before.txt')
 run(['bash','tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',ROOT/'tools/evaluation/attachments/source.gradle','-PpocketloreTestRunner=org.pocketlore.app.AttachmentsInstrumentation'],'build.log',timeout=600)
 identities={}
 for rel in ['debug/app-debug.apk','androidTest/debug/app-debug-androidTest.apk']:
  p=ROOT/'android/app/build/outputs/apk'/rel;identities[p.name]={'bytes':p.stat().st_size,'sha256':sha(p)};run(adb+['install','-r',p],'install-'+p.name+'.txt')
 apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk';permissions=run(['/home/isa/Android/atlas-toolchain/sdk/build-tools/35.0.0/aapt','dump','permissions',apk],'permissions.txt');assert b'android.permission.INTERNET' not in permissions and b'android.permission.RECORD_AUDIO' in permissions
 with zipfile.ZipFile(apk) as z:
  for abi in ['arm64-v8a','x86_64']:alignment(z.read(f'lib/{abi}/libpocketlore_attachments.so'))
  assert not any(b'com/google/android/gms' in z.read(n) for n in z.namelist() if n.endswith('.dex'))
 run(['/home/isa/Android/atlas-toolchain/sdk/build-tools/35.0.0/zipalign','-c','-P','16','4',apk],'zipalign.txt')
 run(adb+['shell','pm','revoke','org.pocketlore.app','android.permission.RECORD_AUDIO'],'revoke.txt')
 run(adb+['shell','run-as','org.pocketlore.app','mkdir','-p','files/attachments-input'],'mkdir.txt')
 for name,p in inputs.items():run(adb+['shell','run-as','org.pocketlore.app','sh','-c',"'cat > files/attachments-input/"+name+"'"],'push-'+name+'.txt',p.read_bytes())
 directory='attachments-test-'+stamp;log=run(adb+['shell','am','instrument','-w','-e','directory',directory,'org.pocketlore.app.test/org.pocketlore.app.AttachmentsInstrumentation'],'instrumentation.txt',timeout=240)
 if b'Process crashed' in log:run(adb+['logcat','-d','-t','200','-s','AndroidRuntime'],'crash.txt');raise AssertionError(str(out))
 report=json.loads(run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/'+directory+'/results.json'],'results.json'))
 after=run(adb+['shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf','files/pack-library/catalog.json'],'saved-after.txt');assert before==after
 run(adb+['shell','run-as','org.pocketlore.app','du','-sk','files/attachment-assets','cache'],'storage.txt');run(adb+['shell','dumpsys','meminfo','org.pocketlore.app'],'meminfo.txt');run(adb+['shell','df','-k','/data'],'capacity.txt')
 receipt={'serial':SERIAL,'artifacts':identities,'results_sha256':sha(out/'results.json'),'status':report['status'],'model_and_catalog_unchanged':before==after,'model_bytes':sum(p['bytes'] for p in models.values()),'artifact_mutations':['changed','missing'],'alignment':'both ABI LOAD and APK16KB passed'};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 assert report['status']=='PASS' and b'ATTACHMENTS_PASS' in log,f'{out}: {report.get("error")}'
 required={'real_ocr_text','tilted_image_text','real_local_transcription','empty_blank.png','empty_silence.wav','ocr_absent','speech_absent','invalid_image','pixel_bound','invalid_audio','native_cancel_released_false','native_cancel_released_true','denied_permission_ui','editable_real_ocr_preview','cancel_discards_completed_preview','absent_engine_ui_keeps_microphone_off','actual_audiorecord_opened','background_clears_capture_and_result','provenance_photo.jpg','retry_preview_visible','cancel_before_verification_never_starts_microphone'};assert required.issubset(report['checks'])
 run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/'+directory+'/preview.png'],'preview.png')
 run(adb+['shell','pm','revoke','org.pocketlore.app','android.permission.RECORD_AUDIO'],'revoke-after.txt')
 print(json.dumps({'status':'PASS','output':str(out),'checks':len(report['checks']),'receipt':receipt},indent=2))
if __name__=='__main__':main()
