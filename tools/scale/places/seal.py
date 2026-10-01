"""Seal completed source, asset and host evidence against the private checkpoint commit.
Run only after checks and the final content commit. Does not mutate tracked files.
"""
import fcntl,hashlib,json,pathlib,subprocess,time
from common import atomic_json,file_sha256
ROOT=pathlib.Path('/home/isa/PocketLore-control/scale-workers/places');REPO=ROOT/'repo';D=ROOT/'data';E=REPO/'docs/evidence/scale/places';G=ROOT/'checkpoints.git'
writer=(ROOT/'places-build.lock').open('a');fcntl.flock(writer,fcntl.LOCK_EX|fcntl.LOCK_NB)
def git(*args):return subprocess.check_output(['git','--git-dir='+str(G),'--work-tree='+str(REPO),*args],text=True).strip()
def record(path,expected=None):
 path=pathlib.Path(path);sha=file_sha256(path)
 if expected is not None:assert sha==expected,(str(path),sha,expected)
 return {'path':str(path),'bytes':path.stat().st_size,'sha256':sha}
required_stages={
 'postprocess-stages.json':{'global-audit','original-source-audit','global-query-checks','auxiliary-source-checks','planet-build','planet-geometry','global-diet-checks'},
 'completion-stages.json':{'osm-compact-build','osm-compact-exhaustive-checks','enrichment-source-checks','measured-baseline-comparison','final-fixture-checks','android-final-readers'},
}
for journal,required in required_stages.items():
 stages=json.loads((ROOT/journal).read_text())
 assert required.issubset(stages),(journal,'required stages missing')
 assert all(stage['status']=='passed' and stage.get('returncode')==0 for stage in stages.values()),(journal,'unfinished or failed stages')
osm_check=json.loads((E/'osm-compact-checks.json').read_text())
assert osm_check['all_source_objects_checked']==4870526 and osm_check['lookup_fields_and_raw_source_bytes_equal'] and osm_check['snapshot_equal']
assert len(osm_check['queries'])==20 and all(q['exact_fields_and_order_match'] for q in osm_check['queries'])
selection=json.loads((E/'asset-selection.json').read_text());assert selection['osm_primary']==str(D/'osm-compact.sqlite')
assert not git('status','--porcelain'),'Commit meaningful final evidence before sealing'
assert not (ROOT/'HANDOFF.json').exists(),'Existing handoff is immutable; preserve and version any replacement'
audit=json.loads((E/'global-audit.json').read_text());checks=json.loads((E/'global-checks.json').read_text());assert checks['semantic_invariants_passed'];assert audit['shards']==16 and audit['compact_ids_not_in_raw']==0 and audit['raw_ids_missing_from_compact']==0
assets=[];review_only=[]
for i in range(16):
 path=D/f'compact-{i:02}.sqlite';report=json.loads(path.with_suffix('.report.json').read_text());assets.append({**record(path,report['sha256']),'role':'primary Overture places','report':str(E/f'compact-{i:02}.report.json')});review_only.append({**record(path.with_suffix('.keys.parquet'),report['keys_sha256']),'role':'identity-audit sidecar; not installed'})
for filename,role in [('cities.sqlite','GeoNames aliases'),('wikivoyage.sqlite','official full English Wikivoyage XML'),('osm-compact.sqlite','global explicit OSM diet/hours')]:
 path=D/filename;report=json.loads(path.with_suffix('.report.json').read_text());assets.append({**record(path,report['sha256']),'role':role,'report':str(E/path.with_suffix('.report.json').name)})
geometry_report=json.loads((D/'osm-geometry.report.json').read_text());review_only.append({**record(D/'osm-geometry.sqlite',geometry_report['sha256']),'role':'pre-compaction OSM coordinate and source-object evidence; not installed'})
base_report=json.loads((D/'osm-planet.report.json').read_text());review_only.append({**record(D/'osm-planet.sqlite',base_report['sha256']),'role':'pre-geometry OSM source objects; not installed'});review_only.append({**record(D/'osm-geometry-work.sqlite'),'role':'referenced-node coordinate derivation evidence; not installed'})
optional=record(D/'travel.sqlite',json.loads((D/'travel.report.json').read_text())['sha256']);optional['role']='optional full cached English ZIM-derived HTML; overlapping snapshot, not additive unique coverage'
notices=json.loads((E/'license-text-receipts.json').read_text());notice_files=[record(n['path'],n['sha256']) for n in notices if n['status']==200]
evidence=[record(p) for p in sorted(E.iterdir()) if p.is_file()]
source_receipts=[]
for p in sorted(D.glob('*.receipt.json')):
 source_receipts.append({'receipt':record(p),'content':json.loads(p.read_text())})
# A redirected stdout log is still growing until this process exits; never seal it.
stdout_target=pathlib.Path('/proc/self/fd/1').resolve()
logs=[record(p) for p in sorted(ROOT.glob('*.log')) if p.is_file() and p.resolve()!=stdout_target]
contracts=json.loads((E/'contracts.json').read_text());primary_bytes=sum(a['bytes'] for a in assets)+sum(a['bytes'] for a in notice_files);other_bytes=sum(a['bytes'] for a in assets if a['role']!='primary Overture places')+sum(a['bytes'] for a in notice_files)
handoff={'sealed_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'objective':'Complete pinned global offline Overture places with separate OSM diet/hours, GeoNames aliases and full English Wikivoyage, preserving source inspection and measuring host gates','editable_scope':['tools/scale/places','docs/evidence/scale/places','FINDINGS.md','LOOP_STATE.json','private places lane only'],'repo':str(REPO),'git_dir':str(G),'branch':git('branch','--show-current'),'commit':git('rev-parse','HEAD'),'tree':git('rev-parse','HEAD^{tree}'),'status':'builder_complete_pending_independent_criticism_and_open_acceptance_gates','assets':assets,'optional_asset':optional,'review_only_artifacts':review_only,'cached_zim_source':json.loads((E/'zim-source-metadata.json').read_text()),'license_texts':notice_files,'evidence':evidence,'source_receipts':source_receipts,'source_receipt_scope':'acquisition history includes failed and comparison-only inputs; admitted assets are listed separately','androidlm_comparison':json.loads((E/'androidlm-comparison.json').read_text()),'enrichment_checks':json.loads((E/'enrichment-checks.json').read_text()),'preserved_logs':logs,'seal_stdout_policy':'Active stdout is excluded because it changes after manifest creation; prior completed attempt logs remain included','postprocess_journal':record(ROOT/'postprocess-stages.json'),'completion_journal':record(ROOT/'completion-stages.json'),'contracts':contracts,'asset_selection':selection,'osm_exhaustive_checks':osm_check,'counts':audit,'query_checks':{'frozen_sha256':checks['frozen_sha256'],'queries':len(checks['queries']),'raw_source_checks':len(checks['raw_record_source_checks']),'passed':checks['semantic_invariants_passed'],'positive_cities':checks['cities_with_any_positive']},'storage':{'primary_lane_assets_bytes':primary_bytes,'places_bytes':audit['bytes'],'places_provisional_budget_bytes':4000000000,'places_budget_passed':audit['within_budget'],'travel_aliases_osm_notices_bytes':other_bytes,'lane_supplemental_budget_passed':other_bytes<=3000000000,'with_optional_zim_bytes':other_bytes+optional['bytes'],'travel_specialty_provisional_aggregate_budget_bytes':3000000000,'other_specialty_lanes_bytes':None,'whole_product_installed_bytes':None,'raw_and_failed_staging_not_installed':True},'limits':{'compute_workers':2,'http_concurrency':2,'gpu_jobs':0,'per_record_network_or_llm_calls':0,'shared_emulator_installs':0,'research_time_network':False,'batch_max_bytes':2147483648,'hardware_ram_acceptance':False,'max_total_product_assets_acceptance':False},'open_gates':['places provisional storage budget','physical Android/GrapheneOS resources and usefulness','Android application integration, multi-shard reader runtime and measured host search latency','independent critic review','rights and attribution distribution review, including missing optional ZIM page links and archive license metadata','source-family identity matching and relation geometry','real-world semantic uniqueness and comparable AndroidLM application/answer-quality acceptance','shared specialty and whole-product asset budgets'],'distribution_ready':False,'android_acceptance':False,'rival_acceptance':False}
atomic_json(ROOT/'HANDOFF.json',handoff);atomic_json(ROOT/'HANDOFF.sha256.json',record(ROOT/'HANDOFF.json'));print(json.dumps({'handoff':str(ROOT/'HANDOFF.json'),'commit':handoff['commit'],'primary_lane_assets_bytes':primary_bytes},indent=2))
