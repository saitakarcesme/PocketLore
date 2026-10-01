"""Finite post-build stages; one private lock, atomic receipts, no automatic retries."""
import fcntl,hashlib,json,os,pathlib,subprocess,sys,time
from common import atomic_json
ROOT=pathlib.Path('/home/isa/PocketLore-control/scale-workers/places');D=ROOT/'data';E=pathlib.Path('docs/evidence/scale/places')
while not all((D/f'compact-{i:02}.report.json').exists() for i in range(16)):time.sleep(10)
lock=(ROOT/'places-build.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX)
journal=ROOT/'postprocess-stages.json';stages=json.loads(journal.read_text()) if journal.exists() else {}
def run(name,args):
 fingerprint=hashlib.sha256(json.dumps(args).encode()+b''.join(pathlib.Path(x).read_bytes() for x in args if x.endswith('.py'))).hexdigest()
 if stages.get(name,{}).get('status')=='passed' and stages[name]['fingerprint']==fingerprint:return
 stamp=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime());logpath=ROOT/(name+'-'+stamp+'.log');stages[name]={'status':'running','fingerprint':fingerprint,'args':args,'log':str(logpath),'utc':stamp};atomic_json(journal,stages)
 with logpath.open('x') as log:r=subprocess.run([sys.executable]+args,stdout=log,stderr=subprocess.STDOUT)
 stages[name].update(status='passed' if r.returncode==0 else 'failed',returncode=r.returncode);atomic_json(journal,stages)
 if r.returncode:raise RuntimeError(name+' failed; preserved; investigate before retry')
 print(name,'passed',flush=True)
run('global-audit',['tools/scale/places/compact_audit.py'])
run('original-source-audit',['tools/scale/places/source_audit.py',str(E/'original-source-audit.json')]+[str(p) for p in sorted(D.glob('part-*.parquet'))])
run('global-query-checks',['tools/scale/places/oracle_checks.py'])
run('auxiliary-source-checks',['tools/scale/places/aux_checks.py'])
planet=D/'planet-260921.osm.pbf'
if not planet.with_suffix('.receipt.json').exists():raise RuntimeError('Planet receipt not complete')
if not (D/'osm-planet.sqlite').exists():run('planet-build',['tools/scale/places/planet.py',str(planet),str(D/'osm-planet.sqlite')])
if not (D/'osm-geometry.sqlite').exists():run('planet-geometry',['tools/scale/places/planet_geometry.py',str(planet),str(D/'osm-planet.sqlite'),str(D/'osm-geometry.sqlite'),str(D/'osm-geometry-work.sqlite')])
run('global-diet-checks',['tools/scale/places/diet_checks.py'])
for p in D.glob('*.report.json'):atomic_json(E/p.name,json.loads(p.read_text()))
state={'task':'global-places','status':'built_and_host_checked_pending_seal_and_independent_review','overture_shards':16,'planet_tags_processed':True,'distribution_ready':False,'android_acceptance':False,'physical_acceptance':False,'unresolved':['provisional budgets','relation geometry','source-family identity matching','Android integration','independent criticism']}
atomic_json('LOOP_STATE.json',state);atomic_json(ROOT/'milestone.json',state);atomic_json(E/'milestone.json',state);print(json.dumps(state),flush=True)
