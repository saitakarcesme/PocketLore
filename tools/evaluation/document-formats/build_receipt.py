"""Actual bounded Gradle commands with before/after source and APK identities."""
import hashlib,json,pathlib,subprocess,sys,time,uuid,zipfile,resource
R=pathlib.Path(__file__).resolve().parents[3]
def sha(b):return hashlib.sha256(b).hexdigest()
def inputs():
 paths=subprocess.check_output(['git','ls-files','android','tools/evaluation/document-formats','tools/android-build.sh','tools/runtime/pins.env','tools/release/finalize_apk.py','tools/release/debug-signing.gradle'],cwd=R,text=True).splitlines();return {p:sha((R/p).read_bytes()) for p in paths if (R/p).is_file()}
kind=sys.argv[1];out=R/'downloads/document-formats'/('build-'+kind+'-'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime()));out.mkdir();before=inputs();argv=['bash','tools/android-build.sh']
if kind=='instrumentation':argv+=['assembleDebug','assembleDebugAndroidTest','--init-script',str(R/'tools/evaluation/document-formats/source.gradle'),'-PpocketloreTestRunner=org.pocketlore.app.DocumentFormatsInstrumentation']
start=time.time();p=subprocess.run(argv,cwd=R,capture_output=True);(out/'stdout').write_bytes(p.stdout);(out/'stderr').write_bytes(p.stderr);after=inputs();artifacts={}
for path in [R/'android/app/build/outputs/apk/debug/app-debug.apk',R/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk']:
 if path.exists():
  with zipfile.ZipFile(path) as z:members={n:sha(z.read(n)) for n in z.namelist() if n.endswith(('.dex','.so'))}
  artifacts[str(path)]={'sha256':sha(path.read_bytes()),'bytes':path.stat().st_size,'members':members,'current_command_included_test_build':kind=='instrumentation'}
r=dict(argv=argv,start=start,end=time.time(),exit=p.returncode,source_before=before,source_after=after,inputs_unchanged=before==after,artifacts=artifacts,child_maxrss_bytes=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss*1024,resource_scope='Child highwater only, not aggregate process-tree peak; Gradle2workers/2GiBheap configured',stdout_sha256=sha(p.stdout),stderr_sha256=sha(p.stderr));(out/'receipt.json').write_text(json.dumps(r,indent=2));print(json.dumps({'path':str(out),'exit':p.returncode,'inputs_unchanged':before==after}));raise SystemExit(p.returncode or int(before!=after))
