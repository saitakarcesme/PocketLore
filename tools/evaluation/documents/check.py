"""Live Android behavior checks. Every run gets an immutable separate output directory."""
import hashlib,json,os,subprocess,time,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
ADB=Path('/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb')
SERIAL=os.environ.get('POCKETLORE_DOCUMENTS_SERIAL','emulator-5560')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(p,identity):
    assert p.is_file() and p.stat().st_size==identity['bytes'] and sha(p)==identity['sha256'],f'Artifact missing or changed: {p}'
def main():
    fixtures=ROOT/'downloads/documents-fixtures';spec=json.loads((ROOT/'docs/evidence/documents/fixtures.json').read_text())
    for name,identity in spec['files'].items():verify(fixtures/name,identity)
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)/'notes.txt';p.write_bytes((fixtures/'notes.txt').read_bytes()+b'x')
        for kind in ('changed','missing'):
            if kind=='missing':p.unlink()
            try:verify(p,spec['files']['notes.txt'])
            except AssertionError:pass
            else:raise AssertionError(f'{kind} artifact accepted')
    stamp=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime());out=ROOT/'downloads/documents-runs'/stamp;out.mkdir(parents=True,exist_ok=False)
    adb=[str(ADB),'-s',SERIAL]
    def run(cmd,name,data=None,timeout=300):
        r=subprocess.run(list(map(str,cmd)),cwd=ROOT,input=data,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
        (out/name).write_bytes(r.stdout)
        if r.returncode:raise RuntimeError(f'{name}: exit {r.returncode}; see {out}')
        return r.stdout
    assert run(adb+['get-state'],'state.txt').strip()==b'device'
    assert run(adb+['shell','getprop','sys.boot_completed'],'boot.txt').strip()==b'1'
    run(adb+['shell','getprop'],'properties.txt')
    before=run(adb+['shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf','files/pack-library/catalog.json'],'saved-before.txt')
    run(['bash','tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',ROOT/'tools/evaluation/documents/source.gradle','-PpocketloreTestRunner=org.pocketlore.app.DocumentsInstrumentation'],'build.log')
    identities={}
    for relative in ['debug/app-debug.apk','androidTest/debug/app-debug-androidTest.apk']:
        p=ROOT/'android/app/build/outputs/apk'/relative;identities[p.name]={'sha256':sha(p),'bytes':p.stat().st_size};run(adb+['install','-r',p],'install-'+p.name+'.txt')
    # Only task-owned fixtures; no app reset, service restart or unrelated asset deletion.
    run(adb+['shell','run-as','org.pocketlore.app','mkdir','-p','files/documents-input'],'mkdir.txt')
    run(adb+['shell','run-as','org.pocketlore.app.test','mkdir','-p','files'],'mkdir-provider.txt')
    for name in spec['files']:
        for package,folder in [('org.pocketlore.app','files/documents-input'),('org.pocketlore.app.test','files')]:
            run(adb+['shell','run-as',package,'sh','-c',"'cat > "+folder+'/'+name+"'"],f'push-{package}-{name}.txt',(fixtures/name).read_bytes())
    directory='documents-test-'+stamp
    instrument=run(adb+['shell','am','instrument','-w','-e','directory',directory,'org.pocketlore.app.test/org.pocketlore.app.DocumentsInstrumentation'],'instrumentation.txt',timeout=240)
    after=run(adb+['shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf','files/pack-library/catalog.json'],'saved-after.txt')
    if b'Process crashed' in instrument:
        run(adb+['logcat','-d','-t','200','-s','AndroidRuntime'],'crash.txt')
        raise AssertionError(f'Instrumentation crashed; evidence retained in {out}')
    raw=run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/'+directory+'/results.json'],'results.json');report=json.loads(raw)
    run(adb+['shell','dumpsys','package','org.pocketlore.app'],'package.txt')
    receipt={'serial':SERIAL,'artifacts':identities,'fixture_manifest_sha256':sha(ROOT/'docs/evidence/documents/fixtures.json'),'results_sha256':sha(out/'results.json'),'saved_assets_unchanged':before==after,'artifact_mutations_rejected':['changed','missing'],'status':report['status']}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    assert b'DOCUMENTS_PASS' in instrument and report['status']=='PASS',f'{out}: {report.get("error",instrument.decode())}'
    assert before==after,'Saved model or existing catalog changed'
    required={'quoted_csv_exact_multiline_record','json_pointer_exact_values','real_pdf_text_page_location','five_searchable_documents','disabled_sources_excluded_after_catalog_reopen','portable_export_exact_bytes','portable_reimport_identity_and_search','cancel_before_read','cancel_during_copy','cancel_library_transaction','cancel_export','input_limit_rejected','ninth_collection_rejected','actual_source_dialog_offsets_owner_exact_text','actual_provider_export_hash','provider_cancel_under_1500ms','live_catalog_restored_exactly'}
    assert required.issubset(report['checks'])
    for name in ['source-dialog.txt','source-dialog.png']:
        run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/'+directory+'/'+name],name)
    run(adb+['shell','am','force-stop','org.pocketlore.app'],'restart-stop.txt')
    restarted=run(adb+['shell','am','instrument','-w','-e','directory',directory,'-e','phase','restart','org.pocketlore.app.test/org.pocketlore.app.DocumentsInstrumentation'],'restart-instrumentation.txt')
    restart=json.loads(run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/'+directory+'/restart.json'],'restart.json'))
    assert restart['status']=='PASS' and restart['retained_collections']==7
    print(json.dumps({'status':'PASS','output':str(out),'checks':len(report['checks']),'receipt':receipt},indent=2))
if __name__=='__main__':main()
