"""Honest source-structure gate: host evidence never substitutes for unavailable Android."""
import base64,hashlib,json,pathlib,subprocess,time,traceback,uuid
ROOT=pathlib.Path(__file__).resolve().parents[3]
PACKET=pathlib.Path('/home/isa/PocketLore-control/overnight-20261005/source-reader-prerequisite-review-20261006T0323Z')
TERMINAL=pathlib.Path('/home/isa/PocketLore-control/overnight-20261005/swiftshader-terminal-20261006T0347Z.json')
def sha(b):return hashlib.sha256(b).hexdigest()
def raw(p):
 b=p.read_bytes();return {'sha256':sha(b),'bytes':len(b),'base64':base64.b64encode(b).decode()}
run=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'-'+uuid.uuid4().hex[:6];out=ROOT/'downloads/source-structure-reader'/run;out.mkdir();report={'run':run,'status':'FAIL','android':'unexecuted; known terminal owned emulator; no retry/restart','source_admission_established':False,'files':{}}
try:
 files=[*list((ROOT/'tools/packs/source-structure').glob('*.py')),*list((ROOT/'tools/evaluation/source-structure').rglob('*.py')),*list((ROOT/'tools/evaluation/source-structure').rglob('*.java')),*list((ROOT/'android/app/src/main/java/org/pocketlore/app').glob('*Structur*.java'))]
 files += [ROOT/'android/app/src/main/AndroidManifest.xml',ROOT/'android/app/src/main/java/org/pocketlore/app/ScaleActivity.java',ROOT/'tools/evaluation/check_source_structure_reader.sh',ROOT/'tools/evaluation/source-structure/source.gradle']
 report['source_inputs']={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in files};report['commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 start=time.time();r=subprocess.run(['python3',str(ROOT/'tools/evaluation/source-structure/test_host.py'),str(out/'host')],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=90);(out/'host.log').write_bytes(r.stdout);report['host_command']={'exit':r.returncode,'start':start,'end':time.time()};assert r.returncode==0,'Host source structure regression'
 report['host']=json.loads((out/'host/host.json').read_text());report['files']['host.log']=raw(out/'host.log')
 # Raw known terminal failure is retained. Do not issue ADB on the same failed invocation.
 report['files']['terminal-host.json']=raw(TERMINAL)
 report['android_missing']=['actual FTS4/platform semantics','isolated import/rollback/cancellation','reader highlight/source navigation/export/restart','current installed APK/boot/inventory/storage/memory']
 report['status']='HOST_PASS_ANDROID_UNEXECUTED'
except BaseException:report['error']=traceback.format_exc()
finally:
 for p in out.rglob('*.log'):report['files'][str(p.relative_to(out))]=raw(p)
 for p in files:report['files'][str(p.relative_to(ROOT))]=raw(p)
 for name in ['manifest.json','independent-expectations.json','sample-policy.json','original-2956.json','original-30000.json','original-100000.json','original-200000.json','html-2956.html','html-30000.html','html-100000.html','html-200000.html']:report['files']['frozen-originals/'+name]=raw(PACKET/name)
 for name in ['CC-BY-SA-3.0.txt','CC-BY-SA-4.0.txt']:report['files']['licenses/'+name]=raw(ROOT/'tools/scale/wiki'/name)
 for name in ['/tmp/source-structure-build.log','/tmp/source-structure-build2.log','/tmp/source-structure-build3.log','/tmp/source-structure-build-final.log','/tmp/source-structure-build-final2.log']:
  if pathlib.Path(name).is_file():report['files'][pathlib.Path(name).name]=raw(pathlib.Path(name))
 for name in ['debug/app-debug.apk','androidTest/debug/app-debug-androidTest.apk']:
  p=ROOT/'android/app/build/outputs/apk'/name
  if p.is_file():report.setdefault('built_apks',{})[name]={'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size,'installed_on_device':False}
 path=ROOT/'docs/evidence/source-structure-reader-review.json';path.write_text(json.dumps(report,indent=2));(out/'review.json').write_bytes(path.read_bytes());print(json.dumps({k:report[k] for k in ('run','status','android')},indent=2),flush=True)
raise SystemExit(1)
