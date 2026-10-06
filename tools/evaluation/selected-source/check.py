"""Offline, evidence-bound qualification of selected producer engineering only."""
import base64,hashlib,json,pathlib,subprocess,sys,time,zlib
import oracle
ROOT=pathlib.Path(__file__).resolve().parents[3]
BASE=ROOT/'downloads/selected-source-production'
ART=ROOT/'docs/evidence/selected-source-production-review.json'
def digest(b):return hashlib.sha256(b).hexdigest()
def embed(path):
 b=path.read_bytes();return {'path':str(path),'bytes':len(b),'sha256':digest(b),'encoding':'zlib+base64','content':base64.b64encode(zlib.compress(b)).decode()}
def main():
 packet={'schema':1,'audit_epoch':time.time(),'status':'FAIL','scope':'host engineering preparation, no full-source or Android admission','files':{},'errors':[],'source_admission_established':False,'android_execution':False}
 try:
  source=ROOT/'tools/packs/selected-source/producer.py';codehash=digest(source.read_bytes())
  ranking=pathlib.Path('/home/isa/PocketLore-control/scale-workers/wiki/priority-2000000.sqlite');h=hashlib.sha256()
  with ranking.open('rb') as f:
   for block in iter(lambda:f.read(1048576),b''):h.update(block)
  assert ranking.stat().st_size==2644783104 and h.hexdigest()=='2f1e6f9171154d2b315188ed421ee6370146a31d5c1aac768d5267c2f953261e','Frozen ranking identity changed'
  for path in [source,ROOT/'tools/packs/source-structure/produce.py',ROOT/'tools/packs/complete-source/production.py',ROOT/'tools/packs/complete-source/compact.py',*pathlib.Path(__file__).parent.glob('*.py'),ROOT/'tools/evaluation/check_selected_source_production.sh',* (ROOT/'docs/evidence/selected-source-production').glob('*')]:
   if path.is_file():packet['files'][str(path.relative_to(ROOT))]=embed(path)
  # All failed receipts stay inspectable, not replaced by the latest run.
  for path in BASE.rglob('*'):
   if path.is_file() and (path.suffix in ('.json','.jsonl','.log','.py')) and path.stat().st_size<4000000:packet['files'][str(path.relative_to(ROOT))]=embed(path)
  for dirname in ['source-reader-prerequisite-review-20261006T0323Z','source-reader-genuine-extended-review-20261006T0403Z']:
   directory=pathlib.Path('/home/isa/PocketLore-control/overnight-20261005')/dirname
   for path in directory.iterdir():
    if path.is_file() and path.stat().st_size<4000000:packet['files'][dirname+'/'+path.name]=embed(path)
  outcomes=[]
  for count in (6000,12000):
   out=BASE/f'final-{count}';state=json.loads((out/'status.json').read_text());assert state['status']=='PROVISIONAL_PREFIX_COMPLETE'
   assert state['configuration']['code'][str(source)]==codehash,'Stale executed source'
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
   outcomes.append({'count':count,'state':state,'oracle':audit})
  controls=json.loads((BASE/'controls-v3/controls.json').read_text());assert controls['status']=='PASS' and controls['producer_sha256']==codehash
  packet['outcomes']=outcomes;packet['controls']=controls;packet['status']='PASS'
 except BaseException as error:packet['errors'].append(type(error).__name__+': '+str(error))
 finally:
  packet['ended_epoch']=time.time();ART.write_text(json.dumps(packet,indent=2)+'\n')
 print(json.dumps({'status':packet['status'],'errors':packet['errors'],'packet':str(ART)}));return 0 if packet['status']=='PASS' else 1
if __name__=='__main__':sys.exit(main())
