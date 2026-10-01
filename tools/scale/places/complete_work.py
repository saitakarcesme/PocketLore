"""Finite lossless OSM optimization and final host checks after the planet pipeline."""
import fcntl,hashlib,json,pathlib,subprocess,sys,time
from common import atomic_json
ROOT=pathlib.Path('/home/isa/PocketLore-control/scale-workers/places');D=ROOT/'data';E=pathlib.Path('docs/evidence/scale/places');journal=ROOT/'completion-stages.json'
while True:
 stages=json.loads((ROOT/'postprocess-stages.json').read_text())
 if any(x['status']=='failed' for x in stages.values()):raise RuntimeError('Prior pipeline failure requires investigation')
 if stages.get('global-diet-checks',{}).get('status')=='passed':break
 time.sleep(10)
lock=(ROOT/'places-build.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX);stages=json.loads(journal.read_text()) if journal.exists() else {}
def run(name,args):
 source_files=sorted(pathlib.Path('tools/scale/places').rglob('*.py')) if '-m' in args else [pathlib.Path(x) for x in args if x.endswith('.py') and pathlib.Path(x).is_file()]
 fingerprint=hashlib.sha256(json.dumps(args).encode()+b''.join(p.read_bytes() for p in source_files)).hexdigest()
 if stages.get(name,{}).get('status')=='passed' and stages[name]['fingerprint']==fingerprint:return
 stamp=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime());logpath=ROOT/(name+'-'+stamp+'.log');previous=stages.get(name);stages[name]={'status':'running','fingerprint':fingerprint,'args':args,'log':str(logpath),'utc':stamp}
 if previous:stages[name]['previous_attempt']=previous
 atomic_json(journal,stages)
 with logpath.open('x') as log:r=subprocess.run([sys.executable]+args,stdout=log,stderr=subprocess.STDOUT)
 stages[name].update(status='passed' if r.returncode==0 else 'failed',returncode=r.returncode);atomic_json(journal,stages)
 if r.returncode:raise RuntimeError(name+' failed; raw output preserved; investigate before retry')
 print(name,'passed',flush=True)
if not (D/'osm-compact.sqlite').exists():run('osm-compact-build',['tools/scale/places/osm_compact.py',str(D/'osm-geometry.sqlite'),str(D/'osm-compact.sqlite')])
run('osm-compact-exhaustive-checks',['tools/scale/places/osm_compact_checks.py'])
r=json.loads((D/'osm-compact.report.json').read_text());old=json.loads((D/'osm-geometry.report.json').read_text());assert r['bytes']<old['bytes'],'Candidate did not improve storage; retain original and inspect'
atomic_json(E/'osm-compact.report.json',r);atomic_json(E/'asset-selection.json',{'overture':'16 compact schema-2 shards; all source IDs retained','osm_primary':str(D/'osm-compact.sqlite'),'osm_original_geometry_bytes':old['bytes'],'osm_compact_bytes':r['bytes'],'osm_saved_bytes':old['bytes']-r['bytes'],'reason':'full source-object and coordinate equality checked; no geographic, field or row pruning','travel_primary':str(D/'wikivoyage.sqlite'),'travel_optional':str(D/'travel.sqlite'),'optional_note':'different overlapping archive retained in staging; do not add listing counts as unique places','android_acceptance':False})
run('enrichment-source-checks',['tools/scale/places/enrichment_checks.py',str(D/'osm-compact.sqlite')])
run('measured-baseline-comparison',['tools/scale/places/compare_baseline.py'])
run('final-fixture-checks',['-m','unittest','discover','-s','tools/scale/places','-p','test_*.py','-v'])
run('android-final-readers',['tools/scale/places/compile_readers.py'])
state={'task':'global-places','status':'all_host_stages_complete_pending_final_seal_and_independent_criticism','overture_ids':81455423,'osm_objects':r['records'],'osm_asset_bytes':r['bytes'],'field_or_geographic_pruning':False,'distribution_ready':False,'physical_acceptance':False,'android_acceptance':False}
for p in ['LOOP_STATE.json',ROOT/'milestone.json',E/'milestone.json']:atomic_json(p,state)
print(json.dumps(state),flush=True)
