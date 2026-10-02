#!/usr/bin/env python3
"""Freeze candidate evidence; no unseen questions or rival execution."""
import pathlib,sys,subprocess,json,hashlib,time
ROOT=pathlib.Path(__file__).resolve().parents[3]
HERE=pathlib.Path(__file__).parent
sys.path.insert(0,str(HERE));import journeys
if '--device' in sys.argv:
    before=set((ROOT/'downloads/frozen-candidate').glob('*')) if (ROOT/'downloads/frozen-candidate').exists() else set()
    sys.argv=[sys.argv[0]]
    try:journeys.main()
    finally:
        for out in set((ROOT/'downloads/frozen-candidate').glob('*'))-before:
            if not out.is_dir():continue
            # This final capture cannot erase the original invocation or substitute a recovered pass.
            for name,args in [('final-observed-boot',['cat','/proc/sys/kernel/random/boot_id']),('final-observed-font',['settings','get','system','font_scale']),('final-observed-memory',['dumpsys','meminfo','org.pocketlore.app'])]:
                r=subprocess.run(journeys.ADB+['shell',*args],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30);(out/(name+'.txt')).write_bytes(r.stdout);(out/(name+'.exit')).write_text(str(r.returncode))
            files={str(p.relative_to(out)):journeys.sha(p) for p in out.rglob('*') if p.is_file()}
            (out/'invocation-seal.json').write_text(json.dumps({'files':files,'has_passing_manifest':(out/'manifest.json').exists()},indent=2)+'\n')
else:
    frozen=json.loads((ROOT/'docs/evidence/frozen-candidate/freeze.json').read_text());out=pathlib.Path(frozen['journey_run']);m=journeys.verify(out)
    assert journeys.sha(out/'invocation-seal.json')==frozen['invocation_seal_sha256']
    for n,h in json.loads((out/'source-inputs.json').read_text())['files'].items():assert journeys.sha(ROOT/n)==h,n
    assert m['apk_sha256']==frozen['apk_sha256']
    assert frozen['status']=='ready_for_separate_evaluation','Candidate remains incomplete'
    print(json.dumps({'status':'PASS','freeze':frozen['id'],'quality':'unseen/matched comparison not run'}))
