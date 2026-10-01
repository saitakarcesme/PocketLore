#!/usr/bin/env python3
"""Verify actual simultaneous Android measurements, exact receipts and negative mutations."""
import hashlib,json,pathlib,tempfile,shutil,sys
ROOT=pathlib.Path(__file__).resolve().parents[3]
BASE=ROOT/'docs/evidence/full-capacity';RUN=BASE/'run'
MODEL=ROOT/'downloads/answers/model/qwen2.5-0.5b-instruct-q4_k_m.gguf'
MODEL_SHA='74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def load(p):return json.loads(p.read_text())
def require(value,why):
 if not value:raise ValueError(why)
def integrity(path,expected):require(path.is_file() and sha(path)==expected,'Missing/changed artifact: '+str(path))
def results(run):return {p.parent.name:load(p) for p in run.glob('*/result.json')}
def behavior(run):
 rs=results(run);env=load(run/'environment.json');require(env['serial']=='emulator-5562' and env['api'].strip()=='35' and env['abi'].strip()=='x86_64','Wrong emulator')
 runtime=load(run/'runtime.json');apk=runtime['apk']['bytes'];test=runtime['test_apk']['bytes']
 package=load(BASE/'package-storage-after.json');code_bytes=max(package['allocated_code_bytes'],load(BASE/'package-storage-before.json')['allocated_code_bytes'])
 require(package['app_allocated_bytes']+code_bytes<50_000_000_000,'Final installed allocation over hard cap')
 current=load(run/'runtime-redirect-repair.json')
 require(package['rows'][0]['apk_sha256']==current['apk']['sha256'],'Installed APK identity drift')
 require(package['rows'][1]['apk_sha256']==current['test_apk']['sha256'],'Installed instrumentation identity drift')
 for label,r in rs.items():require(r['status']=='PASS' and r['model_sha256']==MODEL_SHA,label+' failed or model changed')
 for kind,n in [('wiki',15),('places',16)]:
  for i in range(n):
   r=rs[f'{kind}-{i:02}'];require(len(r['shards'])==i+1,'Rolling sweep cannot satisfy cumulative installation');
   if r.get('reconciled_import'):
    require(r['manifest']==sha(run/(f'{kind}-{i:02}'+'-input')/'manifest.json'),'Reconciled catalog differs from attempted import')
    require('Sampler failure:' in (BASE/'failures'/f'{kind}-{i:02}-original/instrumentation.log').read_text(),'Unexplained import reconciliation')
   else:require(r['files_after']>=r['files_before'],'Installation retired prior assets')
 for label in ['full-inspection','replacement-inspection','restored-inspection']:
  r=rs[label];require((r['wiki_documents'],r['wiki_full'],r['wiki_leads'],r['places_source_records'])==(6498498,1250000,5248498,81455423),'Full simultaneous counts mismatch')
  require(r['reviewed_collections']==3 and r['reviewed_documents']==1113,'Reviewed editions missing')
  require(len(r['wiki_queries'])==11 and len(r['cities'])==20,'Frozen queries missing')
  require(all(q.get('source') and q['ms']>0 for q in r['wiki_queries']),'Source inspection missing')
  for q,want in zip(r['wiki_queries'],load(ROOT/'tools/evaluation/full-capacity/protocol.json')['wiki_queries']):require(q['query']==want and q['title']==want,'Exact-title regression')
  require(all(q['count']>0 and q.get('source') for q in r['cities']),'Full inventory city/category misses remain')
  require(r['absent_category_withheld'] and r['query_cancelled'],'Absence/cancellation failed')
  require(r['app_logical_bytes']>41_000_000_000,'Not whole simultaneous declared candidate')
 for label in ['cancelled-replacement','corrupt-replacement']:
  r=rs[label];require(r['rollback'] and r['files_before']==r['files_after'] and r['rejection'],'Rollback not demonstrated')
 require(rs['cancelled-replacement']['read_bytes']>1048576,'Cancellation did not interrupt payload')
 require(rs['disable']['pid']!=rs['restart-disabled']['pid'],'Not a process restart')
 require(rs['disable']['catalog']==rs['restart-disabled']['catalog'],'Selection lost at restart')
 # Actual incoming new-object bytes and both old/new residency, not an identical delta.
 peaks=[]
 for label in ['replacement','restore']:
  r=rs[label];require(r['new_bytes_written']>1_500_000_000,'Replacement was not the declared largest shard')
  require(r['precommit_files_bytes']>r['files_before']+1_500_000_000,'Old and new did not coexist')
  require(abs(r['files_after']-r['files_before'])<100000,'Whole edition copied or assets lost')
  peak=max(r['precommit_files_bytes'],r['sampled_app_logical_peak'],r['sampled_app_allocated_peak'])+code_bytes
  require(peak<50_000_000_000,'Observed hard storage cap exceeded');peaks.append(peak)
  provider=load(run/(label+'-input')/'transfer.json')['bytes']
  require(peak+provider+134217728<50_000_000_000,'Conservative provider-copy budget exceeds hard cap')
 # Rehash results represent the complete inventory, including auxiliary residency.
 sealed=load(run/'host-inventory.json');required={f['sha256']:f['bytes'] for f in sealed}
 for manifest in ['wiki-14-input','places-15-input']:
  for f in load(run/manifest/'manifest.json')['files']:required[f['sha256']]=f['bytes']
 for label in ['full-hashes','restored-hashes']:
  got={f['sha256']:f['bytes'] for f in rs[label]['objects']}
  require(all(got.get(h)==n for h,n in required.items()),'Missing/corrupt simultaneous sealed asset')
 require(load(run/'complete.json')['whole_inventory_resident'],'Run incomplete')
 repaired=rs['redirect-repair'];cases=load(ROOT/'tools/evaluation/full-capacity/redirect-regression.json')['cases']
 require(repaired['simultaneous_shards']==31 and len(repaired['queries'])==len(cases),'Final reader not measured against complete catalog')
 for got,want in zip(repaired['queries'],cases):
  require(all(got[k]==want[k] for k in ['query','title','id','shard']) and got['source'],'Final redirect source identity mismatch')
 require(all(x['unchanged'] for x in current['import_code_equivalence']),'Final candidate changed measured import code')
 retained=load(BASE/'seed-assets.json');after=load(BASE/'seed-assets-after.json')
 require(len(retained['actual'])==5 and retained['actual']==retained['expected']==after['actual']==after['expected'],'Saved model/reviewed assets changed')
 require(retained['actual']['model.gguf']==MODEL_SHA,'Wrong production model')
 ui=load(BASE/'ui/result.json');require(ui['actual_source_dialog'] and ui['real_controls'] and ui['active_collections']==2 and not ui['generation'],'Actual source/collection UI not validated')
 rendered=(BASE/'ui/source.txt').read_text();require('Citation identity:' in rendered and 'Text SHA-256:' in rendered and 'not cleared for generated answers' in rendered,'Visible source provenance/disclosure missing')
 disk_samples=[json.loads(line) for p in [*run.glob('*/disk-samples.jsonl'),*(BASE/'failures').rglob('disk-samples.jsonl')] for line in p.read_text().splitlines()]
 data_peak=max(int(x['df_k'].splitlines()[-1].split()[2])*1024 for x in disk_samples)
 require(data_peak<50_000_000_000,'Whole-emulator userdata high-water exceeds hard cap')
 return {'status':'PASS','whole_emulator_userdata_peak_bytes':data_peak,'primary_shards':31,'sealed_asset_bytes':sum(f['bytes'] for f in sealed),'installed_bulk_objects_including_notices':len(required),'installed_bulk_bytes_including_notices':sum(required.values()),'max_measured_update_bytes_including_allocated_code_and_test':max(peaks),'target_met':max(peaks)<=45_000_000_000,'cities_positive':[sum(q['count']>0 for q in rs[label]['cities']) for label in ['full-inspection','replacement-inspection','restored-inspection']],'limits':'Emulator capacity/reader validation only; no phone, rights clearance or model quality acceptance.'}
def verify():
 receipt=load(BASE/'receipt.json')
 for f in receipt['files']:integrity(ROOT/f['path'],f['sha256'])
 for f in receipt['external']:integrity(pathlib.Path(f['path']),f['sha256'])
 integrity(MODEL,MODEL_SHA)
 summary=behavior(RUN)
 # Actual temporary mutated/missing artifacts; no mutation of canonical evidence or weights.
 rejected=[]
 with tempfile.TemporaryDirectory(prefix='pocketlore-capacity-') as td:
  d=pathlib.Path(td)
  def fails(name,fn):
   try:fn()
   except (ValueError,FileNotFoundError,KeyError):rejected.append(name)
   else:raise ValueError('Negative regression accepted '+name)
  fixture=d/'artifact';fixture.write_bytes(b'changed model artifact')
  fails('changed model bytes',lambda:integrity(fixture,MODEL_SHA));fixture.unlink();fails('missing model bytes',lambda:integrity(fixture,MODEL_SHA))
  shutil.copytree(RUN,d/'run');behavior(d/'run');p=d/'run/full-inspection/result.json';original=p.read_bytes();p.write_bytes(original+b' ')
  fails('changed raw run bytes',lambda:integrity(p,sha(RUN/'full-inspection/result.json')));p.unlink();fails('missing run artifact',lambda:integrity(p,sha(RUN/'full-inspection/result.json')));p.write_bytes(original)
  r=load(p);r['wiki_documents']=413151;p.write_text(json.dumps(r));fails('subset counts',lambda:behavior(d/'run'));p.write_bytes(original)
  p=d/'run/replacement/result.json';r=load(p);r['precommit_files_bytes']=r['files_before'];p.write_text(json.dumps(r));fails('unmeasured replacement peak',lambda:behavior(d/'run'))
 require(len(rejected)==6,'Regression suite incomplete');summary['negative_regressions']=rejected
 print(json.dumps(summary,indent=2));return summary
if __name__=='__main__':
 try:verify()
 except Exception as e:print('FAIL:',e,file=sys.stderr);sys.exit(1)
