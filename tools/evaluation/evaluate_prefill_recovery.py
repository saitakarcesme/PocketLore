#!/usr/bin/env python3
"""Real JNI prefill/load cancellation and app SIGKILL/restart on the existing emulator."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,time,shutil
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    out=ROOT/'downloads/prefill-recovery'/datetime.datetime.now(datetime.timezone.utc).strftime('run-%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True);print(out,flush=True)
    def run(args,name,input=None,allow=False):
        p=subprocess.run(list(map(str,args)),input=input,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180);(out/name).write_bytes(p.stdout)
        if not allow and p.returncode:raise RuntimeError(f'Command failed: {out/name}')
        return p.stdout
    specfile=ROOT/'tools/evaluation/prefill-recovery/cases.json';assert sha(specfile)=='0d28f42eadd5dc0aace4d251f6f089249db381319278d6ba4c196844c861368e';spec=json.loads(specfile.read_text())
    tc=Path(os.environ.get('POCKETLORE_TOOLCHAIN','/home/isa/Android/atlas-toolchain'));adb=[tc/'sdk/platform-tools/adb','-s','emulator-5560']
    assert run(adb+['shell','getprop','sys.boot_completed'],'boot.txt').strip()==b'1'
    run(adb+['shell','getprop','ro.build.fingerprint'],'fingerprint.txt')
    before=run(adb+['shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf','files/knowledge.plpack'],'saved-before.txt');assert before.decode().split()[0]==spec['model_sha256']
    run(['c++','-std=c++17','-I',ROOT/'android/app/src/main/cpp',ROOT/'tools/evaluation/prefill-recovery/budget_check.cpp','-o',out/'budget-check'],'budget-build.txt')
    run([out/'budget-check'],'budget-result.txt')
    run(['bash',ROOT/'tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',ROOT/'tools/evaluation/prefill-recovery/source.gradle','-PpocketloreTestRunner=org.pocketlore.app.PrefillRecoveryInstrumentation'],'build.log')
    artifacts={}
    for path in ['debug/app-debug.apk','androidTest/debug/app-debug-androidTest.apk']:
        apk=ROOT/'android/app/build/outputs/apk'/path;artifacts[apk.name]={'sha256':sha(apk),'bytes':apk.stat().st_size};shutil.copyfile(apk,out/apk.name);run(adb+['install','-r',apk],'install-'+apk.name+'.txt')
    run(adb+['shell','am','force-stop','org.pocketlore.app'],'stop.txt')
    run(adb+['shell','run-as','org.pocketlore.app','mkdir','-p','files/prefill-recovery-tests'],'mkdir.txt')
    run(adb+['shell','run-as','org.pocketlore.app','sh','-c',"'cat > files/prefill-recovery-tests/cases.json'"],'provision.txt',specfile.read_bytes())
    def instrument(mode):return adb+['shell','am','instrument','-w','-e','mode',mode,'org.pocketlore.app.test/org.pocketlore.app.PrefillRecoveryInstrumentation']
    def read(mode):return run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/prefill-recovery-tests/'+mode+'.json'],mode+'.json')
    # Prevent stale records from being mistaken for this run after a crash.
    run(adb+['shell','run-as','org.pocketlore.app','rm','-f',*['files/prefill-recovery-tests/'+m+'.json' for m in ['lifecycle','kill-ready','restart']]],'clear-results.txt')
    log=run(instrument('lifecycle'),'lifecycle-instrumentation.txt');life=json.loads(read('lifecycle'))
    run(adb+['shell','logcat','-d','--pid='+str(life['pid']),'-v','threadtime'],'lifecycle-logcat.txt')
    assert b'INSTRUMENTATION_CODE: -1' in log and life.get('status')=='PASS',str(out/'lifecycle.json')
    assert life['prefill_observed'][0]==4 and life['prefill_observed'][2]>0 and life['prefill_observed'][3]>=1700
    assert life['prefill_resources'][:2]==[1,1]
    assert all(0<actual<=estimate<=limit for actual,estimate,limit in zip(life['prefill_resources'][2:],life['prefill_observed'][6:],[spec['budget_bytes'][k] for k in ['model','kv','compute']]))
    assert life['prefill_result']==-1 and life['token_callbacks_before_cancel']==life['token_callbacks_after_cancel']==0 and life['prefill_cancel_ms']<5000
    assert life['load_observed'][0]==2 and life['load_observed'][1]>0 and life['closed_load_result']=='Cancelled' and life['close_load_ms']<5000
    assert life['final_resources'][:2]==[0,0] and life['invalid_model_failure']
    # SIGKILL only our own measured app process, after native prefill has started.
    with (out/'kill-instrumentation.txt').open('wb') as logfile:
        proc=subprocess.Popen(list(map(str,instrument('kill-ready'))),stdout=logfile,stderr=subprocess.STDOUT)
        try:
            deadline=time.monotonic()+30;marker=None
            while time.monotonic()<deadline:
                p=subprocess.run(list(map(str,adb+['exec-out','run-as','org.pocketlore.app','cat','files/prefill-recovery-tests/kill-ready.json'])),capture_output=True,timeout=5)
                try:
                    candidate=json.loads(p.stdout)
                    if candidate.get('status')=='READY_FOR_SIGKILL':marker=candidate;break
                    if candidate.get('status')=='FAIL':raise RuntimeError(candidate)
                except json.JSONDecodeError:pass
                time.sleep(.05)
            assert marker is not None,'Native prefill kill marker absent'
            (out/'kill-ready.json').write_text(json.dumps(marker,indent=2)+'\n')
            pid=marker['pid'];assert str(pid) in run(adb+['shell','pidof','org.pocketlore.app'],'pid-before-kill.txt').decode().split()
            assert marker['prefill_observed'][0]==4 and marker['prefill_observed'][2]>0 and marker['token_callbacks_before_cancel']==0
            run(adb+['shell','run-as','org.pocketlore.app','kill','-9',str(pid)],'sigkill.txt');proc.wait(timeout=15)
            exit_info=run(adb+['shell','dumpsys','activity','exit-info','org.pocketlore.app'],'exit-info.txt').decode()
            records=[b for b in exit_info.split('ApplicationExitInfo #') if ('pid='+str(pid)+' ') in b]
            assert len(records)==1 and 'reason=2 (SIGNALED)' in records[0] and 'status=9' in records[0]
            gone=run(adb+['shell','pidof','org.pocketlore.app'],'pid-after-kill.txt',allow=True);assert str(pid) not in gone.decode().split()
        finally:
            if proc.poll() is None:proc.terminate();proc.wait(timeout=10)
    run(adb+['shell','run-as','org.pocketlore.app','ls','-l','files/model.partial','files/pack-140000.partial','files/prefill-notes.partial'],'stages-after-kill.txt')
    log=run(instrument('restart'),'restart-instrumentation.txt');restart=json.loads(read('restart'))
    run(adb+['shell','logcat','-d','--pid='+str(restart['pid']),'-v','threadtime'],'restart-logcat.txt')
    assert b'INSTRUMENTATION_CODE: -1' in log and restart['status']=='PASS' and restart['pid']!=pid,restart
    assert restart['initial_resources'][:2]==[0,0] and restart['final_resources'][:2]==[0,0]
    assert restart['activity_saved_model_ready'] and restart['orphan_stages_removed'] and restart['unrelated_preserved'] and restart['restart_generation']['tokens']>0
    after=run(adb+['shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf','files/knowledge.plpack'],'saved-after.txt');assert before==after
    summary={'status':'PASS','scope':'CPU x86_64 emulator; SIGKILL is not OS OOM; policy rejection is not failed allocation','fixture_sha256':sha(specfile),'artifacts':artifacts,'model_sha256':spec['model_sha256'],'prefill_cancel_ms':life['prefill_cancel_ms'],'close_load_ms':life['close_load_ms'],'killed_pid':pid,'restart_pid':restart['pid'],'failed_real_context_allocations':life['final_operation'][5]+restart['final_operation'][5],'saved_assets_unchanged':before==after,'record_sha256':{n:sha(out/n) for n in ['lifecycle.json','kill-ready.json','restart.json']}}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
