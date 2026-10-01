#!/usr/bin/env python3
"""Check real sealed bytes and Android delta behavior; full installation stays a gate."""
import hashlib,json,pathlib,subprocess,sys,tempfile,shutil,datetime
from full_scale_capacity import capacity
ROOT=pathlib.Path(__file__).resolve().parents[2];E=ROOT/'docs/evidence/full-scale'
ADB=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5560']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def checked(p,s):
 if not p.is_file() or p.stat().st_size!=s['bytes'] or sha(p)!=s['sha256']:raise ValueError('Missing/changed artifact: '+str(p))
def require(b,s):
 if not b:raise ValueError(s)
def main():
 seal=json.loads((E/'candidate.json').read_text())
 # Stop unchanged environment failures before copying weights, installing APKs or rerunning subsets.
 for relative in ['tools/evaluation/verify_full_scale_inventory.py','tools/evaluation/full_scale_capacity.py','docs/evidence/full-scale/budget.json']:
  checked(ROOT/relative,seal['artifacts'][relative])
 budget=json.loads((E/'budget.json').read_text())
 df=subprocess.check_output(ADB+['shell','df','-k','/data'],text=True,timeout=30)
 measured=capacity(df,budget['installed_upper_estimate'])
 out=ROOT/'downloads/full-scale'/('capacity-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir(parents=True)
 (out/'capacity.json').write_text(json.dumps(dict(measured,raw_df=df,subsets_rerun=False),indent=2)+'\n')
 if not measured['prerequisite_met']:
  print('BLOCKED: persistent Android /data total capacity '+str(measured['total_bytes'])+' bytes is below the '+str(measured['installed_lower_bound_bytes'])+' byte candidate requirement; even an empty filesystem cannot fit it.',file=sys.stderr)
  print('No APK installation or subset rerun. Full inventory/update gate remains unmet. Measurement: '+str(out),file=sys.stderr)
  return 1

 for p,s in seal['artifacts'].items():checked(ROOT/p,s)
 files=json.loads((E/'host/files.json').read_text())
 for f in files:checked(pathlib.Path(f['path']),f)
 counts=json.loads((E/'host/counts.json').read_text())
 require(len(counts['wiki'])==15 and sum(x['documents'] for x in counts['wiki'])==6498498,'Wiki inventory count')
 require(len(counts['places'])==16 and sum(x['source_records'] for x in counts['places'])==81455423,'Place source count')
 queries=json.loads((E/'host/wiki-queries.json').read_text());protocol=json.loads((ROOT/'tools/evaluation/full-scale/protocol.json').read_text())
 require([x['query'] for x in queries]==protocol['wiki_queries']+protocol['redirects'],'Query population changed')
 for x in queries[:8]:require(x['hits'][0]['title']==x['query'] and x['hits'][0]['route']=='exact','Exact title lost')
 for x in queries[8:]:require(x['hits'][0]['route']=='redirect','Redirect lost')
 cities=json.loads((E/'host/cities.json').read_text());require([x['query'] for x in cities]==protocol['cities'],'City population changed')
 require(all(x['hits'] and x['first_source'] for x in cities),'Full host city/source coverage missing')
 require(not json.loads((E/'host/summary.json').read_text())['absent_category'],'Absent category leak')
 with tempfile.TemporaryDirectory(prefix='pocketlore-shard-integrity-') as d:
  for p in ['downloads/full-scale/fixtures/update.plscale','docs/evidence/full-scale/host/wiki-queries.json']:
   s=seal['artifacts'][p];copy=pathlib.Path(d)/pathlib.Path(p).name;shutil.copyfile(ROOT/p,copy);checked(copy,s)
   with copy.open('r+b') as f:v=f.read(1);f.seek(0);f.write(bytes([v[0]^1]))
   for changed in [True,False]:
    if not changed:copy.unlink()
    try:checked(copy,s)
    except ValueError:pass
    else:raise ValueError('Changed/missing real artifact accepted')
 large=json.loads((E/'large-android/large-update.json').read_text());base=json.loads((E/'large-android/large-base.json').read_text());manifest=json.loads((E/'places-stage-2.json').read_text())
 require(large['shared_cities'] and large['source_records']==10186606 and large['pid']!=base['pid'],'Full-shard update/restart receipt')
 require(large['new_bytes_written']<1100000000 and large['observed_precommit_bytes']<50000000000,'Full-shard delta duplicated edition or exceeded budget')
 for f in manifest['files']:
  remote='files/scale-library/objects/'+f['sha256']
  actual=subprocess.check_output(ADB+['shell','run-as','org.pocketlore.app','sha256sum',remote],text=True).split()[0]
  require(actual==f['sha256'],'Installed full-shard/shared file changed')
 for p in ['android/app/build/outputs/apk/debug/app-debug.apk','android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk']:subprocess.run(ADB+['install','-r',str(ROOT/p)],check=True)
 subprocess.run(ADB+['shell','run-as','org.pocketlore.app','mkdir','-p','files/shard-fixtures'],check=True)
 for p in list((ROOT/'downloads/full-scale/fixtures').glob('*.plscale'))+[ROOT/'downloads/full-scale/places-fixture/places.plscale']:
  with p.open('rb') as f:subprocess.run(ADB+['shell',"run-as org.pocketlore.app sh -c 'cat > files/shard-fixtures/"+p.name+"'"],stdin=f,check=True)
 out=ROOT/'downloads/full-scale'/('check-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
 subprocess.run(ADB+['shell','am','force-stop','org.pocketlore.app'],check=True)
 run=subprocess.run(ADB+['shell','am','instrument','-w','org.pocketlore.app.test/org.pocketlore.app.ShardUpdateInstrumentation'],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=True)
 (out/'instrumentation.log').write_text(run.stdout);require('INSTRUMENTATION_CODE: -1' in run.stdout,'Android transaction failed; '+str(out))
 raw=subprocess.check_output(ADB+['shell','run-as','org.pocketlore.app','cat','files/shard-update-result.json']);(out/'android.json').write_bytes(raw);r=json.loads(raw)
 require(r['status']=='PASS' and r['shared_object'] and r['corrupt_cancel_rollback'] and r['restart_selection'] and r['changed_missing_shared_object_rejected'] and r['interrupted_stage_recovery'] and r['removed_shard_reclaimed'],'Update recovery gate')
 require(len(r['cities'])==2 and all(x['count']>0 for x in r['cities']),'Android multi-shard place coverage')
 require(r['wiki_observed_precommit_bytes']>=r['wiki_after_bytes'] and r['new_temporary_peak']<r['wiki_after_bytes'],'Delta peak did not retain/reuse content')
 require(r['model_sha256']=='74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db','Production model changed')
 subprocess.run(ADB+['shell','am','force-stop','org.pocketlore.app'],check=True)
 restart=subprocess.run(ADB+['shell','am','instrument','-w','-e','mode','restart','org.pocketlore.app.test/org.pocketlore.app.ShardUpdateInstrumentation'],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=True)
 (out/'restart.log').write_text(restart.stdout);require('INSTRUMENTATION_CODE: -1' in restart.stdout,'Separate process reload failed')
 raw=subprocess.check_output(ADB+['shell','run-as','org.pocketlore.app','cat','files/shard-restart-result.json']);(out/'restart.json').write_bytes(raw);restart_result=json.loads(raw)
 require(restart_result['pid']!=r['pid'] and restart_result['collections']==2 and restart_result['model_sha256']==r['model_sha256'],'Restart changed model/catalog')
 print('PASS: all sealed host hashes/counts, frozen exact/redirect/city results, changed/missing artifacts and fresh Android shared-object delta/rollback/subset checks.',flush=True)
 print('Raw emulator result:',out,flush=True)
 print('BLOCKED: full 41+GB installed inventory and full-scale update peak have not been measured on an approved Android environment; existing emulator userdata is about 6GB. Host/subset results cannot satisfy that gate.',file=sys.stderr)
 return 1
if __name__=='__main__':
 try:sys.exit(main())
 except Exception as e:print('FAIL:',e,file=sys.stderr);sys.exit(1)
