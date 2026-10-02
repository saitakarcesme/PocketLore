#!/usr/bin/env python3
"""Freeze candidate evidence; no unseen questions or rival execution."""
import pathlib,sys,subprocess,json,hashlib,time,tempfile,copy
ROOT=pathlib.Path(__file__).resolve().parents[3]
HERE=pathlib.Path(__file__).parent
sys.path.insert(0,str(HERE));import journeys

def verify(frozen):
 out=pathlib.Path(frozen['journey_run']);m=journeys.verify(out)
 assert journeys.sha(out/'invocation-seal.json')==frozen['invocation_seal_sha256']
 source=json.loads((out/'source-inputs.json').read_text())
 for n,h in source['files'].items():
  actual=journeys.sha(ROOT/n)
  if actual!=h:
   assert n=='tools/evaluation/frozen-candidate/check.py','Tested build input changed: '+n
   assert frozen['audit_only_change']=={'path':n,'tested_sha256':h,'current_sha256':actual}
 for name,pin in frozen['artifacts'].items():assert journeys.sha(pathlib.Path(name))==pin,name
 for row in m['reports']:
  folder=out/pathlib.Path(row['file']).parent
  with tempfile.TemporaryDirectory() as temp:
   decoded=pathlib.Path(temp);journeys.stream_evidence((out/row['transport']).read_text(),m['run_id'],decoded)
   for p in decoded.iterdir():assert p.read_bytes()==(folder/p.name).read_bytes(),'Stream/decoded mismatch'
 assert m['apk_sha256']==frozen['apk_sha256']
 assert frozen['profile']['mode']=='source_brief' and frozen['profile']['generated_quality']=='not measured'
 assert frozen['profile']['production_model_selected'] is False
 budget=json.loads(pathlib.Path(frozen['budget_path']).read_text())
 assert budget['verified_shards']==31 and budget['hard_fits'] and budget['target_fits']
 warm=json.loads((out/'brief-warm/install.json').read_text())
 assert [x['id'] for x in warm['outputs']]==['g01','g21','g24']+['g01']*5
 assert all(not x['generated'] for x in warm['outputs']) and not warm['outputs'][2]['quotes']
 for r in warm['outputs']:
  text=r['rendered'].encode('utf-16-le')
  for q in r['quotes']:assert text[2*q['display_start']:2*q['display_end']].decode('utf-16-le')==q['text'] and hashlib.sha256(q['text'].encode()).hexdigest()==q['sha256']
 assert frozen['status']=='ready_for_separate_source_brief_evaluation','Candidate remains incomplete'
 return m

def audit():
 frozen=json.loads((ROOT/'docs/evidence/frozen-candidate/freeze.json').read_text());m=verify(frozen)
 controls=[]
 for kind in ['changed-apk','wrong-profile','missing-shard']:
  changed=copy.deepcopy(frozen)
  if kind=='changed-apk':changed['apk_sha256']='0'*64
  elif kind=='wrong-profile':changed['profile']['mode']='generated'
  else:changed['budget_path']='/nonexistent-pocketlore-fixture'
  try:verify(changed)
  except (AssertionError,FileNotFoundError):controls.append(kind)
  else:raise AssertionError('Invalid freeze accepted')
 # Existing actual missing/changed/stale/raw-identity controls stay bound in run evidence.
 negatives=json.loads((pathlib.Path(frozen['journey_run'])/'negative-controls.json').read_text())
 assert {'missing','changed','stale','stale-even-with-rehashed-artifact','changed-installed-identity-even-with-rehashed-receipt'}.issubset(negatives)
 print(json.dumps({'status':'PASS','freeze':frozen['id'],'controls':controls+negatives,'quality':'unseen/matched comparison and generated quality not run','profile':'API37 measured subset source briefs; separate full inventory remains API35'}))

if __name__=='__main__':
 if '--device' in sys.argv:
    before=set((ROOT/'downloads/frozen-candidate').glob('*')) if (ROOT/'downloads/frozen-candidate').exists() else set()
    sys.argv=[sys.argv[0]]
    try:journeys.main()
    finally:
        for out in set((ROOT/'downloads/frozen-candidate').glob('*'))-before:
            if not out.is_dir():continue
            for name,args in [('final-observed-boot',['cat','/proc/sys/kernel/random/boot_id']),('final-observed-font',['settings','get','system','font_scale']),('final-observed-memory',['dumpsys','meminfo','org.pocketlore.app'])]:
                r=subprocess.run(journeys.ADB+['shell',*args],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30);(out/(name+'.txt')).write_bytes(r.stdout);(out/(name+'.exit')).write_text(str(r.returncode))
            files={str(p.relative_to(out)):journeys.sha(p) for p in out.rglob('*') if p.is_file()}
            (out/'invocation-seal.json').write_text(json.dumps({'files':files,'has_passing_manifest':(out/'manifest.json').exists()},indent=2)+'\n')
 else:audit()
