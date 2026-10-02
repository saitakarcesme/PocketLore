"""Fresh5560 manual-comparison feature checks; no model execution or downloads."""
import hashlib,json,pathlib,subprocess,time,uuid,copy
ROOT=pathlib.Path(__file__).resolve().parents[3]
ADB=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5560']
def sha(b):return hashlib.sha256(b).hexdigest()
def sources():
 names=subprocess.check_output(['git','ls-files','android','tools'],cwd=ROOT).decode().splitlines()
 return {n:sha((ROOT/n).read_bytes()) for n in names if (ROOT/n).is_file()}
def verify(d):
 m=json.loads(d['manifest.json']);src=json.loads(d['source-inputs.json']);assert src['sources']==m['sources_after']
 assert sha(d['source-inputs.json'])==m['source_hash']
 assert d['boot-before.txt']==d['boot-after.txt'] and d['font-before.txt']==d['font-after.txt']
 assert d['retained-before.txt']==d['retained-after.txt']
 for n,h in m['files'].items():assert sha(d[n])==h,n
 for phase in ['first','cold']:
  r=json.loads(d[phase+'.json']);assert r['status']=='PASS' and r['run_id']==m['run_id'] and r['source_manifest_sha256']==m['source_hash']
  raw=d[phase+'-runtime.txt'].decode();assert 'INSTRUMENTATION_CODE: -1' in raw and 'Process crashed' not in raw
  decoded=json.loads(next(s.split('=',1)[1] for s in raw.splitlines() if s.startswith('INSTRUMENTATION_RESULT: comparison_receipt=')));assert decoded==r
  assert json.loads(d[phase+'-runtime.txt.command.json'])['returncode']==0
 for pkg,info in m['apks'].items():
  for when in ['installed','final']:assert d[when+'-'+pkg+'.txt'].decode().split()[0]==info['sha256']
 r=json.loads(d['first.json']);required={'saved_creates_grid','ui_exact_selected_quote','exact_source_reader_identity','recreation_retains_quote_note','portable_gap_identity_offsets','export_retry_exact_bytes','clear_unknown_gap','research_record_denied','six_dimension_limit','corrupt_literal_gap','corrupt_hash_gap','stale_offset_gap','missing_source_gap','split_surrogate_denied','blocked_export_cancelled'};assert required<=set(r['checks'])
 cold=json.loads(d['cold.json']);assert {'cold_store_exact_export','cold_note_retained','original_notebook_records_retained'}<=set(cold['checks'])
 for name in ['manual-grid','unknown-grid','cold-grid']:
  assert d[name+'.png'].startswith(b'\x89PNG') and len(d[name+'.png'])>10000
  assert b'clickable=true' in d[name+'-accessibility.txt']
 return m

def main():
 id=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'-'+uuid.uuid4().hex[:8];out=ROOT/'downloads/evidence-comparison'/id;out.mkdir(parents=True);print(out,flush=True)
 def run(cmd,name,timeout=240):
  try:p=subprocess.run([str(x) for x in cmd],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
  except subprocess.TimeoutExpired as e:(out/name).write_bytes(e.stdout or b'');(out/(name+'.command.json')).write_text(json.dumps({'returncode':-1,'timeout':timeout}));raise
  (out/name).write_bytes(p.stdout);(out/(name+'.command.json')).write_text(json.dumps({'command':[str(x) for x in cmd],'returncode':p.returncode}));assert p.returncode==0,(name,out);return p.stdout
 def shell(cmd,name):return run(ADB+['shell',*cmd],name)
 fixture=ROOT/'docs/evidence/evidence-comparison/fixtures.json';assert sha(fixture.read_bytes())=='210225f3530e44141bc6ed8c180ad13c822ce870d9628194fc093b646fe695d3'
 src={'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),'sources':sources(),'fixture_sha256':sha(fixture.read_bytes()),'gradle_workers':2,'gradle_heap':'2GiB','sdk_jar_sha256':sha(pathlib.Path('/home/isa/Android/atlas-toolchain/sdk/platforms/android-35/android.jar').read_bytes())}
 (out/'source-inputs.json').write_text(json.dumps(src,sort_keys=True,indent=2)+'\n');source_hash=sha((out/'source-inputs.json').read_bytes())
 run(['bash','tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',ROOT/'tools/evaluation/evidence-comparison/source.gradle','-PpocketloreTestRunner=org.pocketlore.app.ComparisonInstrumentation'],'build.log',300);assert sources()==src['sources']
 apks={}
 for pkg,path in [('app','debug/app-debug.apk'),('test','androidTest/debug/app-debug-androidTest.apk')]:
  p=ROOT/'android/app/build/outputs/apk'/path;apks[pkg]={'path':str(p),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
 (out/'apks.json').write_text(json.dumps(apks,indent=2))
 assert run(ADB+['get-state'],'state.txt').strip()==b'device'
 for cmd,name in [(['getprop','ro.build.version.sdk'],'sdk.txt'),(['getconf','PAGE_SIZE'],'pages.txt'),(['cat','/proc/sys/kernel/random/boot_id'],'boot-before.txt'),(['settings','get','system','font_scale'],'font-before.txt')]:shell(cmd,name)
 def installed(pkg,label):
  path=shell(['pm','path','org.pocketlore.app'+('.test' if pkg=='test' else '')],label+'-path-'+pkg+'.txt').decode().strip().removeprefix('package:');assert path.startswith('/data/app/') and '\n' not in path;shell(['sha256sum',path],label+'-'+pkg+'.txt')
 def retain(label):
  command="for p in files/model.gguf files/model-selection files/model-library files/pack-library files/scale-library files/attachment-assets; do if [ -e \\\"$p\\\" ]; then find \\\"$p\\\" -type f -exec sha256sum {} \\\\; ; else echo ABSENT:$p; fi; done | sort"
  command=command.replace('\\"','"').replace('\\\\;','\\;')
  shell(['run-as','org.pocketlore.app','sh','-c',"'"+command+"'"],'retained-'+label+'.txt')
 def disk(label):
  for flags,kind in [('sb','logical'),('sk','allocated')]:shell(['run-as','org.pocketlore.app','du','-'+flags,'.'],kind+'-'+label+'.txt')
 for pkg in apks:installed(pkg,'before')
 retain('before');disk('before')
 for pkg,item in apks.items():run(ADB+['install','--no-incremental','-r',item['path']],'install-'+pkg+'.txt');installed(pkg,'installed')
 for phase in ['first','cold']:
  if phase=='cold':shell(['am','force-stop','org.pocketlore.app'],'cold-stop.txt')
  raw=run(ADB+['shell','am','instrument','-r','-w','-e','run_id',id,'-e','phase',phase,'-e','source_manifest_sha256',source_hash,'org.pocketlore.app.test/org.pocketlore.app.ComparisonInstrumentation'],phase+'-runtime.txt')
  report=json.loads(next(line.split('=',1)[1] for line in raw.decode().splitlines() if line.startswith('INSTRUMENTATION_RESULT: comparison_receipt=')));(out/(phase+'.json')).write_text(json.dumps(report,indent=2)+'\n')
  assert report['status']=='PASS',(phase,report.get('error'),out)
 for name in ['manual-grid.png','manual-grid-accessibility.txt','unknown-grid.png','unknown-grid-accessibility.txt','cold-grid.png','cold-grid-accessibility.txt','comparison-export.txt','state.json']:
  run(ADB+['exec-out','run-as','org.pocketlore.app','cat','files/comparison-check-'+id+'/'+name],name)
 shell(['cat','/proc/sys/kernel/random/boot_id'],'boot-after.txt');shell(['settings','get','system','font_scale'],'font-after.txt');retain('after');disk('after')
 for pkg in apks:installed(pkg,'final')
 m={'run_id':id,'serial':'emulator-5560','source_hash':source_hash,'sources_after':sources(),'apks':apks,'files':{p.name:sha(p.read_bytes()) for p in out.iterdir() if p.is_file()}}
 (out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');d={p.name:p.read_bytes() for p in out.iterdir() if p.is_file()};verify(d);negative=[]
 for kind in ['missing','corrupt','stale','changed-test']:
  bad=dict(d)
  if kind=='missing':del bad['cold-runtime.txt']
  elif kind=='corrupt':bad['first.json']+=b'x'
  elif kind=='stale':r=json.loads(bad['first.json']);r['run_id']='stale';bad['first.json']=json.dumps(r).encode()
  else:bad['installed-test.txt']=b'0'*64
  try:verify(bad)
  except (AssertionError,KeyError,ValueError):negative.append(kind)
  else:raise AssertionError(kind)
 (out/'negative-controls.json').write_text(json.dumps(negative));print(json.dumps({'status':'PASS','output':str(out)}))
if __name__=='__main__':main()
