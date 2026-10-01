#!/usr/bin/env python3
"""Actual production travel behavior, on host and the existing emulator."""
import datetime,hashlib,json,os,subprocess
from pathlib import Path
from build_travel import ROOT,build
out=ROOT/'downloads/travel'/datetime.datetime.now(datetime.timezone.utc).strftime('verify-%Y%m%dT%H%M%SZ');out.mkdir(parents=True)
def run(args,name):
 p=subprocess.run(list(map(str,args)),stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(out/name).write_bytes(p.stdout)
 if p.returncode:print(p.stdout.decode(errors='replace'));p.check_returncode()
 return p.stdout
pack,manifest=build();first=pack.read_bytes();assert build()[0].read_bytes()==first
assert first==(ROOT/'android/app/src/main/assets/dc-monuments.tsv').read_bytes()
assert manifest==json.loads((ROOT/'android/app/src/main/assets/dc-monuments-manifest.json').read_text())
tc=Path(os.environ.get('POCKETLORE_TOOLCHAIN','/home/isa/Android/atlas-toolchain'));host=out/'host';host.mkdir()
java=ROOT/'android/app/src/main/java/org/pocketlore/app';test=ROOT/'android/app/src/androidTest/java/org/pocketlore/app'
run([tc/'jdk/bin/javac','-d',host,*[java/(n+'.java') for n in ['TravelTools','TravelCatalog','TravelCommands']],test/'TravelChecks.java'],'compile.txt')
run([tc/'jdk/bin/java','-cp',host,'org.pocketlore.app.TravelChecks',pack],'host.txt')
run(['bash',ROOT/'tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-PpocketloreTestRunner=org.pocketlore.app.TravelInstrumentation'],'build.log')
adb=[tc/'sdk/platform-tools/adb','-s','emulator-5560'];assert run(adb+['shell','getprop','sys.boot_completed'],'boot.txt').strip()==b'1'
run(adb+['shell','getprop','ro.build.fingerprint'],'environment.txt')
apks=[ROOT/'android/app/build/outputs/apk/debug/app-debug.apk',ROOT/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk']
for i,apk in enumerate(apks):run(adb+['install','-r',apk],f'install-{i}.txt')
r=run(adb+['shell','am','instrument','-w','org.pocketlore.app.test/org.pocketlore.app.TravelInstrumentation'],'instrumentation.txt')
assert b'INSTRUMENTATION_CODE: -1' in r,r.decode()
run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/travel-results.txt'],'emulator.txt')
summary={'status':'PASS','environment':'Host JVM and AOSP x86_64 emulator; no physical device','pack':manifest,'apk_sha256':hashlib.sha256(apks[0].read_bytes()).hexdigest(),'test_apk_sha256':hashlib.sha256(apks[1].read_bytes()).hexdigest(),'scope':'Frozen deterministic behavior and real Activity actions; not a route, live-data or human usefulness acceptance'}
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(out);print(json.dumps(summary,indent=2))
