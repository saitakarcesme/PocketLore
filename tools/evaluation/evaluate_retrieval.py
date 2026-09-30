#!/usr/bin/env python3
"""Evaluate frozen public retrieval cases using actual production Java. No holdout access."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import time
import zipfile
ROOT=Path(__file__).resolve().parents[2]
def sha(b):return hashlib.sha256(b).hexdigest()
def call(args):
    try:return subprocess.check_output(list(map(str,args)),stderr=subprocess.STDOUT,cwd=ROOT)
    except subprocess.CalledProcessError as error:
        print(error.output.decode(errors='replace'),flush=True)
        raise
def percentile(values,p):
    values=sorted(values);return values[min(len(values)-1,int((len(values)-1)*p))]
def metrics(raw,cases):
    grouped=[];grouped2=[];reciprocal=[];absent=[];distractors=[];failures=[]
    for case,result in zip(cases,raw['cases']):
        assert case['question']==result['query']
        found=[h['id'] for h in result['hits']];groups=case['required_evidence_groups']
        if groups:
            coverage=sum(bool(set(g)&set(found)) for g in groups)/len(groups);grouped.append(coverage)
            grouped2.append(sum(bool(set(g)&set(found[:2])) for g in groups)/len(groups))
            relevant=set(x for g in groups for x in g);rank=next((i+1 for i,x in enumerate(found) if x in relevant),None)
            reciprocal.append(1/rank if rank else 0)
            if coverage<1:failures.append({'id':case['id'],'group_coverage':coverage,'retrieved':found})
        else:
            absent.append(result['lexical_generation_blocked'])
            if not absent[-1]:failures.append({'id':case['id'],'failure':'Absent evidence not blocked by lexical/excerpt gate','retrieved':found})
        distractors.extend(set(found)&set(case['distractor_ids']))
    warm=[t for r in raw['cases'] for t in r['warm_ms']]
    return {'group_coverage_at_4':statistics.mean(grouped),'group_coverage_at_2':statistics.mean(grouped2),'mrr_at_4':statistics.mean(reciprocal),
        'explicit_distractor_hits':len(distractors),'absent_generation_blocked_rate':statistics.mean(absent),
        'present_lexical_generation_blocked':sum(r['lexical_generation_blocked'] for c,r in zip(cases,raw['cases']) if c['required_evidence_groups']),
        'mean_candidates_scored':statistics.mean(r['candidates_scored'] for r in raw['cases'][:len(cases)]),'index_ms':raw['index_ms'],'timing_query_count':len(raw['cases']),'warm_p50_ms':percentile(warm,.5),'warm_p95_ms':percentile(warm,.95),'failures':failures}
def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline-only',action='store_true');p.add_argument('--host-only',action='store_true',help='Diagnostic only; full acceptance requires the existing emulator');a=p.parse_args()
    start=time.monotonic();manifest=json.loads((ROOT/'evaluation/retrieval/manifest.json').read_text())
    fixture=(ROOT/'evaluation/retrieval/development.json').read_bytes();assert sha(fixture)==manifest['cases_sha256'],'Frozen development changed'
    cases=json.loads(fixture)['cases'];assert len(cases)==manifest['case_count']
    pilot=(ROOT/'evaluation/development.json').read_bytes();assert sha(pilot)==manifest['pilot_development_sha256'],'Original pilot changed'
    pack=ROOT/'downloads/packs/english-reference.plpack';assert sha(pack.read_bytes())==manifest['pack_sha256'],'Pinned knowledge pack missing or changed; see docs/KNOWLEDGE_PACKS.md'
    out=ROOT/'downloads/evaluation'/datetime.now(timezone.utc).strftime('retrieval-%Y%m%dT%H%M%S.%fZ');out.mkdir(parents=True)
    with zipfile.ZipFile(pack) as z:payload=z.read('passages.tsv')
    (out/'passages.tsv').write_bytes(payload)
    rowids={line.split('\t')[0] for line in payload.decode().splitlines()}
    for c in cases:
        assert set(c['distractor_ids'])<=rowids
        assert all(set(g)<=rowids and g for g in c['required_evidence_groups'])
    pilot_cases=json.loads(pilot)['cases']
    queries=[c['question'] for c in cases]+[c['question'] for c in pilot_cases]
    assert all('\n' not in q and '\r' not in q for q in queries)
    (out/'queries.txt').write_text('\n'.join(queries)+'\n')
    tc=Path(os.environ.get('POCKETLORE_TOOLCHAIN','/home/isa/Android/atlas-toolchain'))
    java=tc/'jdk/bin/java';javac=tc/'jdk/bin/javac'
    reports={};identities={}
    for name in (['baseline'] if a.baseline_only else ['baseline','candidate']):
        directory=out/name;directory.mkdir();sources=[]
        for filename in ['ResearchEngine.java','EvidencePrompt.java']:
            path='android/app/src/main/java/org/pocketlore/app/'+filename
            src=call(['git','show',manifest['baseline_commit']+':'+path]) if name=='baseline' else (ROOT/path).read_bytes()
            if name=='baseline' and filename=='ResearchEngine.java':assert sha(src)==manifest['baseline_source_sha256']
            (directory/filename).write_bytes(src);sources.append(directory/filename)
            identities[name+'_'+filename]=sha(src)
        call([javac,'-d',directory,*sources,ROOT/'tools/evaluation/RetrievalHarness.java'])
        runs=[]
        for fork in range(3):
            raw=call([java,'-cp',directory,'org.pocketlore.app.RetrievalHarness',out/'passages.tsv',out/'queries.txt'])
            (out/f'{name}-{fork}.json').write_bytes(raw);parsed=json.loads(raw)
            # Same IDs/scores/coverage across independent JVM forks; timings deliberately differ.
            if runs:
                for before,after in zip(runs[0]['cases'],parsed['cases']):
                    assert before['hits']==after['hits'] and before['missing_terms']==after['missing_terms'],'Fork nondeterminism'
            runs.append(parsed)
        reports[name]=[metrics(r,cases) for r in runs]
    summary={'environment':'LLMRig host JVM; not Android or physical device','cases_sha256':manifest['cases_sha256'],'pack_sha256':manifest['pack_sha256'],'source_hashes':identities,'reports':reports,'wall_seconds':time.monotonic()-start,'pilot':'Eight unchanged public pilot questions recorded raw after the 30 scored cases; no holdout opened','status':'BASELINE_ONLY' if a.baseline_only else 'PENDING'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    if not a.baseline_only:
        contract=ROOT/'android/app/src/test/java/org/pocketlore/app/RetrievalIndexCheck.java'
        call([javac,'-cp',out/'candidate','-d',out/'candidate',contract])
        (out/'index-contract.txt').write_bytes(call([java,'-cp',out/'candidate','org.pocketlore.app.RetrievalIndexCheck',out/'passages.tsv']))
        b=reports['baseline'][0];c=reports['candidate'][0];policy=manifest['acceptance_policy']
        baseline_raw=json.loads((out/'baseline-0.json').read_text())['cases']
        candidate_raw=json.loads((out/'candidate-0.json').read_text())['cases']
        analysis=[]
        for case,before,after in zip(cases,baseline_raw,candidate_raw):
            def describe(row):
                ids=[h['id'] for h in row['hits']];groups=case['required_evidence_groups']
                return {'ids':ids,'covered_groups':[i for i,g in enumerate(groups) if set(g)&set(ids)],
                    'explicit_distractors':sorted(set(ids)&set(case['distractor_ids'])),
                    'lexical_generation_blocked':row['lexical_generation_blocked'],'missing_terms':row['missing_terms'],'excerpt_uncovered':row['excerpt_uncovered']}
            analysis.append({'id':case['id'],'tags':case['tags'],'expected_coverage':case['expected_coverage'],'baseline':describe(before),'candidate':describe(after)})
        (out/'failure-analysis.json').write_text(json.dumps(analysis,indent=2)+'\n')
        checks={'group_coverage_floor':c['group_coverage_at_4']>=policy['minimum_group_coverage'],'mrr_floor':c['mrr_at_4']>=policy['minimum_mrr'],'group_coverage_no_regression':c['group_coverage_at_4']>=b['group_coverage_at_4'],'mrr_no_regression':c['mrr_at_4']>=b['mrr_at_4'],'absent_evidence_blocked':c['absent_generation_blocked_rate']>=policy['minimum_absent_blocked'],
            'measured_improvement':c['group_coverage_at_4']>b['group_coverage_at_4'] or c['mean_candidates_scored']<b['mean_candidates_scored']}
        if not a.host_only:
            adb=[tc/'sdk/platform-tools/adb','-s',os.environ.get('ANDROID_SERIAL','emulator-5560')]
            assert str(adb[2]).startswith('emulator-'),'Android measurements here are emulator-only'
            assert call(adb+['shell','getprop','sys.boot_completed']).strip()==b'1','Existing emulator must be booted; no emulator is launched by this check'
            (out/'android-build.log').write_bytes(call(['bash','tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-PpocketloreTestRunner=org.pocketlore.app.RetrievalSmokeInstrumentation']))
            app=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk'
            test=ROOT/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk'
            for apk in (app,test):call(adb+['install','-r',apk])
            call(adb+['shell','run-as','org.pocketlore.app','mkdir','-p','files/retrieval-tests'])
            for name,path in [('reference.plpack',pack),('expected.json',out/'candidate-0.json')]:
                command=[str(x) for x in adb]+['shell','run-as','org.pocketlore.app','sh','-c',"'cat > files/retrieval-tests/"+name+"'"]
                subprocess.run(command,input=path.read_bytes(),check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            result=call(adb+['shell','am','instrument','-w','org.pocketlore.app.test/org.pocketlore.app.RetrievalSmokeInstrumentation'])
            (out/'android-instrumentation.txt').write_bytes(result)
            assert b'INSTRUMENTATION_CODE: -1' in result,result.decode()
            line=next(line for line in result.decode().splitlines() if line.startswith('INSTRUMENTATION_RESULT: report='))
            report=json.loads(line.split('report=',1)[1]);assert report['passed'] and report['pack_sha256']==manifest['pack_sha256']
            assert len(report['cases'])==len(queries)
            (out/'android.json').write_text(json.dumps(report,indent=2)+'\n')
            timing=[t for c in report['cases'] for t in c['warm_ms']]
            summary['android']={'environment':report['environment'],'validated_archive_and_index_ms':report['validated_archive_and_index_ms'],'warm_p50_ms':percentile(timing,.5),'warm_p95_ms':percentile(timing,.95),'parity_cases':len(report['cases']),'apk_sha256':sha(app.read_bytes()),'test_apk_sha256':sha(test.read_bytes())}
            checks['android_production_parity']=True
        summary.update(checks=checks,status=('HOST_ONLY' if a.host_only else 'PASS') if all(checks.values()) else 'FAIL',wall_seconds=time.monotonic()-start);(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(out);print(json.dumps(summary,indent=2))
    if summary['status']=='FAIL':raise SystemExit(1)
if __name__=='__main__':main()
