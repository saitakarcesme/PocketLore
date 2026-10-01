#!/usr/bin/env python3
"""Real sequential emulator comparison; no credentials or private evaluation inputs."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    out=ROOT/'downloads/comparison'/datetime.datetime.now(datetime.timezone.utc).strftime('run-%Y%m%dT%H%M%SZ');out.mkdir(parents=True)
    def run(args,**kw):
        p=subprocess.run(list(map(str,args)),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,**kw)
        if p.returncode:(out/'failure.txt').write_bytes(p.stdout);p.check_returncode()
        return p.stdout
    tc=Path(os.environ.get('POCKETLORE_TOOLCHAIN','/home/isa/Android/atlas-toolchain'))
    adb=[tc/'sdk/platform-tools/adb','-s',os.environ.get('ANDROID_SERIAL','emulator-5560')]
    assert str(adb[2]).startswith('emulator-')
    assert run(adb+['shell','getprop','sys.boot_completed']).strip()==b'1'
    protocol=ROOT/'evaluation/comparison-v1/protocol.json';spec=json.loads(protocol.read_text())
    pack=ROOT/'downloads/packs/english-reference.plpack';assert sha(pack)==spec['pack_sha256']
    # Use the already imported model; never overwrite user model state.
    assert run(adb+['shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf']).decode().split()[0]==spec['model_sha256']
    (out/'build.log').write_bytes(run(['bash',ROOT/'tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',ROOT/'tools/evaluation/comparison/source.gradle','-PpocketloreTestRunner=org.pocketlore.app.ComparisonInstrumentation']))
    apks=[ROOT/'android/app/build/outputs/apk/debug/app-debug.apk',ROOT/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk']
    for apk in apks:run(adb+['install','-r',apk])
    run(adb+['shell','am','force-stop','org.pocketlore.app'])
    run(adb+['shell','run-as','org.pocketlore.app','mkdir','-p','files/comparison-tests'])
    for name,p in [('protocol.json',protocol),('reference.plpack',pack)]:
        run(adb+['shell','run-as','org.pocketlore.app','sh','-c',"'cat > files/comparison-tests/"+name+"'"],input=p.read_bytes())
    environment={k:run(adb+['shell',*cmd]).decode().strip() for k,cmd in {'fingerprint':['getprop','ro.build.fingerprint'],'abi':['getprop','ro.product.cpu.abi'],'airplane_mode':['settings','get','global','airplane_mode_on']}.items()}
    log=run(adb+['shell','am','instrument','-w','org.pocketlore.app.test/org.pocketlore.app.ComparisonInstrumentation']);(out/'instrumentation.txt').write_bytes(log)
    (out/'partial.json').write_bytes(run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/comparison-tests/partial.json']))
    assert b'INSTRUMENTATION_CODE: -1' in log,log.decode()
    raw=run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/comparison-tests/results.json']);(out/'results.json').write_bytes(raw)
    (out/'protocol.json').write_bytes(protocol.read_bytes())
    manifest={'version':1,'environment':environment,'measurement_class':'AOSP emulator on LLMRig; not physical Android','model_sha256':spec['model_sha256'],'pack_sha256':sha(pack),'protocol_sha256':sha(protocol),'results_sha256':sha(out/'results.json'),'apk_sha256':sha(apks[0]),'test_apk_sha256':sha(apks[1]),'git_commit':run(['git','rev-parse','HEAD']).decode().strip(),'source_hashes':{str(p.relative_to(ROOT)):sha(p) for p in sorted(list((ROOT/'tools/evaluation/comparison').glob('*'))+list((ROOT/'android/app/src/main/java/org/pocketlore/app').glob('*.java'))+[ROOT/'tools/evaluation/run_comparison.py',ROOT/'tools/evaluation/verify_comparison.py'])},'external_rivals':{'status':'not run','reason':'No configured authorized rival endpoint supplied; no credentials sought or outputs fabricated.'}}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    from verify_comparison import make_blind,validate
    packet,key=make_blind(json.loads(raw));(out/'blind.json').write_text(json.dumps(packet,indent=2)+'\n');(out/'identity-key.json').write_text(json.dumps(key,indent=2)+'\n')
    validate(out);print(out,flush=True)
if __name__=='__main__':main()
