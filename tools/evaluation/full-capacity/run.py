#!/usr/bin/env python3
"""Dedicated 5562 cumulative installation. Resumes completed steps without replacing evidence."""
import hashlib,json,pathlib,subprocess,time,zipfile,shutil,threading,os
ROOT=pathlib.Path(__file__).resolve().parents[3]
OUT=ROOT/'docs/evidence/full-capacity/run';SCRATCH=ROOT/'downloads/full-capacity'
LANES=pathlib.Path('/home/isa/PocketLore-control/scale-workers')
ADB=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5562']
PKG='org.pocketlore.app'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def adb(*args):return subprocess.check_output(ADB+list(args),text=True)
def shell(s):return adb('shell',s)
def push(p,remote):
 shell('run-as '+PKG+' mkdir -p '+str(pathlib.PurePosixPath(remote).parent))
 with p.open('rb') as f:subprocess.run(ADB+['shell',"run-as "+PKG+" sh -c 'cat > "+remote+"'"],stdin=f,check=True)
def step(label,mode,archive=None):
 d=OUT/label
 if (d/'result.json').exists():
  r=json.loads((d/'result.json').read_text());assert r['status']=='PASS';return r
 d.mkdir(parents=True,exist_ok=False)
 stop=threading.Event()
 def monitor():
  with (d/'disk-samples.jsonl').open('w') as f:
   while not stop.is_set():
    f.write(json.dumps({'monotonic':time.monotonic(),'df_k':shell('df -k /data')})+'\n');f.flush();stop.wait(1)
 t=threading.Thread(target=monitor);t.start()
 try:
  with (d/'instrumentation.log').open('w') as log:
   proc=subprocess.Popen(ADB+['shell','am','instrument','-w','-e','mode',mode,PKG+'.test/'+PKG+'.FullCapacityInstrumentation'],stdout=log,stderr=subprocess.STDOUT)
   if archive:
    for _ in range(240):
     if subprocess.run(ADB+['shell','run-as',PKG,'test','-p','files/capacity-input'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:break
     if proc.poll() is not None:raise RuntimeError('No FIFO: '+label)
     time.sleep(.25)
    else:raise RuntimeError('FIFO timeout')
    with archive.open('rb') as f:
     tx=subprocess.run(ADB+['shell',"run-as "+PKG+" sh -c 'cat > files/capacity-input'"],stdin=f,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=1800)
    (d/'transport.log').write_bytes(tx.stdout)
    if mode=='import':assert tx.returncode==0
   proc.wait(timeout=1800)
  assert 'INSTRUMENTATION_CODE: -1' in (d/'instrumentation.log').read_text(),label
  raw=shell('run-as '+PKG+' cat files/capacity-result.json');r=json.loads(raw);assert r['mode']==mode
  (d/'result.json').write_text(raw);print(label,r['status'],r.get('elapsed_ms',''),flush=True);return r
 finally:stop.set();t.join()
def catalog():
 p=subprocess.run(ADB+['shell','run-as',PKG,'cat','files/scale-library/catalog.json'],capture_output=True,text=True)
 if p.returncode:return {}
 result={}
 for e in json.loads(p.stdout):
  m=json.loads(shell('run-as '+PKG+' cat files/scale-library/'+e['id']+'/manifest.json'));result[m['kind']]=(e['id'],m)
 return result
def transfer(label,m,paths,mode='import'):
 d=OUT/(label+'-input');d.mkdir(parents=True,exist_ok=True)
 raw=(json.dumps(m,sort_keys=True,indent=2)+'\n').encode();mp=d/'manifest.json'
 if mp.exists():assert mp.read_bytes()==raw
 else:mp.write_bytes(raw)
 if (OUT/label/'result.json').exists():return step(label,mode)
 archive=SCRATCH/'incoming.plscale'
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as z:
  z.writestr(zipfile.ZipInfo('manifest.json',(2026,10,1,0,0,0)),raw)
  for f in m['files']:
   if not f['payload']:continue
   p=paths[f['path']];info=zipfile.ZipInfo(f['path'],(2026,10,1,0,0,0));info.file_size=p.stat().st_size
   with p.open('rb') as src,z.open(info,'w',force_zip64=True) as dst:
    shutil.copyfileobj(src,dst,1048576)
 save(d/'transfer.json',{'bytes':archive.stat().st_size,'sha256':sha(archive),'transport':'local ADB FIFO, no device archive copy'})
 r=step(label,mode,archive);archive.unlink();return r

def main():
 OUT.mkdir(parents=True,exist_ok=True);SCRATCH.mkdir(parents=True,exist_ok=True)
 if not (OUT/'environment.json').exists():
  assert shell('getprop sys.boot_completed').strip()=='1'
  env={key:shell(cmd) for key,cmd in {'fingerprint':'getprop ro.build.fingerprint','abi':'getprop ro.product.cpu.abi','api':'getprop ro.build.version.sdk','data_df_k':'df -k /data','memory':'cat /proc/meminfo','cpu':'cat /proc/cpuinfo','boot_id':'cat /proc/sys/kernel/random/boot_id'}.items()};env['serial']='emulator-5562';assert env['api'].strip()=='35' and env['abi'].strip()=='x86_64';assert int(env['data_df_k'].splitlines()[-1].split()[1])*1024>50_000_000_000;save(OUT/'environment.json',env)
  app=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk';test=ROOT/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk'
  for p in [app,test]:subprocess.run(ADB+['install','-r',str(p)],check=True)
  for p,name in [(app,'app.apk'),(test,'test.apk')]:shutil.copyfile(p,SCRATCH/name)
  save(OUT/'runtime.json',{'apk':{'path':str(SCRATCH/'app.apk'),'bytes':app.stat().st_size,'sha256':sha(app)},'test_apk':{'path':str(SCRATCH/'test.apk'),'bytes':test.stat().st_size,'sha256':sha(test)},'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'no_inference':True})
  model=ROOT/'downloads/answers/model/qwen2.5-0.5b-instruct-q4_k_m.gguf';assert sha(model)=='74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db';push(model,'files/model.gguf')
  for p,n in [('downloads/packs/english-reference.plpack','reference'),('downloads/science/science-supplement-2026-10-01-v1.plpack','science'),('downloads/broad-reference/rendered-v2/broad-reference.plpack','broad')]:push(ROOT/p,'files/capacity-seed/'+n+'.plpack')
  push(ROOT/'tools/evaluation/full-capacity/protocol.json','files/capacity-protocol.json')
 step('seed','seed')
 # Hash immutable inventory once; installation hashes every incoming object on Android too.
 if not (OUT/'host-inventory.json').exists():
  inv=json.loads((ROOT/'docs/evidence/full-scale/host/files.json').read_text())
  for f in inv:
   p=pathlib.Path(f['path']);assert p.stat().st_size==f['bytes'] and sha(p)==f['sha256'],p
  save(OUT/'host-inventory.json',inv)
 inv=json.loads((OUT/'host-inventory.json').read_text());allman={k:json.loads((ROOT/f'docs/evidence/full-scale/{k}-all.json').read_text()) for k in ['wiki','places']}
 manifest_paths={str(LANES/('wiki/edition-v7' if k=='wiki' else 'places/data')/f['path']) for k,m in allman.items() for f in m['files']}
 # Auxiliary declared assets remain installed, but are not claimed as integrated readers.
 if not (OUT/'auxiliary.json').exists():
  rows=[]
  for f in inv:
   if f['path'] not in manifest_paths:
    p=pathlib.Path(f['path']);dest='files/capacity-aux/'+p.name;push(p,dest);actual=shell('run-as '+PKG+' sha256sum '+dest).split()[0];assert actual==f['sha256'];rows.append(dict(f,device_path=dest))
  save(OUT/'auxiliary.json',rows)
 plan=json.loads((ROOT/'docs/evidence/full-scale/sweep/plan.json').read_text())['frozen_rows']
 for kind in ['wiki','places']:
  full=allman[kind];base=LANES/('wiki/edition-v7' if kind=='wiki' else 'places/data');rows=[r for r in plan if r['kind']==kind]
  common=[f for f in full['files'] if ('/' not in f['path'] if kind=='wiki' else f['path'] not in full['shards'])]
  for i,row in enumerate(rows):
   label=f'{kind}-{i:02}'
   if (OUT/label/'result.json').exists():continue
   old=catalog().get(kind);known={f['sha256'] for f in old[1]['files']} if old else set();selected={r['shard'] for r in rows[:i+1]}
   specs=common+[f for f in full['files'] if (f['path'].split('/')[0] in selected if kind=='wiki' else f['path'] in selected)]
   m=dict(full,collection_key='sealed-'+kind,replaces=old[0] if old else '',label='Complete sealed '+kind+'; browse only',shards=sorted(selected),files=[dict(f,payload=f['sha256'] not in known) for f in specs],installed_bytes=sum(f['bytes'] for f in specs))
   for key in row['counts']:m[key]=sum(r['counts'][key] for r in rows[:i+1])
   transfer(label,m,{f['path']:base/f['path'] for f in specs})
 step('full-hashes','hash');step('full-inspection','inspect')
 step('disable','disable');shell('am force-stop '+PKG);step('restart-disabled','restart');step('enable','enable')
 # Representation-only replacement of both objects of the largest wiki shard.
 old_id,original=catalog()['wiki']
 if (SCRATCH/'original-manifest.json').exists():original=json.loads((SCRATCH/'original-manifest.json').read_text())
 replace_paths={};replacement=SCRATCH/'replacement';replacement.mkdir(exist_ok=True)
 for name in ['000_00003/catalog.sqlite','000_00003/articles.blocks']:
  p=replacement/pathlib.Path(name).name
  if not p.exists():
   shutil.copyfile(LANES/'wiki/edition-v7'/name,p)
   with p.open('r+b') as f:
    if name.endswith('sqlite'):f.seek(60);f.write((1).to_bytes(4,'big'))
    else:f.seek(0,2);f.write(b'\n')
  replace_paths[name]=p
 if not (OUT/'replacement-input/manifest.json').exists():
  m=dict(original,replaces=old_id,representation_fixture='Only SQLite user_version and unused block trailer differ; no new facts',files=[dict(f,payload=f['path'] in replace_paths,**({'sha256':sha(replace_paths[f['path']]),'bytes':replace_paths[f['path']].stat().st_size} if f['path'] in replace_paths else {})) for f in original['files']]);m['installed_bytes']=sum(f['bytes'] for f in m['files'])
  save(SCRATCH/'original-manifest.json',original)
 else:m=json.loads((OUT/'replacement-input/manifest.json').read_text())
 paths={f['path']:replace_paths.get(f['path'],LANES/'wiki/edition-v7'/f['path']) for f in m['files']}
 # Cancel the real incoming delta after more than one MiB, before catalog publication.
 transfer('cancelled-replacement',m,paths,'cancel')
 # Corruption is a bounded bad notice payload, with old collection retained.
 badfile=SCRATCH/'bad-notice';badfile.write_bytes(b'corrupted controlled fixture\n');bad=dict(m);notice=next(f for f in m['files'] if f['path'].endswith('.txt'));bad['files']=[dict(notice,payload=True)]+[dict(f,payload=False) for f in original['files'] if f['path']!=notice['path']];bad['installed_bytes']=sum(f['bytes'] for f in bad['files']);bad['representation_fixture']='Corrupt fixture; must reject'
 transfer('corrupt-replacement',bad,{notice['path']:badfile},'corrupt')
 transfer('replacement',m,paths)
 step('replacement-inspection','inspect')
 if not (OUT/'restore-input/manifest.json').exists():
  original=json.loads((SCRATCH/'original-manifest.json').read_text());current=catalog()['wiki'];known={f['sha256'] for f in current[1]['files']};restore=dict(original,replaces=current[0],files=[dict(f,payload=f['sha256'] not in known) for f in original['files']])
 else:restore=json.loads((OUT/'restore-input/manifest.json').read_text())
 transfer('restore',restore,{f['path']:LANES/'wiki/edition-v7'/f['path'] for f in restore['files']})
 shell('am force-stop '+PKG);step('restored-hashes','hash');step('restored-inspection','inspect')
 save(OUT/'complete.json',{'serial':'emulator-5562','whole_inventory_resident':True,'generation':False,'finished_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'catalog':catalog()})
if __name__=='__main__':main()
