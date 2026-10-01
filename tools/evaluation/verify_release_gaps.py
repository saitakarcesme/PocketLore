#!/usr/bin/env python3
"""Recompute public evidence metrics and verify actionable gap/task coverage, with mutations."""
from pathlib import Path
from collections import Counter
import copy,hashlib,json,re,sys,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/evidence/release-gap-review'
QUEUE=Path('/home/isa/PocketLore-control/tasks')
GATES={'Useful research','Android installation','GrapheneOS','Resource limits','Offline use','Usable speed','Honest comparison','Public delivery'}
def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def derive():
    fixture=read(ROOT/'evaluation/retrieval/development.json')['cases']
    raw=read(ROOT/'docs/evidence/retrieval/final/candidate-0.json')['cases']
    by_question={r['query']:r for r in raw}
    present=blocked=absent=absent_blocked=distractors=0
    for c in fixture:
        row=by_question[c['question']];ids={h['id'] for h in row['hits']}
        distractors+=len(ids & set(c['distractor_ids']))
        if c['expected_coverage']=='present':present+=1;blocked+=int(row['lexical_generation_blocked'])
        else:absent+=1;absent_blocked+=int(row['lexical_generation_blocked'])
    def routes(path,key,select=lambda r:True):
        rows=[r for r in read(ROOT/path)[key] if select(r)]
        return dict(sorted(Counter(r['kind'] for r in rows).items()))
    comparison=read(ROOT/'docs/evidence/comparison/run-v1/results.json')['rows']
    times=[r['end_to_end_ms'] for r in comparison if r['system']=='pocketlore' and r['tokens']>0]
    manifest=read(ROOT/'docs/evidence/release-v3/manifest.json')
    current=read(BASE/'current-answer-gate.json')['cases']
    current_counts={label:sum(not r['reaches_model_availability'] for r in current if r['expected_coverage']==label) for label in ['present','absent']}
    return {'current_pre_model_blocked':current_counts,'measurement_class':'Derived public development host/emulator evidence, not new phone or quality measurements','retrieval':{'present':present,'supported_blocked':blocked,'absent':absent,'absent_blocked':absent_blocked,'explicit_distractor_hits':distractors},'comparison_routes':routes('docs/evidence/comparison/run-v1/results.json','rows',lambda r:r['system']=='pocketlore'),'synthesis_routes':routes('docs/evidence/synthesis/repair-1/results.json','cases'),'fresh_demo_routes':routes('docs/evidence/release-v3/cycle-1-loaded-result.json','cases'),'comparison_inference_ms_range':[min(times),max(times)],'candidate_apk':manifest['artifacts']['android/app/build/outputs/apk/debug/app-debug.apk']}
def validate(plan,metrics,queue=QUEUE):
    assert plan['schema']==1 and plan['release_complete'] is False
    assert {g['gate'] for g in plan['gates']}==GATES
    assert len({g['id'] for g in plan['gates']})==len(plan['gates'])
    referenced=set()
    for g in plan['gates']:
        assert g['status'] in ['rig_work','mixed','external']
        assert g['next_action'] and g['external_dependency'] and g['evidence']
        for p in g['evidence']:assert p in plan['evidence_sha256']
        if g['status']!='external':assert g['task_ids'],'Rig work lacks concrete task'
        else:assert not g['task_ids']
        referenced.update(g['task_ids'])
    assert referenced==set(plan['tasks']) and referenced
    for ident,t in plan['tasks'].items():
        assert ident==t['id'] and t['dependencies']==['110-release-gap-review']
        assert all(t[k] for k in ['objective','scope','artifacts','acceptance_checks','prompt'])
        assert ['bash','tools/android-build.sh'] in t['acceptance_checks']
        assert len(t['acceptance_checks'])>=2 and all(isinstance(c,list) and c and all(isinstance(x,str) for x in c) for c in t['acceptance_checks'])
        assert all(p.startswith('docs/evidence/') for p in t['artifacts'])
        assert json.dumps(t,ensure_ascii=False).isascii()
        assert read(queue/(ident+'.json'))==t,'Queued task drift: '+ident
    for p,h in plan['evidence_sha256'].items():
        assert not Path(p).is_absolute() and '..' not in Path(p).parts and 'holdout' not in p.lower()
        assert sha(ROOT/p)==h,p
    assert metrics==derive(),'Derived evidence was changed'
    snapshot=read(BASE/'emulator-snapshot.json')['commands']
    assert all(row['exit_code']==0 for row in snapshot.values())
    assert snapshot['installed_apk_hash']['output'].split()[0]==metrics['candidate_apk']['sha256']
    assert re.search(r'TOTAL PSS:\s+[1-9][0-9]*',snapshot['memory']['output'])
    assert {line.split()[1] for line in snapshot['owned_disk']['output'].splitlines()}=={'files','cache','code_cache'}
    apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk'
    assert sha(apk)==metrics['candidate_apk']['sha256'] and apk.stat().st_size==metrics['candidate_apk']['bytes']
def main():
    plan=read(BASE/'plan.json');metrics=derive()
    with tempfile.TemporaryDirectory() as directory:
        output=Path(directory)/'gate.json'
        subprocess.run([sys.executable,str(ROOT/'tools/evaluation/measure_answer_gate.py'),'--output',str(output)],check=True,stdout=subprocess.PIPE)
        actual=read(output);recorded=read(BASE/'current-answer-gate.json')
        assert actual['source_sha256']==recorded['source_sha256']
        assert actual['fixture_sha256']==recorded['fixture_sha256'] and actual['pack_sha256']==recorded['pack_sha256']
        strip_time=lambda rows:[{k:v for k,v in r.items() if k!='host_routing_ms'} for r in rows]
        assert strip_time(actual['cases'])==strip_time(recorded['cases']), 'Current production routing drift'
    if '--record' in sys.argv:(BASE/'derived.json').write_text(json.dumps(metrics,indent=2)+'\n')
    stored=read(BASE/'derived.json');validate(plan,stored)
    for kind in ['false_completion','missing_gate','missing_task','missing_dependency','tampered_metric','missing_evidence']:
        p,m=copy.deepcopy((plan,stored))
        if kind=='false_completion':p['release_complete']=True
        elif kind=='missing_gate':p['gates']=[g for g in p['gates'] if g['gate']!='GrapheneOS']
        elif kind=='missing_task':p['gates'][0]['task_ids']=[]
        elif kind=='missing_dependency':next(iter(p['tasks'].values()))['dependencies']=[]
        elif kind=='tampered_metric':m['retrieval']['supported_blocked']=0
        else:p['evidence_sha256'][next(iter(p['evidence_sha256']))]='0'*64
        try:validate(p,m)
        except AssertionError:pass
        else:raise AssertionError('Mutation escaped: '+kind)
    print('PASS: executed current host pre-model routing and recomputed public raw metrics, exact candidate identity, eight goal categories, hashed evidence, seven queued task specifications and six rejected mutations.')
    print('Release work remains INCOMPLETE; validation is audit consistency, not acceptance or a semantic proof of completeness.')
if __name__=='__main__':main()
