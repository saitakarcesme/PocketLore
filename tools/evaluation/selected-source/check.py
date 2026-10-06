"""Offline, evidence-bound qualification of selected producer engineering only."""
import copy
import base64,hashlib,json,pathlib,resource,sqlite3,subprocess,sys,time,zlib
import oracle
ROOT=pathlib.Path(__file__).resolve().parents[3]
BASE=ROOT/'downloads/selected-source-production'
ART=ROOT/'docs/evidence/selected-source-production-review.json'
def digest(b):return hashlib.sha256(b).hexdigest()
def embed(path):
 b=path.read_bytes();return {'path':str(path),'bytes':len(b),'sha256':digest(b),'encoding':'zlib+base64','content':base64.b64encode(zlib.compress(b)).decode()}
def sampled_originals(out,audit):
 d=sqlite3.connect('file:'+str(out/'index.sqlite')+'?mode=ro',uri=True);d.execute('pragma cache_size=-2048');d.execute('pragma mmap_size=0');items=[]
 try:
  for sample in audit['deterministic_source_samples']:
   if sample['outcome']!='inspection-only':continue
   page,rev=sample['page'],sample['revision'];record={'identity':sample,'pieces':{}}
   for kind in ('original','html','structure'):
    chunks=[]
    for part,start,end,key,blob in d.execute('SELECT p.part,p.start,p.end,p.sha,c.z FROM pieces p JOIN capsules c ON c.sha=p.sha WHERE p.page=? AND p.revision=? AND p.kind=? ORDER BY p.part',(page,rev,kind)):
     chunks.append({'part':part,'start':start,'end':end,'sha256':key,'zlib_base64':base64.b64encode(blob).decode()})
    record['pieces'][kind]=chunks
   rows=d.execute('SELECT node,start,end,title,text,fragment_sha,scope,disposition FROM contexts WHERE page=? AND revision=? ORDER BY node',(page,rev)).fetchall();raw=json.dumps(rows,ensure_ascii=False).encode();record['contexts']={'bytes':len(raw),'sha256':digest(raw),'encoding':'zlib+base64','content':base64.b64encode(zlib.compress(raw)).decode()};items.append(record)
 finally:d.close()
 return items

def validate_state(state,count,codehash):
 assert state['status']=='PROVISIONAL_PREFIX_COMPLETE'
 assert state['configuration']['code'][str(ROOT/'tools/packs/selected-source/producer.py')]==codehash,'Stale executed source'
 assert state['configuration']['count']==count and state['counts']['selected']==count
 assert state['configuration']['through']==99999 and state['configuration']['mode']=='engineering'
 assert state['configuration']['ranking']=='/home/isa/PocketLore-control/scale-workers/wiki/priority-2000000.sqlite'
 assert state['configuration']['ranking_sha256']=='2f1e6f9171154d2b315188ed421ee6370146a31d5c1aac768d5267c2f953261e'
 assert set(state['configuration']['code'])=={str(ROOT/name) for name in ('tools/packs/selected-source/producer.py','tools/packs/source-structure/produce.py','tools/packs/complete-source/production.py','tools/packs/complete-source/compact.py')}
 assert state['configuration']['stage']=='/home/isa/PocketLore-control/overnight-20261005/source-original-staging/run-originals/original-records.sqlite'
 assert not state['source_admission_established'] and not state['distribution_ready'] and not state['whole_source_identity_verified']
 assert state['independently_eligible_full_articles']==0 and state['independently_eligible_contexts']==0
 assert state['memory']['ru_maxrss_bytes']<536870912 and state['limits']['address_space_limit_bytes']<=536870912
 assert state['storage']['free_host_bytes']>=107374182400

def negative_states(state,count,codehash):
 mutations=[('substituted ranking',['configuration','ranking'],'other.sqlite'),('changed rank pin',['configuration','ranking_sha256'],'0'*64),('stale code',['configuration','code',str(ROOT/'tools/packs/selected-source/producer.py')],'0'*64),('partial phase',['status'],'RUNNING'),('false admission',['source_admission_established'],True),('false complete archive',['whole_source_identity_verified'],True),('missing source identity',['configuration','stage'],'missing.sqlite'),('wrong count',['counts','selected'],count-1),('memory over cap',['memory','ru_maxrss_bytes'],536870913)]
 results=[]
 for name,path,value in mutations:
  altered=copy.deepcopy(state);at=altered
  for field in path[:-1]:at=at[field]
  at[path[-1]]=value
  try:validate_state(altered,count,codehash)
  except (AssertionError,KeyError):results.append({'name':name,'mutation_path':path,'value':value,'expected':'rejection','baseline_run_id':state['run_id']})
  else:raise AssertionError('Corrupted receipt accepted: '+name)
 altered=copy.deepcopy(state);del altered['whole_source_identity_verified']
 try:validate_state(altered,count,codehash)
 except KeyError:results.append({'name':'missing completion field','expected':'rejection','baseline_run_id':state['run_id']})
 else:raise AssertionError('Missing receipt accepted')
 return results

def validate_reader(reader,index_sha):
 assert reader['status']=='PASS' and reader['source_index_sha256']==index_sha and reader['reader_sha256']==digest((ROOT/'tools/packs/selected-source/read.py').read_bytes())
 fixture=ROOT/'docs/evidence/selected-source-production/reader-fixtures.json';expected=json.loads(fixture.read_text());assert reader['fixture_sha256']==digest(fixture.read_bytes())
 assert reader['executed_harness_sha256']==digest((pathlib.Path(__file__).parent/'measure_reader.py').read_bytes())
 assert [q['query'] for q in reader['queries']]==expected['queries'] and reader['negative_controls']==['limit','window','cancel before search','cancel during window']
 assert all(len(q['first_open_and_repeat_not_cold_OS'])==2 and all(0<=m['rows']<=20 and len(m['ids'])==m['rows'] for m in q['first_open_and_repeat_not_cold_OS']) for q in reader['queries'])

def main():
 packet={'schema':1,'audit_epoch':time.time(),'status':'FAIL','scope':'host engineering preparation, no full-source or Android admission','files':{},'errors':[],'source_admission_established':False,'android_execution':False}
 try:
  source=ROOT/'tools/packs/selected-source/producer.py';codehash=digest(source.read_bytes())
  ranking=pathlib.Path('/home/isa/PocketLore-control/scale-workers/wiki/priority-2000000.sqlite');h=hashlib.sha256()
  with ranking.open('rb') as f:
   for block in iter(lambda:f.read(1048576),b''):h.update(block)
  assert ranking.stat().st_size==2644783104 and h.hexdigest()=='2f1e6f9171154d2b315188ed421ee6370146a31d5c1aac768d5267c2f953261e','Frozen ranking identity changed'
  for path in [source,ROOT/'tools/packs/source-structure/produce.py',ROOT/'tools/packs/selected-source/read.py',ROOT/'tools/packs/complete-source/production.py',ROOT/'tools/packs/complete-source/compact.py',*pathlib.Path(__file__).parent.glob('*.py'),ROOT/'tools/evaluation/check_selected_source_production.sh',* (ROOT/'docs/evidence/selected-source-production').glob('*')]:
   if path.is_file():packet['files'][str(path.relative_to(ROOT))]=embed(path)
  # All failed receipts stay inspectable, not replaced by the latest run.
  for path in BASE.rglob('*'):
   if path.name.startswith('check-final') and path.suffix=='.log':continue # Active auditor stdout is collected by its caller after this packet closes.
   if path.is_file() and (path.suffix in ('.json','.jsonl','.log','.py','.stdout','.stderr')) and path.stat().st_size<4000000:packet['files'][str(path.relative_to(ROOT))]=embed(path)
  for dirname in ['source-reader-prerequisite-review-20261006T0323Z','source-reader-genuine-extended-review-20261006T0403Z']:
   directory=pathlib.Path('/home/isa/PocketLore-control/overnight-20261005')/dirname
   for path in directory.iterdir():
    if path.is_file() and path.stat().st_size<4000000:packet['files'][dirname+'/'+path.name]=embed(path)
  outcomes=[]
  for count in (6000,12000):
   out=BASE/f'final-{count}';state=json.loads((out/'status.json').read_text());validate_state(state,count,codehash);negatives=negative_states(state,count,codehash)
   assert state['configuration']['code'][str(source)]==codehash,'Stale executed source'
   for filename,expected in state['configuration']['code'].items():assert digest(pathlib.Path(filename).read_bytes())==expected,'Changed executed dependency'
   assert json.loads((BASE/f'final-{count}-transport.json').read_text())['exit_code']==0,'Actual producer transport failed'
   assert state['configuration']['count']==count and state['counts']['selected']==count
   assert not state['source_admission_established'] and not state['distribution_ready'] and state['independently_eligible_full_articles']==0
   assert state['memory']['ru_maxrss_bytes']<536870912 and state['limits']['address_space_limit_bytes']<=536870912
   assert state['storage']['free_host_bytes']>=107374182400
   # Streamed digest verifies actual final SQLite bytes, not a status assertion alone.
   h=hashlib.sha256()
   with (out/'index.sqlite').open('rb') as f:
    for block in iter(lambda:f.read(1048576),b''):h.update(block)
   assert h.hexdigest()==state['index_sha256'],'Corrupt index'
   audit=oracle.audit(out,state['configuration']['stage'],state['configuration']['ranking']);assert audit['status']=='PASS' and audit['selected_distinct_originals']==count
   packet['files'][str((out/'independent-oracle.json').relative_to(ROOT))]=embed(out/'independent-oracle.json')
   reader=json.loads((out/'reader-measurements-v2.json').read_text());validate_reader(reader,state['index_sha256'])
   reader_negatives=[]
   for field,value in [('fixture_sha256','0'*64),('executed_harness_sha256','0'*64),('queries',[]),('negative_controls',[])]:
    altered=copy.deepcopy(reader);altered[field]=value
    try:validate_reader(altered,state['index_sha256'])
    except (AssertionError,KeyError):reader_negatives.append({'field':field,'value':value,'expected':'rejection'})
    else:raise AssertionError('Substituted reader receipt accepted')
   outcomes.append({'count':count,'state':state,'oracle':audit,'reader':reader,'actual_sample_capsules':sampled_originals(out,audit),'receipt_negative_controls':negatives,'reader_receipt_negative_controls':reader_negatives})
  controls=json.loads((BASE/'final-controls/controls.json').read_text());assert controls['status']=='PASS' and controls['producer_sha256']==codehash
  assert controls['executed_oracle_sha256']==digest((pathlib.Path(__file__).parent/'oracle.py').read_bytes())
  assert controls['executed_test_sha256']==digest((pathlib.Path(__file__).parent/'test_controls.py').read_bytes())
  boundaries=json.loads((BASE/'boundaries-v1/boundary-controls.json').read_text());assert boundaries['status']=='PASS' and boundaries['producer_sha256']==codehash and boundaries['executed_test_sha256']==digest((pathlib.Path(__file__).parent/'test_boundaries.py').read_bytes())
  atomic=json.loads((BASE/'atomic-v2/atomic-controls.json').read_text());assert atomic['status']=='PASS' and atomic['test_sha256']==digest((pathlib.Path(__file__).parent/'test_atomic.py').read_bytes());assert atomic['results'][1]['producer_sha256']==codehash and atomic['results'][0]['counts_after_actual_process_exit']=={'articles':1,'receipts':0} and atomic['results'][1]['counts_after_actual_process_exit']=={'articles':0,'receipts':0}
  packet['atomic_controls']=atomic
  snapshot=json.loads((BASE/'snapshot-v1/snapshot-controls.json').read_text());assert snapshot['status']=='PASS' and snapshot['producer_sha256']==codehash and snapshot['test_sha256']==digest((pathlib.Path(__file__).parent/'test_snapshot.py').read_bytes());assert snapshot['actual_writer']['checkpoint']==[0,0,0];packet['snapshot_controls']=snapshot
  packet['full_source_readiness_contract']=embed(pathlib.Path('/home/isa/PocketLore-control/overnight-20261005/source-full-readiness-contract.json'))
  build=json.loads((BASE/'android-build-final.json').read_text());assert build['exit']==0 and build['command']==['bash','tools/android-build.sh']
  for name,identity in build['source_inputs_before'].items():assert digest((ROOT/name).read_bytes())==identity['sha256'],'Stale Android build input'
  for stream in ('stdout','stderr'):assert digest((BASE/('android-build-final.'+stream)).read_bytes())==build[stream+'_sha256']
  assert digest((ROOT/'android/app/build/outputs/apk/debug/app-debug.apk').read_bytes())==build['apk_sha256'];packet['build']=build
  launch_path=ROOT/'docs/evidence/selected-source-production-launch.json';launch=json.loads(launch_path.read_text());assert launch['builder_launch_forbidden'] and launch['limits']['MemoryMax']==536870912 and launch['limits']['MemorySwapMax']==0 and launch['limits']['TasksMax']==32 and launch['limits']['Restart']=='no'
  assert launch['limits']['cleanup_deadline_epoch']<=1791269964 and launch['limits']['work_cutoff_epoch']+10<=launch['limits']['cleanup_deadline_epoch']
  for name,expected in launch['code'].items():assert digest((pathlib.Path(launch['frozen_executable_root'])/name).read_bytes())==expected and digest((ROOT/name).read_bytes())==expected
  packet['launch_artifact']=embed(launch_path);packet['production_launch_qualified']=False
  packet['outcomes']=outcomes;packet['controls']=controls;packet['boundary_controls']=boundaries;packet['status']='PASS'
 except BaseException as error:packet['errors'].append(type(error).__name__+': '+str(error))
 finally:
  packet['ended_epoch']=time.time();packet['audit_pre_serialization_peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
  if packet['audit_pre_serialization_peak_rss_bytes']>=536870912:packet['status']='FAIL';packet['errors'].append('Audit process RSS exceeds 512 MiB')
  rendered=json.dumps(packet,indent=2)+'\n'
  if len(rendered.encode())>32*1024**2:packet['status']='FAIL';packet['errors'].append('Review packet exceeds 32 MiB; retain complete evidence separately before reducing scope');rendered=json.dumps(packet,indent=2)+'\n'
  ART.write_text(rendered)
 print(json.dumps({'status':packet['status'],'errors':packet['errors'],'packet':str(ART)}));return 0 if packet['status']=='PASS' else 1
if __name__=='__main__':sys.exit(main())
