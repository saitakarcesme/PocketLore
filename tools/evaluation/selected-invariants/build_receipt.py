"""Fresh required build with exact inputs and raw receipts; no device commands."""
import hashlib,json,pathlib,subprocess,sys,time,resource,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[3]
def sha(b):return hashlib.sha256(b).hexdigest()
def inputs():
 paths=subprocess.check_output(['git','ls-files','android','tools/android-build.sh','tools/release/finalize_apk.py','tools/release/debug-signing.gradle'],cwd=ROOT,text=True).splitlines()
 return {p:sha((ROOT/p).read_bytes()) for p in paths if (ROOT/p).is_file()}
def main(out):
 out.mkdir(parents=True);before=inputs();start=time.time();r=subprocess.run(['bash','tools/android-build.sh'],cwd=ROOT,capture_output=True);(out/'stdout').write_bytes(r.stdout);(out/'stderr').write_bytes(r.stderr);after=inputs();apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk';members={}
 if apk.exists():
  with zipfile.ZipFile(apk) as z:
   for n in z.namelist():
    if n.endswith(('.dex','.so')):members[n]=sha(z.read(n))
 result={'command':['bash','tools/android-build.sh'],'exit':r.returncode,'start':start,'end':time.time(),'source_inputs_before':before,'source_inputs_after':after,'inputs_unchanged':before==after,'apk_sha256':sha(apk.read_bytes()) if apk.exists() else None,'apk_bytes':apk.stat().st_size if apk.exists() else None,'apk_members':members,'stdout_sha256':sha(r.stdout),'stderr_sha256':sha(r.stderr),'child_maxrss_bytes':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss*1024,'memory_definition':'Child maximum, not aggregate process-tree peak; Gradle configured 2 workers/2GiB heap','device_execution':False};(out/'build.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));return r.returncode or int(before!=after)
if __name__=='__main__':sys.exit(main(pathlib.Path(sys.argv[1])))
