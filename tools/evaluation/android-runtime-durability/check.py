"""Owned API37 continuity, exact retained rows and pinned load. No VM/service mutations."""
import base64,os
import pathlib,subprocess,json,hashlib,datetime,sqlite3,sys,copy,time,traceback,importlib.util
from witness import request,continuity,validate
ROOT=pathlib.Path(__file__).resolve().parents[3]
ADB=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5564'];PKG='org.pocketlore.app'
def sha(b):return hashlib.sha256(b).hexdigest()
def memory_assertions(a):
 samples=a['memory_samples'];lo=a['loaded_window_start_ns'];hi=a['loaded_window_end_ns'];pid=a['pid']
 assert hi-lo>=1_000_000_000 and 0<len(samples)<=2400,'missing loaded window'
 loaded=[x for x in samples if x['phase']=='loaded' and lo<=x['start_ns']<=x['end_ns']<=hi]
 assert len(loaded)>=5,'absent loaded-window coverage'
 assert all(x['pid']==pid and x['start_ns']<=x['end_ns'] and 0<x['pss_bytes'] and 0<x['rss_bytes']<=x['hwm_bytes'] for x in samples),'invalid PID/time/units'
 for x in samples:
  fields={line.split(':')[0]:line.split(':',1)[1].strip() for line in x['raw_status'].splitlines() if ':' in line}
  assert int(fields['Pid'])==pid and fields['VmRSS'].endswith(' kB') and fields['VmHWM'].endswith(' kB'),'proc identity/units'
  assert int(fields['VmRSS'].split()[0])*1024==x['rss_bytes'] and int(fields['VmHWM'].split()[0])*1024==x['hwm_bytes'],'raw status mismatch'
 assert a['loaded_sync'] in loaded and a['loaded_end'] in loaded,'missing synchronous loaded samples'
 assert a['sampled_peak_rss_bytes']==max(x['rss_bytes'] for x in samples) and a['sampled_peak_pss_bytes']==max(x['pss_bytes'] for x in samples),'contradictory sampled peaks'
 assert max(x['hwm_bytes'] for x in samples)+1073741824<12_000_000_000,'kernel HWM cap'
 assert a['sampled_peak_rss_bytes']>=a['loaded_sync']['rss_bytes'],'synchronous/sample contradiction'
def freeze_packet(out):
 # Raw databases contain personal bodies and remain protected; exact per-row oracles and hashes are included.
 files={}
 for p in sorted(out.iterdir()):
  if p.is_file() and p.suffix!='.sqlite':
   b=p.read_bytes()
   if b.startswith(b'SQLite format 3\x00'):
    files[p.name]={'sha256':sha(b),'bytes':len(b),'withheld':'Protected raw SQLite; row oracle supplied separately'};continue
   files[p.name]={'sha256':sha(b),'bytes':len(b),'encoding':'base64','content':base64.b64encode(b).decode()}
 code=json.loads((out/'executed-sources.json').read_text()) if (out/'executed-sources.json').exists() else {}
 assert all(sha(v['content'].encode())==v['sha256'] for v in code.values()),'Executed source packet corruption'
 builds=ROOT/'docs/evidence/android-runtime-durability/window-build'
 for p in sorted(builds.glob('*')):
  if p.is_file():
   b=p.read_bytes();files['build/'+p.name]={'sha256':sha(b),'bytes':len(b),'encoding':'base64','content':base64.b64encode(b).decode()}
 recovery=ROOT/'docs/evidence/android-runtime-durability/software-recovery'
 for p in sorted(recovery.glob('*.json')):
  b=p.read_bytes();files['parent-recovery/'+p.name]={'sha256':sha(b),'bytes':len(b),'encoding':'base64','content':base64.b64encode(b).decode()}
 historical=ROOT/'docs/evidence/android-runtime-durability/final-validation/material-20261006T025314Z.json'
 if historical.exists():
  b=historical.read_bytes();files['historical-failed-window-run.json']={'sha256':sha(b),'bytes':len(b),'encoding':'base64','content':base64.b64encode(b).decode()}
 packet={'task':'523-android-runtime-durability-and-preserved-state-strategy-change','run':out.name,'status':'FAIL' if (out/'failure.json').exists() else 'PASS','checker_exit':1 if (out/'failure.json').exists() else 0,'raw_files':files,'executed_sources':code,'database_policy':'Raw SQLite excluded; original row oracle, independently extracted current row hashes and full file inventories included.','limits':'Zero-token emulator load only; sustained renderer, generation, full distribution and physical gates open.'}
 target=ROOT/'docs/evidence/android-runtime-durability-review.json';tmp=target.with_suffix('.tmp');tmp.write_text(json.dumps(packet,indent=2));os.replace(tmp,target)
 archive=ROOT/'docs/evidence/android-runtime-durability/final-validation';archive.mkdir(exist_ok=True);(archive/(out.name+'.json')).write_bytes(target.read_bytes())
def assertions(d):
 assert d['package_present'] and d['apk_actual']==d['apk_expected'],'missing/wrong APK'
 assert d['boot_before']==d['boot_after'] and d['boot_before'],'boot discontinuity'
 assert d['rows_before']==d['rows_after']==d['rows_expected'] and len(d['rows_after'])==201,'changed/missing original rows'
 assert d['schema_before']==d['schema_after']==2,'unsupported notebook schema'
 assert d['catalog_verified'] and d['assets_unchanged'],'source/asset identity'
 assert d['source_hash']==d['executed_source_hash'],'source mismatch'
 assert all(r['status']=='PASS' for r in d['phases']) and len(d['phases'])==2,'partial lifecycle'
 assert d['logical_bytes']<=50_000_000_000 and d['guest_ram_bytes']<=12_000_000_000,'resource cap'
 assert d['owned_host_process_continuity'],'host process identity unavailable'
 assert d['selected_model_compatible'] and d['provider_inventory_known'],'full development profile unavailable'
 memory_assertions(d['admission'])
 assert d['admission']['sampled_peak_pss_bytes']>0 and 0<d['admission']['sampled_peak_rss_bytes']<12_000_000_000-1073741824,'sampled model memory'
 assert d['admission']['sample_error'] is None and d['admission']['sampler_stopped'] and d['admission']['sample_count']>0,'memory sampler incomplete'
def main():
 run=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');out=ROOT/'downloads/android-runtime-durability'/('material-'+run);out.mkdir(parents=True);print(out,flush=True);started=time.time();android_start=None;android_end=None
 def cmd(name,args,timeout=120,allow_failure=False):
  begin=time.time()
  try:
   p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout);raw=p.stdout;code=p.returncode
  except subprocess.TimeoutExpired as e:raw=e.stdout or b'';code=124
  (out/(name+'.txt')).write_bytes(raw);(out/(name+'.command.json')).write_text(json.dumps({'args':args,'exit':code,'started_epoch':begin,'finished_epoch':time.time()},indent=2));assert allow_failure or code==0,(name,code);return raw
 def shell(name,s,timeout=120):return cmd(name,ADB+['shell',s],timeout)
 def database(label):
  raw=cmd(label,ADB+['exec-out','su','0','cat','/data/user/0/'+PKG+'/databases/reader-notebook.sqlite']);f=out/(label+'.sqlite');f.write_bytes(raw);db=sqlite3.connect('file:'+str(f)+'?mode=ro',uri=True);assert db.execute('pragma integrity_check').fetchone()[0]=='ok';schema=db.execute('pragma user_version').fetchone()[0];rows=db.execute('select id,created,kind,title,question,body,provenance,note,bookmark from entries order by id').fetchall();db.close();return schema,{str(r[0]):sha(json.dumps(r,ensure_ascii=False,separators=(',',':')).replace('/','\\/').encode()) for r in rows}
 def inventory(label):
  raw=shell(label,"su 0 sh -c 'find /data/user/0/org.pocketlore.app -type f -exec sha256sum {} \\;'",240)
  sizes=shell(label+'-sizes',"su 0 sh -c 'find /data/user/0/org.pocketlore.app -type f -exec stat -c \"%s %b %n\" {} \\;'",120)
  return {line.split('  ',1)[1]:line.split('  ',1)[0] for line in raw.decode().splitlines()}
 try:
  paths=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','android','tools/evaluation/android-runtime-durability','tools/runtime','tools/android-build.sh'],cwd=ROOT,text=True).splitlines()
  sources={p:sha((ROOT/p).read_bytes()) for p in sorted(set(paths)) if(ROOT/p).is_file()};(out/'source-inputs.json').write_text(json.dumps(sources,sort_keys=True));source_hash=sha((out/'source-inputs.json').read_bytes());(out/'executed-check.py').write_bytes(pathlib.Path(__file__).read_bytes());(out/'executed-witness.py').write_bytes(pathlib.Path(__file__).with_name('witness.py').read_bytes())
  code={p:{'sha256':h,'content':(ROOT/p).read_text()} for p,h in sources.items() if p.startswith('tools/evaluation/android-runtime-durability/') and (ROOT/p).suffix in ('.py','.java','.json','.xml','.gradle','.cpp')}
  assert all(sha(v['content'].encode())==v['sha256'] for v in code.values()),'Frozen code hash mismatch'
  (out/'executed-sources.json').write_text(json.dumps(code,sort_keys=True))
  cmd('packet-controls',[sys.executable,str(ROOT/'tools/evaluation/android-runtime-durability/material/packet_controls.py')])
  cmd('local-service-unavailable',['systemctl','--user','show','pocketlore-modern-emulator.service','-p','MainPID','-p','Restart','-p','NRestarts'],allow_failure=True)
  before_host=request(out,'before',source_hash,started)
  assert all(sha((ROOT/p).read_bytes())==h for p,h in sources.items()),'Source changed after freeze'
  android_start=time.time()
  before=shell('boot-before','cat /proc/sys/kernel/random/boot_id').decode().strip();shell('environment','getprop ro.build.version.sdk; getconf PAGE_SIZE; settings get system font_scale; settings get system accelerometer_rotation; settings get system user_rotation')
  package=shell('package-before','pm path '+PKG).decode().strip();assert package.startswith('package:'),'Package unavailable; no automatic recovery'
  shell('installed-before','sha256sum '+package.removeprefix('package:'));shell('stop-before','am force-stop '+PKG)
  schema_before,rows_before=database('before');wanted=json.loads((ROOT/'tools/evaluation/android-runtime-durability/fixtures/expected.json').read_text())['rows'];assert schema_before==2 and rows_before==wanted,'Protected original data mismatch before install'
  (out/'rows-before.json').write_text(json.dumps(rows_before,sort_keys=True));inv_before=inventory('inventory-before')
  baseline_bytes=(ROOT/'tools/evaluation/android-runtime-durability/fixtures/precrash-inventory.txt').read_bytes();(out/'precrash-inventory.txt').write_bytes(baseline_bytes)
  baseline={line.split('  ',1)[1]:line.split('  ',1)[0] for line in baseline_bytes.decode().splitlines()}
  protected=lambda p:'/cache/' not in p and '/code_cache/' not in p and '/databases/' not in p and not p.endswith('/files/notebook-export.json')
  differences={p:{'before':h,'after':inv_before.get(p)} for p,h in baseline.items() if protected(p) and inv_before.get(p)!=h}
  (out/'precrash-reconciliation.json').write_text(json.dumps({'baseline_sha256':sha(baseline_bytes),'protected_count':sum(protected(p) for p in baseline),'differences':differences},indent=2));assert not differences,'Precrash protected asset changed/missing'
  test_inventory_before=shell('test-inventory-before',"su 0 sh -c 'find /data/user/0/org.pocketlore.app.test -type f -exec sha256sum {} \\;'",240);shell('test-storage-before','su 0 du -sb /data/user/0/org.pocketlore.app.test; su 0 du -sk /data/user/0/org.pocketlore.app.test')
  apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk';test=ROOT/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk';expected=sha(apk.read_bytes());(out/'candidate.json').write_text(json.dumps({'source_hash':source_hash,'apk_sha256':expected,'test_sha256':sha(test.read_bytes()),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'native_libraries':{str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in (ROOT/'android/app/build/generated/nativeLibs').rglob('*.so')}},indent=2))
  cmd('install-main',ADB+['install','--no-incremental','-r',str(apk)],180);cmd('install-test',ADB+['install','--no-incremental','-r',str(test)],180)
  package=shell('package','pm path '+PKG).decode().strip();actual=shell('installed','sha256sum '+package.removeprefix('package:')).decode().split()[0];assert actual==expected
  testpath=shell('test-path','pm path '+PKG+'.test').decode().strip().removeprefix('package:');assert shell('test-hash','sha256sum '+testpath).decode().split()[0]==sha(test.read_bytes())
  phases=[]
  for phase in ['open','app-restart']:
   if phase=='app-restart':shell('app-stop','am force-stop '+PKG)
   raw=cmd(phase,ADB+['shell','am','instrument','-r','-w','-e','run',out.name,'-e','phase',phase,'-e','source_hash',source_hash,PKG+'.test/org.pocketlore.app.RuntimeDurabilityInstrumentation'],180).decode();assert 'INSTRUMENTATION_CODE: -1' in raw,'Instrumentation unsuccessful';line=next((x for x in raw.splitlines() if x.startswith('INSTRUMENTATION_RESULT: receipt=')),None);assert line,'Missing raw receipt';r=json.loads(line.split('=',1)[1]);(out/(phase+'.json')).write_text(json.dumps(r,indent=2));phases.append(r);assert r['status']=='PASS',r.get('error');assert r['run']==out.name and r['source_hash']==source_hash and r['row_hashes']==wanted
   for name in ['report.json','source201.png']:
    data=cmd(phase+'-'+name,ADB+['exec-out','run-as',PKG,'cat','files/runtime-durability-'+out.name+'-'+phase+'/'+name]);assert data.startswith(b'\x89PNG') if name.endswith('.png') else json.loads(data)==r
  shell('stop-model-before','am force-stop '+PKG);selected=shell('selected-before','run-as '+PKG+' cat files/model-selection').decode().strip()
  raw=cmd('native-admission',ADB+['shell','am','instrument','-r','-w','-e','run',out.name,'-e','source_hash',source_hash,'-e','phase','admission',PKG+'.test/org.pocketlore.app.RuntimeDurabilityInstrumentation'],240).decode();admission=json.loads(next(x for x in raw.splitlines() if x.startswith('INSTRUMENTATION_RESULT: admission_receipt=')).split('=',1)[1]);(out/'native-admission.json').write_text(json.dumps(admission,indent=2));assert 'INSTRUMENTATION_CODE: -1' in raw and admission['measurement_complete'],admission
  assert admission['run']==out.name and admission['source_hash']==source_hash and admission['selection']==selected
  compatible=admission['catalog_admitted'] and admission['native_admitted'] and admission['selection_unchanged'] and admission['generated_tokens']==0 and admission['resources_after_close']==[0]*5
  shell('stop-after','am force-stop '+PKG);schema_after,rows_after=database('after');(out/'rows-after.json').write_text(json.dumps(rows_after,sort_keys=True));inv_after=inventory('inventory-after')
  # Existing ephemeral instrumentation/export caches may change, but never models, sources,
  # preferences or notebook rows. Every exception is enumerated for independent inspection.
  changes={p:{'before':h,'after':inv_after.get(p)} for p,h in inv_before.items() if inv_after.get(p)!=h}
  allowed=lambda p: '/cache/' in p or '/code_cache/' in p or '/databases/' in p or p.endswith('/files/notebook-export.json')
  protected_changes={p:v for p,v in changes.items() if not allowed(p)};(out/'inventory-changes.json').write_text(json.dumps({'all_existing_changes':changes,'protected_changes':protected_changes,'new_files':sorted(set(inv_after)-set(inv_before))},indent=2));assert not protected_changes,'Protected files changed'
  after=shell('boot-after','cat /proc/sys/kernel/random/boot_id').decode().strip();cat=json.loads(shell('catalog','run-as '+PKG+' cat files/pack-library/catalog.json'));valid=all(inv_after.get('/data/user/0/'+PKG+'/files/pack-library/'+c['sha256']+'.plpack')==c['sha256'] for c in cat['collections'])
  test_inventory_after=shell('test-inventory-after',"su 0 sh -c 'find /data/user/0/org.pocketlore.app.test -type f -exec sha256sum {} \\;'",240);test_size=shell('test-storage-after','su 0 du -sb /data/user/0/org.pocketlore.app.test; su 0 du -sk /data/user/0/org.pocketlore.app.test').decode();assert test_inventory_before==test_inventory_after,'Existing instrumentation assets changed'
  memory=shell('guest-memory','cat /proc/meminfo').decode();ram=int(next(x.split()[1] for x in memory.splitlines() if x.startswith('MemTotal:')))*1024
  size=shell('logical','su 0 du -sb /data/user/0/'+PKG).decode();shell('allocated','su 0 du -sk /data/user/0/'+PKG);shell('disk','df -k /data');provider=shell('providers','dumpsys package '+PKG);actual_after=shell('installed-after','sha256sum '+package.removeprefix('package:')).decode().split()[0];assert actual_after==expected
  shell('environment-after','getprop ro.build.version.sdk; getconf PAGE_SIZE; settings get system font_scale; settings get system accelerometer_rotation; settings get system user_rotation');assert (out/'environment.txt').read_bytes()==(out/'environment-after.txt').read_bytes()
  android_end=time.time();after_host=request(out,'after',source_hash,started,android_end);owned=continuity(before_host,after_host,android_start,android_end)
  result={'run':out.name,'android_start_epoch':android_start,'android_end_epoch':android_end,'package_present':True,'apk_actual':actual_after,'apk_expected':expected,'boot_before':before,'boot_after':after,'rows_before':rows_before,'rows_after':rows_after,'rows_expected':wanted,'schema_before':schema_before,'schema_after':schema_after,'catalog_verified':valid,'assets_unchanged':not protected_changes,'source_hash':source_hash,'executed_source_hash':phases[0]['source_hash'],'phases':phases,'logical_bytes':int(size.split()[0])+int(test_size.split()[0])+apk.stat().st_size+test.stat().st_size,'guest_ram_bytes':ram,'owned_host_process_continuity':owned,'selected_model_compatible':compatible,'provider_inventory_known':b'org.pocketlore.app/.NotebookExportProvider' in provider and b'org.pocketlore.app.notebook' in provider,'admission':admission,'classification':'Bounded current owned lifecycle/profile; sustained renderer, full distribution, physical and quality gates remain open'}
  (out/'result.json').write_text(json.dumps(result,indent=2));assertions(result)
  controls=[]
  for name in ['missing-window','contradictory-peak','wrong-sample-pid']:
   bad=copy.deepcopy(admission)
   if name=='missing-window':bad['loaded_window_end_ns']=bad['loaded_window_start_ns']
   elif name=='contradictory-peak':bad['sampled_peak_rss_bytes']=1
   else:bad['memory_samples'][0]['pid']=-1
   try:memory_assertions(bad)
   except AssertionError:controls.append(name)
   else:raise AssertionError('memory negative accepted '+name)
  for field,value in [('package_present',False),('apk_actual','wrong'),('boot_after','changed'),('rows_after',{}),('schema_after',1),('catalog_verified',False),('executed_source_hash','stale'),('logical_bytes',50_000_000_001),('owned_host_process_continuity',False),('provider_inventory_known',False),('selected_model_compatible',False),('rows_expected',{})]:
   bad=copy.deepcopy(result);bad[field]=value
   try:assertions(bad)
   except AssertionError:controls.append(field)
   else:raise AssertionError('negative accepted '+field)
  for field in ('pid','proc_start_ticks','host_boot_id','executable_sha256'):
   bad=copy.deepcopy(after_host);bad[field]='changed'
   try:continuity(before_host,bad,android_start,android_end)
   except AssertionError:controls.append('witness-'+field)
   else:raise AssertionError('changed witness accepted')
  for field in ('InvocationID','ExecMainStartTimestampMonotonic'):
   bad=copy.deepcopy(after_host);bad['props'][field]='changed'
   try:continuity(before_host,bad,android_start,android_end)
   except AssertionError:controls.append('witness-'+field)
   else:raise AssertionError('changed invocation accepted')
  bad=copy.deepcopy(before_host);bad['observed_epoch']=android_end+1
  try:continuity(bad,after_host,android_start,android_end)
  except AssertionError:controls.append('stale-unbracketed-witness')
  else:raise AssertionError('stale witness accepted')
  (out/'negative-controls.json').write_text(json.dumps({'constructed_mutations_of_actual_pass':controls},indent=2));print('PASS bounded owned runtime continuity and exact pinned model profile; sustained stability remains open')
 except BaseException as e:
  (out/'failure.json').write_text(json.dumps({'status':'FAIL','error':traceback.format_exc(),'android_start_epoch':android_start,'android_end_epoch':android_end,'at':time.time()},indent=2));raise
 finally:
  freeze_packet(out)
if __name__=='__main__':main()
