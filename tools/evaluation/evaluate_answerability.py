#!/usr/bin/env python3
"""Frozen development coverage + real JNI on newly recovered cases; preserve every run."""
from pathlib import Path
import datetime,hashlib,json,os,re,subprocess,zipfile
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    out=ROOT/'downloads/answerability'/datetime.datetime.now(datetime.timezone.utc).strftime('run-%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True);print(out,flush=True)
    def run(args,name,**kw):
        p=subprocess.run(list(map(str,args)),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,**kw);(out/name).write_bytes(p.stdout)
        if p.returncode:raise RuntimeError(f'Command failed; see {out/name}')
        return p.stdout
    frozen=ROOT/'tools/evaluation/answerability-cases.json';assert sha(frozen)=='9358ed5398460e9fde4e8e11fb30211b35a554b51cd27ae92e1cd251b8169f98'
    spec=json.loads(frozen.read_text());fixture=ROOT/'evaluation/retrieval/development.json';baseline=ROOT/'docs/evidence/answerability-support/baseline.json'
    assert sha(fixture)==spec['public_fixture_sha256'] and sha(baseline)==spec['baseline_sha256']
    before=json.loads(baseline.read_text());cases=json.loads(fixture.read_text())['cases'];assert len(cases)==30
    run(['python3',ROOT/'tools/evaluation/measure_answer_gate.py','--output',out/'after.json'],'gate.log');after=json.loads((out/'after.json').read_text())
    expected={c['id']:c['question'] for c in cases}
    for report in [before,after]:assert {c['id']:c['question'] for c in report['cases']}==expected
    blocked=lambda r,label:sum(not c['reaches_model_availability'] for c in r['cases'] if c['expected_coverage']==label)
    assert blocked(before,'present')==14 and blocked(before,'absent')==10
    assert blocked(after,'present')<14 and blocked(after,'present')<blocked(before,'present') and blocked(after,'absent')==10
    old={c['id']:c for c in before['cases']};recovered=[c['id'] for c in after['cases'] if c['reaches_model_availability'] and not old[c['id']]['reaches_model_availability']]
    assert set(recovered)==set(spec['positive_ids'])
    assert all(c['reaches_model_availability'] for c in after['cases'] if old[c['id']]['reaches_model_availability'])
    testcases=[{'id':c['id'],'question':c['question']} for c in cases if c['id'] in recovered or c['expected_coverage']=='absent']
    testcases += [{'id':f'additional-absent-{i}','question':q} for i,q in enumerate(spec['additional_absent_questions'])]
    pack=ROOT/'downloads/packs/english-reference.plpack';assert sha(pack)==before['pack_sha256']
    with zipfile.ZipFile(pack) as z:(out/'passages.tsv').write_bytes(z.read('passages.tsv'))
    (out/'controls.tsv').write_text(''.join(('eligible' if c['id'] in recovered else 'blocked')+'\t'+c['question']+'\n' for c in testcases))
    tc=Path(os.environ.get('POCKETLORE_TOOLCHAIN','/home/isa/Android/atlas-toolchain'));classes=out/'classes';classes.mkdir();src=ROOT/'android/app/src/main/java/org/pocketlore/app'
    run([tc/'jdk/bin/javac','-d',classes,*[src/(n+'.java') for n in ['ResearchEngine','EvidencePrompt','AnswerEngine','NativeRuntime']],ROOT/'tools/evaluation/answerability/AnswerabilityCheck.java',ROOT/'android/app/src/test/java/org/pocketlore/app/TemporalScopeCheck.java'],'javac.log')
    run([tc/'jdk/bin/java','-cp',classes,'org.pocketlore.app.AnswerabilityCheck',out/'passages.tsv',out/'controls.tsv'],'coverage-controls.txt')
    run([tc/'jdk/bin/java','-cp',classes,'org.pocketlore.app.TemporalScopeCheck',ROOT/'tools/evaluation/regressions/temporal-scope'],'temporal-regression.txt')
    model_sha='74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db'
    protocol=dict(cases=testcases,pack_sha256=sha(pack),model_sha256=model_sha);(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    adb=[tc/'sdk/platform-tools/adb','-s','emulator-5560']
    assert run(adb+['shell','getprop','sys.boot_completed'],'boot.txt').strip()==b'1'
    assert run(adb+['shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf'],'saved-model.txt').decode().split()[0]==model_sha
    run(['bash',ROOT/'tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',ROOT/'tools/evaluation/answerability/source.gradle','-PpocketloreTestRunner=org.pocketlore.app.AnswerabilityInstrumentation'],'build.log')
    apks=[ROOT/'android/app/build/outputs/apk/debug/app-debug.apk',ROOT/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk']
    identities={p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in apks}
    for p in apks:
        (out/p.name).write_bytes(p.read_bytes());run(adb+['install','-r',p],'install-'+p.name+'.txt')
    run(adb+['shell','am','force-stop','org.pocketlore.app'],'stop.txt')
    run(adb+['shell','run-as','org.pocketlore.app','mkdir','-p','files/answerability-tests'],'mkdir.txt')
    for name,p in [('protocol.json',out/'protocol.json'),('reference.plpack',pack)]:run(adb+['shell','run-as','org.pocketlore.app','sh','-c',"'cat > files/answerability-tests/"+name+"'"],'provision-'+name+'.txt',input=p.read_bytes())
    environment={k:run(adb+['shell',*args],k+'.txt').decode().strip() for k,args in {'fingerprint':['getprop','ro.build.fingerprint'],'abi':['getprop','ro.product.cpu.abi'],'airplane_mode':['settings','get','global','airplane_mode_on']}.items()}
    assert environment['abi']=='x86_64' and environment['airplane_mode']=='1'
    log=run(adb+['shell','am','instrument','-w','org.pocketlore.app.test/org.pocketlore.app.AnswerabilityInstrumentation'],'instrumentation.txt')
    run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/answerability-tests/partial.json'],'partial.json')
    assert b'INSTRUMENTATION_CODE: -1' in log
    raw=run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/answerability-tests/results.json'],'results.json');report=json.loads(raw)
    assert {r['id']:r['question'] for r in report['rows']}=={r['id']:r['question'] for r in testcases} and len(report['rows'])==len(testcases)
    for row in report['rows']:
        if row['id'] in recovered:
            assert row['invoked_model'] and row['tokens']>0 and row['raw_draft'] and row['prompt']
            assert row['kind'] in ['GENERATED','FALLBACK','ABSTAINED']
            if row['kind']=='GENERATED':
                ids=set(re.findall(r'\[([^\[\]]+)\]',row['text']));assert ids and ids<={s['id'] for s in row['sources']}
        else:assert row['kind']=='ABSTAINED' and not row['invoked_model'] and row['tokens']==0
    summary={'status':'PASS','scope':'Current public coverage and real JNI invocation/safety, not semantic or physical acceptance','before_supported_blocked':14,'after_supported_blocked':blocked(after,'present'),'absent_blocked':10,'additional_absent_blocked':len(spec['additional_absent_questions']),'recovered':recovered,'routes':{r['id']:r['kind'] for r in report['rows']},'environment':environment,'model_sha256':model_sha,'pack_sha256':sha(pack),'artifacts':identities,'results_sha256':sha(out/'results.json'),'protocol_sha256':sha(out/'protocol.json'),'fixture_sha256':sha(frozen),'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [src/'EvidencePrompt.java',src/'AnswerEngine.java',ROOT/'tools/evaluation/answerability/AnswerabilityInstrumentation.java']}}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
