import pathlib,json,subprocess,time,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[3];ADB=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5562']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=ROOT/'downloads/hybrid-retrieval'/time.strftime('%Y%m%dT%H%M%SZ',time.gmtime());out.mkdir(parents=True)
 def run(cmd,name,timeout=480):
  p=subprocess.run(list(map(str,cmd)),cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout);(out/name).write_bytes(p.stdout);assert p.returncode==0,(name,p.stdout[-2000:]);return p.stdout
 baseline=json.loads((ROOT/'docs/evidence/hybrid-retrieval/baseline.json').read_text());assert baseline['status']=='PASS'
 run(ADB+['get-state'],'state.txt');run(ADB+['shell','getprop'],'properties.txt');run(ADB+['shell','df','-k','/data'],'disk-before.txt')
 before=run(ADB+['shell','run-as','org.pocketlore.app','sha256sum','files/scale-library/catalog.json','files/model.gguf'],'before.txt')
 run(['bash','tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',ROOT/'tools/evaluation/hybrid-retrieval/source.gradle','-PpocketloreTestRunner=org.pocketlore.app.HybridRetrievalInstrumentation'],'build.log')
 apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk';test=ROOT/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk'
 for f in [apk,test]:run(ADB+['install','-r',f],'install-'+f.name+'.txt')
 run(ADB+['shell','am','instrument','-w','-e','mode','cached','org.pocketlore.app.test/org.pocketlore.app.HybridRetrievalInstrumentation'],'runtime.txt')
 raw=run(ADB+['exec-out','run-as','org.pocketlore.app','cat','files/hybrid-cached.json'],'report.json');r=json.loads(raw);assert r['status']=='PASS',r.get('error')
 assert [x['identities'] for x in r['searches']]==[x['identities'] for x in baseline['searches']],'Ranking changed'
 assert all(x['cache_hit'] for x in r['reads'][1:]);assert max(x['ms'] for x in r['reads'][1:])<min(x['ms'] for x in baseline['reads']),'No repeat-read improvement'
 after=run(ADB+['shell','run-as','org.pocketlore.app','sha256sum','files/scale-library/catalog.json','files/model.gguf'],'after.txt');assert before==after
 path=run(ADB+['shell','pm','path','org.pocketlore.app'],'installed-path.txt').decode().strip().removeprefix('package:');installed=run(ADB+['shell','sha256sum',path],'installed-hash.txt').decode().split()[0];assert installed==sha(apk)
 run(ADB+['shell','df','-k','/data'],'disk-after.txt');receipt={'status':'PASS','apk_sha256':installed,'apk_bytes':apk.stat().st_size,'baseline_sha256':sha(ROOT/'docs/evidence/hybrid-retrieval/baseline.json'),'protocol_sha256':sha(ROOT/'tools/evaluation/hybrid-retrieval/protocol.json'),'files':{p.name:sha(p) for p in out.iterdir() if p.is_file()},'semantic_embedder':None,'scope':'Full installed API35 emulator corpus; unchanged ranking, bounded verified-preview cache; not phone or answer support'}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':'PASS','output':str(out),'reads':r['reads'],'cache_state':r['cache_state']}))
if __name__=='__main__':main()
