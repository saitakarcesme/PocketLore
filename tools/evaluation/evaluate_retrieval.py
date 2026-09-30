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
def call(args):return subprocess.check_output(list(map(str,args)),stderr=subprocess.STDOUT,cwd=ROOT)
def percentile(values,p):
    values=sorted(values);return values[min(len(values)-1,int((len(values)-1)*p))]
def metrics(raw,cases):
    grouped=[];reciprocal=[];absent=[];distractors=[];failures=[]
    for case,result in zip(cases,raw['cases']):
        assert case['question']==result['query']
        found=[h['id'] for h in result['hits']];groups=case['required_evidence_groups']
        if groups:
            coverage=sum(bool(set(g)&set(found)) for g in groups)/len(groups);grouped.append(coverage)
            relevant=set(x for g in groups for x in g);rank=next((i+1 for i,x in enumerate(found) if x in relevant),None)
            reciprocal.append(1/rank if rank else 0)
            if coverage<1:failures.append({'id':case['id'],'group_coverage':coverage,'retrieved':found})
        else:
            absent.append(result['lexical_generation_blocked'])
            if not absent[-1]:failures.append({'id':case['id'],'failure':'Absent evidence not blocked by lexical/excerpt gate','retrieved':found})
        distractors.extend(set(found)&set(case['distractor_ids']))
    warm=[t for r in raw['cases'] for t in r['warm_ms']]
    return {'group_coverage_at_4':statistics.mean(grouped),'mrr_at_4':statistics.mean(reciprocal),
        'explicit_distractor_hits':len(distractors),'absent_generation_blocked_rate':statistics.mean(absent),
        'present_lexical_generation_blocked':sum(r['lexical_generation_blocked'] for c,r in zip(cases,raw['cases']) if c['required_evidence_groups']),
        'index_ms':raw['index_ms'],'warm_p50_ms':percentile(warm,.5),'warm_p95_ms':percentile(warm,.95),'failures':failures}
def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline-only',action='store_true');a=p.parse_args()
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
        b=reports['baseline'][0];c=reports['candidate'][0];policy=manifest['acceptance_policy']
        checks={'group_coverage_floor':c['group_coverage_at_4']>=policy['minimum_group_coverage'],'mrr_floor':c['mrr_at_4']>=policy['minimum_mrr'],'group_coverage_no_regression':c['group_coverage_at_4']>=b['group_coverage_at_4'],'absent_evidence_blocked':c['absent_generation_blocked_rate']>=policy['minimum_absent_blocked'],
            'measured_improvement':c['group_coverage_at_4']>b['group_coverage_at_4'] or statistics.median(r['warm_p50_ms'] for r in reports['candidate'])<statistics.median(r['warm_p50_ms'] for r in reports['baseline'])}
        summary.update(checks=checks,status='PASS' if all(checks.values()) else 'FAIL');(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(out);print(json.dumps(summary,indent=2))
    if summary['status']=='FAIL':raise SystemExit(1)
if __name__=='__main__':main()
