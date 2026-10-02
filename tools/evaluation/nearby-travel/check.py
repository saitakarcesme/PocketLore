import pathlib,subprocess,json,hashlib,time
ROOT=pathlib.Path(__file__).resolve().parents[3];ADB=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5560']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=ROOT/'downloads/nearby-travel'/time.strftime('%Y%m%dT%H%M%SZ',time.gmtime());out.mkdir(parents=True)
 def run(cmd,name,timeout=360):
  r=subprocess.run(list(map(str,cmd)),cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout);(out/name).write_bytes(r.stdout);assert r.returncode==0,(name,r.stdout[-2000:]);return r.stdout
 payload=ROOT/'android/app/src/main/assets/reviewed-cities.json';pin=json.loads((ROOT/'tools/evaluation/nearby-travel/payload-pin.json').read_text());assert sha(payload)==pin['sha256'] and payload.stat().st_size<=200000
 run(['bash','tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',ROOT/'tools/evaluation/nearby-travel/source.gradle','-PpocketloreTestRunner=org.pocketlore.app.NearbyTravelInstrumentation'],'build.log')
 before=run(ADB+['shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf','files/model-selection','files/scale-library/catalog.json','files/pack-library/catalog.json'],'before.txt')
 for name in ['debug/app-debug.apk','androidTest/debug/app-debug-androidTest.apk']:run(ADB+['install','-r',ROOT/'android/app/build/outputs/apk'/name],'install-'+pathlib.Path(name).name+'.txt')
 run(ADB+['shell','am','instrument','-w','org.pocketlore.app.test/org.pocketlore.app.NearbyTravelInstrumentation'],'runtime.txt',600)
 raw=run(ADB+['exec-out','run-as','org.pocketlore.app','cat','files/nearby-travel.json'],'report.json');report=json.loads(raw);assert report['status']=='PASS',report.get('error')
 for id in [292223,292672,292968]:run(ADB+['exec-out','run-as','org.pocketlore.app','cat',f'files/city-export-{id}.md'],f'city-export-{id}.md')
 after=run(ADB+['shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf','files/model-selection','files/scale-library/catalog.json','files/pack-library/catalog.json'],'after.txt');assert before==after
 package=run(ADB+['shell','dumpsys','package','org.pocketlore.app'],'package.txt');assert b'android.permission.INTERNET' not in package and b'ACCESS_BACKGROUND_LOCATION' not in package
 apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk';path=run(ADB+['shell','pm','path','org.pocketlore.app'],'installed.txt').decode().strip().removeprefix('package:');installed=run(ADB+['shell','sha256sum',path],'installed-hash.txt').decode().split()[0];assert installed==sha(apk)
 receipt={'status':'PASS','apk_sha256':installed,'apk_bytes':apk.stat().st_size,'payload':pin,'environment':'API35 x86_64 emulator-5560, no physical GPS fix or phone qualification','checks':len(report['checks']),'files':{p.name:sha(p) for p in out.iterdir() if p.is_file()}}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':'PASS','output':str(out),'checks':len(report['checks'])}))
if __name__=='__main__':main()
