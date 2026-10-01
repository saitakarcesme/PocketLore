#!/usr/bin/env python3
"""Verify exact candidate bytes, reproducible pack, host behavior and measured demo records."""
import argparse,copy,hashlib,importlib.util,json,os,subprocess,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'docs/evidence/release'
MANIFEST=EVIDENCE/'manifest.json'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def run(args):
    p=subprocess.run(list(map(str,args)),cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if p.returncode:raise RuntimeError(p.stdout.decode(errors='replace'))
    return p.stdout.decode()
def check_demo(summary,loaded,fresh):
    assert summary['environment'].startswith('Existing AOSP x86_64 emulator')
    assert len(summary['checks'])==10 and summary['status']=='PASS'
    required={'airplane_mode_on','internet_permission_denied','socket_denied_by_application_uid','real_offline_inference_0','real_offline_inference_1','unsupported_abstention_0','unsupported_abstention_1','cancel_discards_real_partial_draft','activity_recreated','recreation_discards_prior_draft','inference_after_recreation','source_dialog_opened'}
    assert set(loaded['checks'])==required and loaded['status']=='PASS'
    assert 'EPERM' in loaded['socket_probe'] or 'EACCES' in loaded['socket_probe']
    assert loaded['cancel_ms']>=0 and loaded['elapsed_ms']>0
    expected=['Compare evaporation and condensation','What is groundwater?','quasar supernova','Does evaporation cure diabetes?']
    assert [c['question'] for c in loaded['cases']]==expected
    for i,c in enumerate(loaded['cases']):
        assert c['total_ms']>=0 and c['text']
        if i<2:assert c['invoked_model'] and c['tokens']>0 and c['raw_draft'] and c['prompt'] and c['kind'] in ['GENERATED','FALLBACK']
        else:assert not c['invoked_model'] and c['tokens']==0 and c['kind']=='ABSTAINED'
    assert len(fresh)==2
    for r in fresh:
        assert len(r['checks'])==6 and 'no_restored_model_or_pack' in r['checks'] and r['status']=='PASS'
        assert r['cases'][0]['kind']=='FALLBACK' and not r['cases'][0]['invoked_model']
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--freeze',type=Path,help='Explicitly archive a completed fresh offline demo and freeze local candidate identities');args=parser.parse_args()
    tc=Path(os.environ.get('POCKETLORE_TOOLCHAIN','/home/isa/Android/atlas-toolchain'))
    apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk'
    if args.freeze:
        source=args.freeze.resolve();EVIDENCE.mkdir(parents=True,exist_ok=True)
        names=['summary.json','cycle-1-loaded-result.json','cycle-1-fresh-result.json','cycle-2-fresh-result.json','permissions.txt','runtime-dependencies.txt','fingerprint.txt','abi.txt']
        for name in names:(EVIDENCE/name).write_bytes((source/name).read_bytes())
        # No app-data tar, model weights, private logs or control state are archived in Git.
        artifacts=[apk,ROOT/'downloads/answers/model/qwen2.5-0.5b-instruct-q4_k_m.gguf',ROOT/'downloads/packs/english-reference.plpack']
        manifest={'schema':1,'candidate':'development debug; not accepted release','demo_run':source.name,'source_commit':run(['git','rev-parse','HEAD']).strip(),'build_tools':{'jdk':'Temurin 17.0.20.1+1','gradle':'8.13','android_gradle_plugin':'8.9.2','sdk':'35','build_tools':'35.0.0','ndk':'r27c','cmake':'3.22.1'},'runtime':{'llama_cpp_revision':'bb4caa7540188872173c44d161602d9271386413','license':'MIT','backends':['CPU'],'abis':['arm64-v8a','x86_64'],'java_runtime_dependencies':[], 'static_support':['NDK libc++ and compiler runtime; toolchain licenses apply'], 'ndk_notice_sha256':sha(tc/'android-ndk-r27c/toolchains/llvm/prebuilt/linux-x86_64/NOTICE')},'artifacts':{str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in artifacts},'apk_entries':{},'evidence':{n:sha(EVIDENCE/n) for n in names},'source_locks':{str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'tools/runtime/pins.env',ROOT/'tools/answers/model.env',ROOT/'tools/packs/sources.lock.json',ROOT/'tools/packs/travel-sources.lock.json',ROOT/'android/knowledge-sources.json']}}
        with zipfile.ZipFile(apk) as z:
            manifest['apk_entries']={n:{'bytes':len(z.read(n)),'sha256':hashlib.sha256(z.read(n)).hexdigest()} for n in z.namelist() if n.startswith(('assets/','lib/'))}
        MANIFEST.write_text(json.dumps(manifest,indent=2)+'\n')
    m=json.loads(MANIFEST.read_text())
    for name,identity in m['artifacts'].items():
        p=ROOT/name;assert p.stat().st_size==identity['bytes'] and sha(p)==identity['sha256'],name
    for name,h in m['source_locks'].items():assert sha(ROOT/name)==h,name
    for name,h in m['evidence'].items():assert sha(EVIDENCE/name)==h,name
    with zipfile.ZipFile(apk) as z:
        actual={n:{'bytes':len(z.read(n)),'sha256':hashlib.sha256(z.read(n)).hexdigest()} for n in z.namelist() if n.startswith(('assets/','lib/'))}
        assert actual==m['apk_entries']
        for abi in ['arm64-v8a','x86_64']:assert z.read('lib/'+abi+'/libpocketlore.so')[:4]==b'\x7fELF'
        for name in ['llama.cpp.txt','qwen2.5-Apache-2.0.txt','answer-model-notice.txt','travel-wikidata-notice.txt']:assert len(z.read('assets/licenses/'+name))>100
    permissions=run([tc/'sdk/build-tools/35.0.0/aapt','dump','permissions',apk]);assert 'uses-permission:' not in permissions
    deps=run(['bash','tools/android-build.sh',':app:dependencies','--configuration','debugRuntimeClasspath']);assert 'No dependencies' in deps
    summary=json.loads((EVIDENCE/'summary.json').read_text());loaded=json.loads((EVIDENCE/'cycle-1-loaded-result.json').read_text());fresh=[json.loads((EVIDENCE/f'cycle-{i}-fresh-result.json').read_text()) for i in [1,2]]
    check_demo(summary,loaded,fresh)
    assert summary['artifacts'][apk.name]==m['artifacts'][str(apk.relative_to(ROOT))]
    for name in ['qwen2.5-0.5b-instruct-q4_k_m.gguf','english-reference.plpack']:
        assert summary['artifacts'][name]==next(v for p,v in m['artifacts'].items() if Path(p).name==name)
    for mutation in ['no_inference','wrong_question','fresh_restore','missing_cancel']:
        s,l,f=copy.deepcopy((summary,loaded,fresh))
        if mutation=='no_inference':l['cases'][0]['invoked_model']=False
        elif mutation=='wrong_question':l['cases'][0]['question']='substituted'
        elif mutation=='fresh_restore':f[0]['checks'].remove('no_restored_model_or_pack')
        else:l['checks'].remove('cancel_discards_real_partial_draft')
        try:check_demo(s,l,f)
        except AssertionError:pass
        else:raise AssertionError('Mutation escaped: '+mutation)
    spec=importlib.util.spec_from_file_location('release_pack',ROOT/'tools/packs/build_pack.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory() as directory:
        a,_=module.build(output=Path(directory)/'a.plpack');b,_=module.build(output=Path(directory)/'b.plpack')
        assert a.read_bytes()==b.read_bytes()==(ROOT/'downloads/packs/english-reference.plpack').read_bytes()
    print(run(['bash','tools/android-check.sh']).strip())
    print('PASS: exact candidate bytes/ABIs/licenses/permissions/dependencies, two pack rebuilds, host retrieval behavior, measured fresh-demo integrity and four negative mutations.')
    print('Demo evidence replay only: run bash tools/evaluation/check_offline.sh for a new destructive emulator demonstration. No physical, quality, signing or competitive acceptance.')
if __name__=='__main__':main()
