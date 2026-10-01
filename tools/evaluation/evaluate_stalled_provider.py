#!/usr/bin/env python3
"""Real Android provider transport regression; preserve failed and passing runs."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys,shutil
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    legacy='--legacy' in sys.argv
    out=ROOT/'downloads/stalled-provider'/datetime.datetime.now(datetime.timezone.utc).strftime('run-%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True);print(out,flush=True)
    def run(args,name,input=None):
        p=subprocess.run(list(map(str,args)),input=input,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180)
        (out/name).write_bytes(p.stdout)
        if p.returncode:raise RuntimeError(f'Command failed: {out/name}')
        return p.stdout
    tc=Path(os.environ.get('POCKETLORE_TOOLCHAIN','/home/isa/Android/atlas-toolchain'));adb=[tc/'sdk/platform-tools/adb','-s','emulator-5560']
    fixture=ROOT/'tools/evaluation/stalled-provider/cases.json';spec=json.loads(fixture.read_text())
    assert sha(fixture)=='1c0818856e39dea26aa41f3806087b5ffb837f6c8aa205c7bf950a81435707f5'
    pack=ROOT/'downloads/packs/english-reference.plpack';assert sha(pack)==spec['pack_sha256']
    assert run(adb+['shell','getprop','sys.boot_completed'],'boot.txt').strip()==b'1'
    run(adb+['shell','getprop','ro.build.fingerprint'],'fingerprint.txt')
    before=run(adb+['shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf','files/knowledge.plpack'],'saved-before.txt')
    run(['bash',ROOT/'tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',ROOT/'tools/evaluation/stalled-provider/source.gradle','-PpocketloreTestRunner=org.pocketlore.app.StalledProviderInstrumentation'],'build.log')
    identities={}
    for path in ['debug/app-debug.apk','androidTest/debug/app-debug-androidTest.apk']:
        p=ROOT/'android/app/build/outputs/apk'/path;identities[p.name]={'sha256':sha(p),'bytes':p.stat().st_size};shutil.copyfile(p,out/p.name)
        run(adb+['install','-r',p],'install-'+p.name+'.txt')
    run(adb+['shell','am','force-stop','org.pocketlore.app'],'stop.txt')
    for package,directory in [('org.pocketlore.app','files/stalled-provider-tests'),('org.pocketlore.app.test','files')]:
        run(adb+['shell','run-as',package,'mkdir','-p',directory],package+'-mkdir.txt')
        run(adb+['shell','run-as',package,'sh','-c',"'cat > "+directory+"/reference.plpack'"],package+'-pack.txt',pack.read_bytes())
    run(adb+['shell','run-as','org.pocketlore.app','rm','-f','files/stalled-provider-tests/results.json'],'clear-old-result.txt')
    log=run(adb+['shell','am','instrument','-w','-e','legacy',str(legacy).lower(),'org.pocketlore.app.test/org.pocketlore.app.StalledProviderInstrumentation'],'instrumentation.txt')
    if b'INSTRUMENTATION_CODE: -1' not in log:
        run(adb+['shell','logcat','-d','-t','160','-s','AndroidRuntime'],'failure-logcat.txt')
    raw=run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/stalled-provider-tests/results.json'],'results.json');report=json.loads(raw)
    after=run(adb+['shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf','files/knowledge.plpack'],'saved-after.txt');assert before==after
    assert b'INSTRUMENTATION_CODE: -1' in log,report
    assert report['status']==('BASELINE_FAILURE_REPRODUCED' if legacy else 'PASS'),report
    assert {(r['kind'],r['case']) for r in report['rows']}=={(k,c) for k in spec['imports'] for c in spec['cases']} and len(report['rows'])==10
    cancels=[r for r in report['rows'] if 'cancel_ms' in r]
    if legacy:assert any(not r['returned_before_release'] for r in cancels)
    else:
        assert all(r['returned_before_release'] and r['clean_before_release'] and r['saved_unchanged'] and r['cancel_ms']<spec['cancel_deadline_ms'] for r in cancels)
        assert all(r['opens']==0 if r['case']=='cancel-before-open' else r['provider_state_after_release']=='reader-closed' for r in cancels)
    assert len({r['worker_thread_id'] for r in report['rows'] if r['case']=='retry'})==1
    summary={'status':report['status'],'scope':'x86_64 emulator document-provider transport; model retry is staging only, not native validation','fixture_sha256':sha(fixture),'pack_sha256':sha(pack),'results_sha256':sha(out/'results.json'),'artifacts':identities,'max_cancel_ms':max(r['cancel_ms'] for r in cancels),'actual_saved_assets_unchanged':before==after}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
