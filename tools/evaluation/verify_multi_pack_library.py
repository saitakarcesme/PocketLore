#!/usr/bin/env python3
"""Real Android catalog/controller/UI behavior on public fixtures, never a presence-only check."""
from pathlib import Path
import sys,subprocess,json,hashlib,datetime,time,os,zipfile
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/evaluation/multi-pack-library'))
from make_fixtures import build

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'downloads/multi-pack-library'/datetime.datetime.now(datetime.timezone.utc).strftime('run-%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True);print(out,flush=True)
 def run(cmd,name,input=None,timeout=180):
  p=subprocess.run(list(map(str,cmd)),input=input,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout);(out/name).write_bytes(p.stdout)
  if p.returncode:raise RuntimeError(str(out/name))
  return p.stdout
 tc=Path(os.environ.get('POCKETLORE_TOOLCHAIN','/home/isa/Android/atlas-toolchain'));a=[tc/'sdk/platform-tools/adb','-s','emulator-5560'];base='files/multi-pack-tests'
 assert run(a+['shell','getprop','sys.boot_completed'],'boot.txt').strip()==b'1'
 run(a+['shell','getprop','ro.build.fingerprint'],'fingerprint.txt')
 saved=run(a+['shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf','files/knowledge.plpack'],'saved-before.txt')
 assert b'567e9bbbaab896826809ec20f81ae1c4b3f421b011931edae0989d28cfce10ea  files/knowledge.plpack' in saved,'Refuse to replace or migrate an unrelated saved pack during test'
 assert b'74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db  files/model.gguf' in saved,'Unexpected model; no model replacement authorized'
 fixtures=out/'fixtures';hashes=build(fixtures);assert hashes==build(out/'repeat-fixtures'),'Fixture build not deterministic'
 run(['bash',R/'tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',R/'tools/evaluation/multi-pack-library/source.gradle','-PpocketloreTestRunner=org.pocketlore.app.LibraryInstrumentation'],'build.log')
 artifacts={}
 for rel in ['debug/app-debug.apk','androidTest/debug/app-debug-androidTest.apk']:
  p=R/'android/app/build/outputs/apk'/rel;artifacts[p.name]={'sha256':sha(p),'bytes':p.stat().st_size};run(a+['install','-r',p],'install-'+p.name+'.txt')
 run(a+['shell','am','force-stop','org.pocketlore.app'],'stop-before.txt')
 run(a+['shell','run-as','org.pocketlore.app','mkdir','-p',base+'/archives'],'mkdir.txt')
 # Only archive catalog files whose entries are our pinned project editions. Never delete user data.
 listing=run(a+['shell','run-as','org.pocketlore.app','ls','files'],'files-before.txt').decode().split()
 if 'pack-library' in listing:
  contents=run(a+['shell','run-as','org.pocketlore.app','ls','files/pack-library'],'prior-library-files.txt').decode().split()
  if contents:
   raw=run(a+['exec-out','run-as','org.pocketlore.app','cat','files/pack-library/catalog.json'],'prior-catalog.json');catalog=json.loads(raw)
   allowed={hashes['reference.plpack'],hashes['science.plpack']}
   assert all(e['sha256'] in allowed for e in catalog['collections']),'Unrelated collection: stop rather than replace'
   for e in catalog['collections']:
    actual=run(a+['exec-out','run-as','org.pocketlore.app','cat','files/pack-library/'+e['sha256']+'.plpack'],'prior-'+e['sha256']+'.plpack');assert hashlib.sha256(actual).hexdigest()==e['sha256']
  run(a+['shell','run-as','org.pocketlore.app','mv','files/pack-library',base+'/archives/'+out.name+'-catalog'],'archive-catalog.txt')
 for p in fixtures.glob('*.plpack'):run(a+['exec-in','run-as','org.pocketlore.app','sh','-c','cat > '+base+'/'+p.name],'provision-'+p.name+'.txt',p.read_bytes())
 run(a+['shell','settings','put','global','airplane_mode_on','1'],'airplane-set.txt');run(a+['shell','svc','wifi','disable'],'wifi-disable.txt');run(a+['shell','svc','data','disable'],'data-disable.txt')
 run(a+['shell','settings','get','global','airplane_mode_on'],'airplane.txt')
 for mode in ['exercise','restart']:
  run(a+['shell','am','force-stop','org.pocketlore.app'],'stop-'+mode+'.txt')
  if mode=='restart':run(a+['shell','run-as','org.pocketlore.app','rm','-f',base+'/ready-memory'],'clear-owned-marker.txt')
  cmd=list(map(str,a+['shell','am','instrument','-w','-e','mode',mode,'org.pocketlore.app.test/org.pocketlore.app.LibraryInstrumentation']))
  with (out/(mode+'-instrumentation.txt')).open('wb') as log:
   p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT);end=time.monotonic()+360;trimmed=False
   while p.poll() is None and time.monotonic()<end:
    if mode=='restart' and not trimmed:
     marker=subprocess.run(list(map(str,a+['shell','run-as','org.pocketlore.app','test','-f',base+'/ready-memory'])),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
     if marker.returncode==0:
      run(a+['shell','am','send-trim-memory','org.pocketlore.app','RUNNING_LOW'],'platform-trim.txt');trimmed=True
    time.sleep(1)
   if p.poll() is None:p.terminate();raise RuntimeError('Instrumentation timeout; preserve '+str(out))
  raw=run(a+['exec-out','run-as','org.pocketlore.app','cat',base+'/'+mode+'.json'],mode+'.json');r=json.loads(raw)
  assert p.returncode==0 and r['status']=='PASS' and 'INSTRUMENTATION_CODE: -1' in (out/(mode+'-instrumentation.txt')).read_text(),str(out/(mode+'.json'))
  if mode=='restart':assert trimmed
 for name in ['science-dialog','reference-dialog','reload-dialog','collections-dialog']:run(a+['exec-out','run-as','org.pocketlore.app','cat',base+'/'+name+'.png'],name+'.png')
 after=run(a+['shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf','files/knowledge.plpack'],'saved-after.txt');assert saved==after
 catalog=json.loads(run(a+['exec-out','run-as','org.pocketlore.app','cat','files/pack-library/catalog.json'],'final-catalog.json'));assert len(catalog['collections'])==2 and all(e['active'] for e in catalog['collections'])
 exercise=json.loads((out/'exercise.json').read_text());restart=json.loads((out/'restart.json').read_text());assert exercise['pid']!=restart['pid']
 assert len(exercise['rejections'])==5 and len(exercise['tests'])==9
 assert exercise['index_counts'][0]==210
 assert exercise['selection_before_restart']==restart['restart_status']
 assert all('Search these collections' in d['collection_controls'] for d in [exercise,restart])
 assert exercise['science-dialog']['hits'][0]['id']==restart['reload-dialog']['hits'][0]['id']
 for key in ['science-dialog','reference-dialog']:
  assert exercise[key]['route']!='GENERATED','This fixture unloads model; do not claim inference'
 # Independently compare every displayed/search source with its original immutable edition.
 expected={}
 for name in ['reference','science']:
  with zipfile.ZipFile(fixtures/(name+'.plpack')) as z:
   manifest=json.loads(z.read('manifest.json'));rows={r.split('\t')[0]:r.split('\t') for r in z.read('passages.tsv').decode().splitlines()}
   for d in manifest['documents']:
    for passage in d['passages']:
     expected['p'+hashes[name+'.plpack']+'_'+passage['id']]=(rows[passage['id']],d['raw_sha256'],hashes[name+'.plpack'])
 for hits in [exercise['cross_pack'],exercise['science-dialog']['hits'],exercise['reference-dialog']['hits'],restart['reload-dialog']['hits']]:
  for h in hits:
   row,source_hash,edition=expected[h['id']]
   assert [h['url'],h['date'],h['rights'],h['text']]==row[2:6]
   assert source_hash in h['provenance'] and edition in h['provenance'] and row[0] in h['provenance']
 sources={str(p.relative_to(R)):sha(p) for p in (R/'android/app/src/main/java/org/pocketlore/app').glob('*.java')}
 report={'status':'PASS','classification':'Actual x86_64 emulator catalog/retrieval/UI/trim behavior; not generated support, OS OOM or phone acceptance','artifacts':artifacts,'fixtures':hashes,'protocol_sha256':sha(R/'tools/evaluation/multi-pack-library/protocol.json'),'source_sha256':sources,'records':{p.name:sha(p) for p in out.iterdir() if p.is_file()},'collections':2,'distinct_active_documents':18,'active_passages':210}
 (out/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
