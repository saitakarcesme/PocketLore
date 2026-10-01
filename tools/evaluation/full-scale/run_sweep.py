#!/usr/bin/env python3
"""Serial local FIFO sweep. Every full shard is real; residency is only rolling."""
import json,pathlib,hashlib,subprocess,time,zipfile,tarfile,datetime
ROOT=pathlib.Path(__file__).resolve().parents[3];OUT=ROOT/'downloads/full-scale/sweep';LANES=pathlib.Path('/home/isa/PocketLore-control/scale-workers');ADB=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5560']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def command(*args):return subprocess.check_output(ADB+list(args),text=True)
def catalog():
 r=subprocess.run(ADB+['shell','run-as','org.pocketlore.app','cat','files/sweep-owned/scale-library/catalog.json'],text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
 return json.loads(r.stdout)[0]['id'] if r.returncode==0 and json.loads(r.stdout) else ''
def archive_owned(label):
 if not catalog():return
 dest=OUT/(label+'-owned.tar')
 with dest.open('xb') as f:subprocess.run(ADB+['exec-out','run-as','org.pocketlore.app','tar','cf','-','files/sweep-owned'],stdout=f,check=True)
 with tarfile.open(dest) as t:
  assert all(x.name=='files/sweep-owned' or (x.name.startswith('files/sweep-owned/') and '..' not in pathlib.PurePosixPath(x.name).parts) for x in t.getmembers())
 (OUT/(label+'-archive.json')).write_text(json.dumps({'bytes':dest.stat().st_size,'sha256':sha(dest),'scope':'Only sweep-owned fixtures; primary installed collection/model untouched'},indent=2)+'\n')
 subprocess.run(ADB+['shell','run-as','org.pocketlore.app','rm','-r','files/sweep-owned'],check=True)
def execute(label,m,base):
 directory=OUT/label;directory.mkdir(exist_ok=False)
 raw=(json.dumps(m,sort_keys=True,indent=2)+'\n').encode();(directory/'manifest.json').write_bytes(raw)
 archive=OUT/'incoming.plscale'
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as z:
  z.writestr(zipfile.ZipInfo('manifest.json',(2026,10,1,0,0,0)),raw)
  for f in m['files']:
   if not f['payload']:continue
   path=base/f['path'];assert path.stat().st_size==f['bytes'] and sha(path)==f['sha256'],path
   info=zipfile.ZipInfo(f['path'],(2026,10,1,0,0,0));info.file_size=f['bytes']
   with path.open('rb') as src,z.open(info,'w',force_zip64=True) as dst:
    for b in iter(lambda:src.read(1024*1024),b''):dst.write(b)
 (directory/'transfer.json').write_text(json.dumps({'archive_bytes':archive.stat().st_size,'archive_sha256':sha(archive),'transport':'local ADB to app-owned FIFO; no Android incoming archive'},indent=2)+'\n')
 with (directory/'instrumentation.log').open('w') as log:
  proc=subprocess.Popen(ADB+['shell','am','instrument','-w','-e','label',label,'org.pocketlore.app.test/org.pocketlore.app.ShardSweepInstrumentation'],stdout=log,stderr=subprocess.STDOUT)
  for _ in range(120):
   if subprocess.run(ADB+['shell','run-as','org.pocketlore.app','test','-p','files/sweep-input'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:break
   if proc.poll() is not None:raise RuntimeError('No FIFO: '+label)
   time.sleep(.25)
  else:raise RuntimeError('FIFO readiness timeout')
  try:
   with archive.open('rb') as src:subprocess.run(ADB+['shell',"run-as org.pocketlore.app sh -c 'cat > files/sweep-input'"],stdin=src,check=True,timeout=240)
   proc.wait(timeout=120)
  except BaseException:
   # Preserve diagnostics and input; app-scoped test may require explicit recovery.
   raise
 text=(directory/'instrumentation.log').read_text();good='INSTRUMENTATION_CODE: -1' in text
 if good:
  raw=command('shell','run-as','org.pocketlore.app','cat','files/sweep-result.json');(directory/'result.json').write_text(raw);r=json.loads(raw)
  assert r['manifest']==hashlib.sha256((directory/'manifest.json').read_bytes()).hexdigest()
  if m.get('probe') and m['kind']=='wiki':assert r['source_sha256'].lower()==m['probe']['source_sha256'].lower()
 else:(directory/'failure.json').write_text(json.dumps({'status':'FAIL','label':label,'log':'instrumentation.log'})+'\n')
 (directory/'disk.txt').write_text(command('shell','df','-k','/data'))
 if good:archive.unlink()
 print(label,'PASS' if good else 'FAIL',flush=True)
 return good

def main():
 OUT.mkdir(exist_ok=True);plan=json.loads((ROOT/'docs/evidence/full-scale/sweep/plan.json').read_text());start=time.monotonic();outcomes=[]
 before=command('shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf','files/pack-library/catalog.json','files/scale-library/catalog.json');(OUT/'retained-before.txt').write_text(before)
 archive_owned('smoke')
 for kind in ['wiki','places']:
  full=json.loads((ROOT/'docs/evidence/full-scale'/ (kind+'-all.json')).read_text());base=LANES/('wiki/edition-v7' if kind=='wiki' else 'places/data');common=[f for f in full['files'] if ('/' not in f['path'] if kind=='wiki' else f['path'] not in full['shards'])]
  def manifest(row=None,payload=False):
   m=dict(full,version=2,collection_key='rolling-'+kind,replaces=catalog(),metadata_only=row is None,shards=[] if row is None else [row['shard']],label='Rolling compatibility sweep; not full installation')
   selected=common+([] if row is None else [f for f in full['files'] if (f['path'].startswith(row['shard']+'/') if kind=='wiki' else f['path']==row['shard'])])
   common_names={f['path'] for f in common};m['files']=[dict(f,payload=payload or f['path'] not in common_names) for f in selected];m['installed_bytes']=sum(f['bytes'] for f in selected)
   m.update((dict(documents=0,full_articles=0,leads=0) if kind=='wiki' else dict(source_records=0)) if row is None else row['counts'])
   if row:m['probe']=row['probe']
   return m
  assert execute(kind+'-metadata',manifest(payload=True),base)
  for i,row in enumerate(r for r in plan['frozen_rows'] if r['kind']==kind):
   label=kind+'-'+str(i).zfill(2);ok=execute(label,manifest(row),base);outcomes.append(dict(label=label,shard=row['shard'],status='PASS' if ok else 'FAIL'))
   assert execute(label+'-retire',manifest(),base),'Could not retire sweep shard'
  archive_owned(kind)
 after=command('shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf','files/pack-library/catalog.json','files/scale-library/catalog.json');(OUT/'retained-after.txt').write_text(after);assert before==after,'Saved assets changed'
 (OUT/'summary.json').write_text(json.dumps({'platform':'emulator-5560; rolling full-shard compatibility, NOT simultaneous full installation','seconds':time.monotonic()-start,'outcomes':outcomes,'all_pass':all(x['status']=='PASS' for x in outcomes),'retained_hashes_unchanged':before==after},indent=2)+'\n')
if __name__=='__main__':main()
