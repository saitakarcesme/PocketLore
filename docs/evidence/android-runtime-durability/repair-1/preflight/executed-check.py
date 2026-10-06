"""Bounded owned-device validation. Never installs the main APK or restores/deletes data."""
import pathlib,subprocess,json,hashlib,datetime,sqlite3,sys,copy,re
ROOT=pathlib.Path(__file__).resolve().parents[3];ADB=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5564'];PKG='org.pocketlore.app'
def sha(b):return hashlib.sha256(b).hexdigest()
def assertions(d):
 assert d['package_present'] and d['apk_actual']==d['apk_expected'],'missing/wrong APK'
 assert d['boot_before']==d['boot_after'] and d['boot_before'],'boot discontinuity'
 assert d['rows_before']==d['rows_after']==d['rows_expected'] and len(d['rows_after'])==201,'changed/missing original rows'
 assert d['catalog_verified'] and d['assets_unchanged'],'source/asset identity'
 assert d['source_hash']==d['executed_source_hash'],'source mismatch'
 assert all(r['status']=='PASS' for r in d['phases']) and len(d['phases'])==2,'partial lifecycle'
 assert d['logical_bytes']<=50_000_000_000 and d['guest_ram_bytes']<=12_000_000_000,'resource cap'
 assert d['owned_host_process_continuity'],'host process identity unavailable'
 assert d['selected_model_compatible'] and d['provider_inventory_known'],'full development profile unavailable'
def main():
 run=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');out=ROOT/'downloads/android-runtime-durability'/('check-'+run);out.mkdir(parents=True);print(out,flush=True)
 def cmd(name,args,timeout=90,allow_failure=False):
  p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout);(out/(name+'.txt')).write_bytes(p.stdout);(out/(name+'.command.json')).write_text(json.dumps({'args':args,'exit':p.returncode}));assert allow_failure or p.returncode==0,(name,p.returncode);return p.stdout
 def shell(name,s):return cmd(name,ADB+['shell',s])
 paths=subprocess.check_output(['git','ls-files','android','tools/evaluation/android-runtime-durability'],cwd=ROOT,text=True).splitlines();sources={p:sha((ROOT/p).read_bytes()) for p in paths if(ROOT/p).is_file()};(out/'source-inputs.json').write_text(json.dumps(sources,sort_keys=True));source_hash=sha((out/'source-inputs.json').read_bytes())
 service_before=cmd('service-before',['systemctl','--user','show','pocketlore-modern-emulator.service','-p','MainPID','-p','Restart','-p','NRestarts'],allow_failure=True)
 if b'MainPID=' not in service_before or b'Restart=no' not in service_before:
  failure={'status':'BLOCKED','full_gate_pass':False,'reason':'Fresh owned-host identity and Restart=no proof unavailable; stop before repeated UI/lifecycle work','source_hash':source_hash}
  (out/'preflight-failure.json').write_text(json.dumps(failure,indent=2));raise AssertionError(failure['reason'])
 before=shell('boot-before','cat /proc/sys/kernel/random/boot_id').decode().strip();package=shell('package','pm path '+PKG).decode().strip();assert package.startswith('package:'),'Package unavailable; no automatic installation'
 apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk';expected=sha(apk.read_bytes());actual=shell('installed','sha256sum '+package.removeprefix('package:')).decode().split()[0];assert actual==expected,'Wrong candidate; no automatic replacement'
 def database(label):
  raw=cmd(label,ADB+['exec-out','su','0','cat','/data/user/0/'+PKG+'/databases/reader-notebook.sqlite']);f=out/(label+'.sqlite');f.write_bytes(raw);db=sqlite3.connect('file:'+str(f)+'?mode=ro',uri=True);assert db.execute('pragma integrity_check').fetchone()[0]=='ok';rows=db.execute('select id,created,kind,title,question,body,provenance,note,bookmark from entries order by id').fetchall();db.close();return {str(r[0]):sha(json.dumps(r,ensure_ascii=False,separators=(',',':')).replace('/','\\/').encode()) for r in rows}
 shell('stop-before','am force-stop '+PKG);rows_before=database('before');wanted=json.loads((ROOT/'tools/evaluation/android-runtime-durability/fixtures/expected.json').read_text())['rows'];assert rows_before==wanted,'Original records changed'
 inventory=shell('assets-before',"su 0 sh -c 'find /data/user/0/org.pocketlore.app/files/pack-library /data/user/0/org.pocketlore.app/files/model-library -type f -exec sha256sum {} \\;'")
 mem=shell('guest-memory','cat /proc/meminfo').decode();ram=int(next(x.split()[1] for x in mem.splitlines() if x.startswith('MemTotal:')))*1024
 test=ROOT/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk';cmd('test-install',ADB+['install','--no-incremental','-r',str(test)]);testpath=shell('test-path','pm path '+PKG+'.test').decode().strip().removeprefix('package:');assert shell('test-hash','sha256sum '+testpath).decode().split()[0]==sha(test.read_bytes())
 phases=[]
 for phase in ['open','app-restart']:
  if phase=='app-restart':shell('app-stop','am force-stop '+PKG)
  raw=cmd(phase,ADB+['shell','am','instrument','-r','-w','-e','run',run,'-e','phase',phase,'-e','source_hash',source_hash,PKG+'.test/org.pocketlore.app.RuntimeDurabilityInstrumentation'],180).decode();line=next((x for x in raw.splitlines() if x.startswith('INSTRUMENTATION_RESULT: receipt=')),None);assert line,'Missing raw receipt';r=json.loads(line.split('=',1)[1]);(out/(phase+'.json')).write_text(json.dumps(r,indent=2));phases.append(r);assert r['status']=='PASS',r.get('error');assert r['run']==run and r['source_hash']==source_hash and r['row_hashes']==wanted
  for name in ['report.json','source201.png']:
   data=cmd(phase+'-'+name,ADB+['exec-out','run-as',PKG,'cat','files/runtime-durability-'+run+'-'+phase+'/'+name]);assert data.startswith(b'\x89PNG') if name.endswith('.png') else json.loads(data)==r
 shell('stop-after','am force-stop '+PKG);rows_after=database('after');after=shell('boot-after','cat /proc/sys/kernel/random/boot_id').decode().strip();asset_after=shell('assets-after',"su 0 sh -c 'find /data/user/0/org.pocketlore.app/files/pack-library /data/user/0/org.pocketlore.app/files/model-library -type f -exec sha256sum {} \\;'")
 cat=json.loads(shell('catalog',"run-as org.pocketlore.app cat files/pack-library/catalog.json"));hashes={line.split('  ',1)[1]:line.split('  ',1)[0] for line in inventory.decode().splitlines()};valid=all(hashes.get('/data/user/0/'+PKG+'/files/pack-library/'+c['sha256']+'.plpack')==c['sha256'] for c in cat['collections'])
 size=shell('logical',"su 0 du -sb /data/user/0/org.pocketlore.app").decode();shell('allocated',"su 0 du -sk /data/user/0/org.pocketlore.app");selected=shell('selected',"run-as org.pocketlore.app cat files/model-selection").decode();spec_hashes=re.findall(r'new Spec\([^\n]+"([a-f0-9]{64})",[0-9]+L\)',(ROOT/'android/app/src/main/java/org/pocketlore/app/ModelCatalog.java').read_text());compatible=selected in spec_hashes and any(line.startswith(selected+'  ') and line.endswith('/model-library/'+selected+'.gguf') for line in inventory.decode().splitlines())
 provider=shell('providers',"dumpsys package org.pocketlore.app");service=cmd('service-after',['systemctl','--user','show','pocketlore-modern-emulator.service','-p','MainPID','-p','Restart','-p','NRestarts'],allow_failure=True)
 result={'run':run,'package_present':True,'apk_actual':actual,'apk_expected':expected,'boot_before':before,'boot_after':after,'rows_before':rows_before,'rows_after':rows_after,'rows_expected':wanted,'catalog_verified':valid,'assets_unchanged':inventory==asset_after,'source_hash':source_hash,'executed_source_hash':phases[0]['source_hash'],'phases':phases,'logical_bytes':int(size.split()[0])+apk.stat().st_size+test.stat().st_size,'guest_ram_bytes':ram,'owned_host_process_continuity':service==service_before and b'MainPID=' in service and b'MainPID=0\n' not in service and b'Restart=no' in service,'selected_model_compatible':compatible,'provider_inventory_known':b'org.pocketlore.app/.NotebookExportProvider' in provider and b'org.pocketlore.app.notebook' in provider,'classification':'INCOMPLETE: host PID namespace/bus inaccessible; full development profile must qualify independently'}
 (out/'result.json').write_text(json.dumps(result,indent=2));controls=[]
 good=copy.deepcopy(result);good['owned_host_process_continuity']=True;good['selected_model_compatible']=True;good['provider_inventory_known']=True;assertions(good)
 for field,value in [('package_present',False),('apk_actual','wrong'),('boot_after','changed'),('rows_after',{}),('catalog_verified',False),('executed_source_hash','stale'),('logical_bytes',50_000_000_001),('owned_host_process_continuity',False),('provider_inventory_known',False),('selected_model_compatible',False),('rows_expected',{})]:
  bad=copy.deepcopy(good);bad[field]=value
  try:assertions(bad)
  except AssertionError:controls.append(field)
  else:raise AssertionError('negative accepted '+field)
 (out/'negative-controls.json').write_text(json.dumps({'constructed_validation_controls_not_device_success':controls},indent=2));assertions(result);print('PASS full runtime durability')
if __name__=='__main__':main()
