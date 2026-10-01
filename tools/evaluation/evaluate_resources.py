#!/usr/bin/env python3
"""Measure actual app/JNI behavior on the existing emulator; preserve raw failures."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,zipfile
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'downloads/resources'/datetime.datetime.now(datetime.timezone.utc).strftime('run-%Y%m%dT%H%M%SZ');OUT.mkdir(parents=True)
print(OUT,flush=True)
def run(args,name,input=None):
 p=subprocess.run(list(map(str,args)),input=input,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(OUT/name).write_bytes(p.stdout)
 if p.returncode:print(p.stdout.decode(errors='replace'));p.check_returncode()
 return p.stdout
tc=Path(os.environ.get('POCKETLORE_TOOLCHAIN','/home/isa/Android/atlas-toolchain'));adb=[tc/'sdk/platform-tools/adb','-s','emulator-5560']
(OUT/'host-meminfo.txt').write_bytes(Path('/proc/meminfo').read_bytes())
run(adb+['shell','cat','/proc/meminfo'],'emulator-meminfo-before.txt');assert run(adb+['shell','getprop','sys.boot_completed'],'boot.txt').strip()==b'1'
run(adb+['shell','getprop','ro.build.fingerprint'],'emulator-fingerprint.txt')
run(['bash',ROOT/'tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-PpocketloreTestRunner=org.pocketlore.app.ResourceInstrumentation'],'build.log')
apks=[ROOT/'android/app/build/outputs/apk/debug/app-debug.apk',ROOT/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk']
for i,p in enumerate(apks):run(adb+['install','-r',p],f'install-{i}.txt')
run(adb+['shell','am','force-stop','org.pocketlore.app'],'force-stop.txt')
# Reuse installed compatible test assets; never silently overwrite a user's model.
for remote,digest in [('files/synthesis-tests/model.gguf','061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a'),('files/synthesis-tests/reference.plpack','567e9bbbaab896826809ec20f81ae1c4b3f421b011931edae0989d28cfce10ea')]:
 data=run(adb+['shell','run-as','org.pocketlore.app','sha256sum',remote],'hash-'+Path(remote).name+'.txt');assert data.decode().split()[0]==digest
run(adb+['shell','run-as','org.pocketlore.app','du','-ak','files','cache','code_cache'],'disk-before.txt')
run(adb+['shell','df','-k','/data'],'free-disk-before.txt')
r=run(adb+['shell','am','instrument','-w','org.pocketlore.app.test/org.pocketlore.app.ResourceInstrumentation'],'instrumentation.txt')
raw=run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/resource-results.json'],'results.json');report=json.loads(raw)
run(adb+['shell','logcat','-d','--pid='+str(report.get('pid',0)),'-v','threadtime'],'app-logcat.txt')
run(adb+['shell','run-as','org.pocketlore.app','du','-ak','files','cache','code_cache'],'disk-after.txt')
run(adb+['shell','cat','/proc/meminfo'],'emulator-meminfo-after.txt');run(adb+['shell','df','-k','/data'],'free-disk-after.txt')
assert b'INSTRUMENTATION_CODE: -1' in r and report['status']=='PASS',report
expected={'pinned_real_model','low_storage_rejected','model_mid_copy_cancel','model_cancel_preserves_old','injected_model_oom_cleanup','invalid_pack_preserves_old','pack_mid_copy_cancel','pack_old_bytes_preserved','recognized_stage_recovery_only','full_real_model_staged_hash','full_stage_removed','second_resident_session_rejected','context_overflow_rejected','real_generation','context_released_after_generation','close_cancels_and_holds_resident_lease_until_return','no_native_lease_or_context_after_cancel','session_slot_recovered','activity_saved_model_ready','trim_model_unavailable','trim_released_native_lease','explicit_reload_after_trim','low_memory_callback_releases','saved_model_unchanged_after_pressure'}
assert set(report['checks'])==expected and len(report['checks'])==len(expected)
assert report['generation_tokens']>0 and report['sampled_peak_pss_kib']>0 and len(report['samples'])>3
assert report['staged_model_bytes']==report['model_bytes'] and report['model_bytes']==1834426016
artifacts={str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in apks}
with zipfile.ZipFile(apks[0]) as z:
 for n in z.namelist():
  if n.endswith('.so') or n.endswith('.tsv'):artifacts[n]={'uncompressed_bytes':z.getinfo(n).file_size,'compressed_bytes':z.getinfo(n).compress_size,'sha256':hashlib.sha256(z.read(n)).hexdigest()}
summary={'status':'PASS','scope':'Actual emulator JNI and disk measurements; injected callback/storage controls; no physical acceptance','checks':len(expected),'artifacts':artifacts,'results_sha256':hashlib.sha256(raw).hexdigest()}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
