#!/usr/bin/env python3
"""Run existing behavioral lanes serially; verify one candidate and hash-bound reports."""
import pathlib,subprocess,os,json,time,hashlib,threading,shutil,tempfile,sys
ROOT=pathlib.Path(__file__).resolve().parents[3];ADB='/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb'
LANES=[('product_ui','check_product_ui.sh','downloads/product-ui/runs'),('documents','check_documents.sh','downloads/documents-runs'),('attachments','check_attachments.sh','downloads/attachments/runs'),('model_management','check_model_management.sh','downloads/model-management'),('nearby','check_nearby_travel.sh','downloads/nearby-travel'),('cache','check_hybrid_retrieval.sh','downloads/hybrid-retrieval'),('specialist','check_specialist_collections.sh','downloads/specialist')]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def verify(out):
 manifest=json.loads((out/'manifest.json').read_text());assert manifest['status']=='PASS';assert {x['name'] for x in manifest['lanes']}=={x[0] for x in LANES}
 for name,digest in manifest['files'].items():assert sha(out/name)==digest,name
 candidate=manifest['apk_sha256']
 for lane in manifest['lanes']:
  p=out/lane['name'];r=json.loads((p/'receipt.json').read_text());assert r['status']=='PASS',lane
  claimed=r.get('apk_sha256',r.get('artifacts',{}).get('app-debug.apk',{}).get('sha256'));assert claimed==candidate,('different candidate',lane)
  assert (p/'integrated-installed-hash.txt').read_text().split()[0]==candidate
  reports={name:json.loads((p/name).read_text()) for name in lane['reports']}
  assert reports and all(r['status']=='PASS' for r in reports.values())
 docs=json.loads((out/'documents/results.json').read_text());assert {'personal_library_return_does_not_infer','library_import_reloads_retained_research'}.issubset(docs['checks'])
 attachments=json.loads((out/'attachments/results.json').read_text());assert {f'edited_recognition_is_question_{i}' for i in (3,4)}.issubset(attachments['checks']);assert {f'recognition_not_submitted_or_evidence_{i}' for i in (3,4)}.issubset(attachments['checks'])
 model=json.loads((out/'model_management/select.json').read_text());assert model['generation_performed'] is False and 'unverified_token_output' not in model;assert 'Actual JNI load failure reloads previous model and preserves selection' in model['checks']
 assert json.loads((out/'alignment.json').read_text())['valid']
 samples=[json.loads(x) for x in (out/'storage-samples.jsonl').read_text().splitlines()];assert all(any(s['serial']==serial and s.get('logical_bytes',0)>0 and s.get('allocated_bytes',0)>0 for s in samples) for serial in ('emulator-5560','emulator-5562'))
 for serial in ('emulator-5560','emulator-5562'):
  assert (out/(serial+'-assets-before.txt')).read_bytes()==(out/(serial+'-assets-after.txt')).read_bytes()
  assert (out/(serial+'-selection-before.txt')).read_bytes()==(out/(serial+'-selection-after.txt')).read_bytes()
 if (out/'storage-audit').is_dir():
  pins=json.loads((ROOT/'tools/attachments/models.json').read_text());expected={v['sha256'] for v in pins.values()}
  for serial in ('emulator-5560','emulator-5562'):
   assert {line.split()[0] for line in (out/'storage-audit'/(serial+'-recognition-hashes.txt')).read_text().splitlines()}==expected
 return manifest

def main():
 reuse=pathlib.Path(sys.argv[2]) if len(sys.argv)>2 and sys.argv[1]=='--reuse' else None
 if len(sys.argv)>1 and reuse is None:verify(pathlib.Path(sys.argv[1]));print('Verified integrated receipts');return
 out=ROOT/'downloads/integrated-candidate'/time.strftime('%Y%m%dT%H%M%SZ',time.gmtime());out.mkdir(parents=True);print(out,flush=True)
 def run(cmd,name,timeout=600):
  r=subprocess.run(list(map(str,cmd)),cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout);(out/name).write_bytes(r.stdout);assert r.returncode==0,(name,r.stdout[-2000:]);return r.stdout
 def adb(serial,args,name):return run([ADB,'-s',serial]+args,name)
 assets=['files/model.gguf','files/pack-library/catalog.json','files/scale-library/catalog.json']
 for serial in ['emulator-5560','emulator-5562']:
  adb(serial,['shell','getprop'],serial+'-properties.txt');adb(serial,['shell','run-as','org.pocketlore.app','sha256sum']+assets,serial+'-assets-before.txt');adb(serial,['shell','run-as','org.pocketlore.app','sh','-c',"'if test -f files/model-selection; then cat files/model-selection; else echo legacy-model.gguf; fi'"],serial+'-selection-before.txt')
 run(['bash','tools/android-build.sh'],'build-required.log');apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk';candidate=sha(apk)
 run(['python3','tools/evaluation/verify_16kb_artifacts.py',apk],'alignment.json')
 stop=threading.Event();lane_name='initial';lock=threading.Lock()
 def sample():
  while not stop.is_set():
   for serial in ['emulator-5560','emulator-5562']:
    record={'time_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'serial':serial,'lane':lane_name}
    for flag,key in [('b','logical_bytes'),('k','allocated_bytes')]:
     p=subprocess.run([ADB,'-s',serial,'shell','run-as','org.pocketlore.app','du','-s'+flag,'.'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
     if p.returncode==0:
      try:record[key]=int(p.stdout.split()[0])*(1024 if flag=='k' else 1)
      except ValueError:record[key+'_error']=p.stdout.decode(errors='replace')
    test=subprocess.run([ADB,'-s',serial,'shell','run-as','org.pocketlore.app.test','du','-sk','.'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
    if test.returncode==0:record['test_provider_allocated_bytes']=int(test.stdout.split()[0])*1024
    with lock:
     with (out/'storage-samples.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
   stop.wait(3)
 sampler=threading.Thread(target=sample);sampler.start();lanes=[]
 try:
  for name,script,folder in LANES:
   lane_name=name
   report_names={'product_ui':['report-default.json','report-large.json','cold-report.json'],'documents':['results.json','restart.json'],'attachments':['results.json'],'model_management':['import.json','select.json'],'nearby':['report.json'],'cache':['report.json'],'specialist':['install.json','restart.json']}[name]
   serial='emulator-5562' if name in ('cache','specialist') else 'emulator-5560'
   previous=reuse/name if reuse else None
   if previous and (previous/'receipt.json').is_file() and (previous/'integrated-installed-hash.txt').is_file():
    receipt=json.loads((previous/'receipt.json').read_text());claimed=receipt.get('apk_sha256',receipt.get('artifacts',{}).get('app-debug.apk',{}).get('sha256'))
    assert receipt['status']=='PASS' and claimed==candidate and (previous/'integrated-installed-hash.txt').read_text().split()[0]==candidate
    assert all(json.loads((previous/n).read_text())['status']=='PASS' for n in report_names)
    # Reuse only complete, same-candidate Android runs, retaining their original times.
    shutil.copytree(previous,out/name);lanes.append({'name':name,'serial':serial,'source':str(previous),'reports':report_names,'reused':True});print(name+' REUSED PASS',flush=True);continue
   base=ROOT/folder;before=set(base.glob('*'));env=os.environ.copy();env['POCKETLORE_NO_GENERATION']='1'
   with (out/(name+'.log')).open('wb') as log:r=subprocess.run(['bash','tools/evaluation/'+script],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1500)
   created=[p for p in base.glob('*') if p not in before and p.is_dir()];assert len(created)==1,(name,created);source=created[0];target=out/name;target.mkdir()
   for p in source.rglob('*'):
    if p.is_file() and p.suffix not in ('.apk','.plpack','.gguf','.bin'):
     destination=target/p.relative_to(source);destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,destination)
   assert r.returncode==0,('Behavioral lane failed',name,str(source))
   serial='emulator-5562' if name in ('cache','specialist') else 'emulator-5560'
   path=adb(serial,['shell','pm','path','org.pocketlore.app'],name+'/integrated-installed-path.txt').decode().strip().removeprefix('package:');adb(serial,['shell','sha256sum',path],name+'/integrated-installed-hash.txt')
   assert sha(apk)==candidate,'Application changed between lanes'
   report_names={'product_ui':['report-default.json','report-large.json','cold-report.json'],'documents':['results.json','restart.json'],'attachments':['results.json'],'model_management':['import.json','select.json'],'nearby':['report.json'],'cache':['report.json'],'specialist':['install.json','restart.json']}[name]
   lanes.append({'name':name,'serial':serial,'source':str(source),'reports':report_names});print(name+' PASS',flush=True)
 finally:stop.set();sampler.join(65)
 for serial in ['emulator-5560','emulator-5562']:
  adb(serial,['shell','run-as','org.pocketlore.app','sha256sum']+assets,serial+'-assets-after.txt')
  for folder in ['files/model-library','files/attachment-assets','files/pack-library','files/scale-library']:
   adb(serial,['shell','run-as','org.pocketlore.app','sh','-c',"'if test -d "+folder+"; then du -ak "+folder+"; else echo absent; fi'"],serial+'-'+folder.split('/')[-1]+'-allocated.txt')
  adb(serial,['shell','run-as','org.pocketlore.app','cat','files/pack-library/catalog.json','files/scale-library/catalog.json'],serial+'-catalogs.txt');adb(serial,['shell','run-as','org.pocketlore.app','sh','-c',"'if test -f files/model-selection; then cat files/model-selection; else echo legacy-model.gguf; fi'"],serial+'-selection-after.txt')
  adb(serial,['shell','dumpsys','meminfo','org.pocketlore.app'],serial+'-memory.txt')
 storage_dir=pathlib.Path(run(['python3','tools/evaluation/integrated-candidate/storage_snapshot.py'],'storage-audit.log').decode().strip());shutil.copytree(storage_dir,out/'storage-audit')
 manifest={'status':'PASS','apk_sha256':candidate,'apk_bytes':apk.stat().st_size,'lanes':lanes,'files':{str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');verify(out)
 # Mutate only disposable copies of actual raw reports, never canonical evidence.
 with tempfile.TemporaryDirectory(dir=ROOT/'downloads/integrated-candidate') as tmp:
  copy=pathlib.Path(tmp)/'evidence';shutil.copytree(out,copy);f=copy/'model_management/select.json';raw=f.read_bytes()
  for kind in ['changed','missing','wrong-candidate']:
   f.write_bytes(raw)
   if kind=='changed':f.write_bytes(raw+b' ')
   elif kind=='missing':f.unlink()
   else:
    m=json.loads((copy/'manifest.json').read_text());m['apk_sha256']='0'*64;(copy/'manifest.json').write_text(json.dumps(m))
   try:verify(copy)
   except (AssertionError,FileNotFoundError):pass
   else:raise AssertionError('Invalid evidence accepted: '+kind)
 (out/'negative-controls.json').write_text(json.dumps({'changed_report':'rejected','missing_report':'rejected','wrong_candidate':'rejected'})+'\n');print(json.dumps({'status':'PASS','output':str(out),'candidate':candidate}))
if __name__=='__main__':main()
