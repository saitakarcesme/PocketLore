#!/usr/bin/env python3
"""Validate the bounded redirect repair after the completed unchanged storage run."""
import importlib.util,json,pathlib,subprocess,shutil,hashlib,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('capacity_run',ROOT/'tools/evaluation/full-capacity/run.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
assert (r.OUT/'complete.json').exists(),'Do not interrupt the storage run'
record=r.OUT/'runtime-redirect-repair.json'
if not record.exists():
 original=json.loads((r.OUT/'runtime.json').read_text());changes=[]
 for name in ['ScaleLibrary.java','SharedShardUpdate.java','NativeIndex.java','ResourceStorage.java']:
  path='android/app/src/main/java/org/pocketlore/app/'+name
  old=subprocess.check_output(['git','show','a34f121:'+path],cwd=ROOT);current=(ROOT/path).read_bytes()
  assert old==current,path
  changes.append({'path':path,'sha256':hashlib.sha256(current).hexdigest(),'measured_commit':'a34f121','unchanged':True})
 artifacts={}
 for name,path in [('apk',ROOT/'android/app/build/outputs/apk/debug/app-debug.apk'),('test_apk',ROOT/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk')]:
  saved=r.SCRATCH/('redirect-repair-'+name+'.apk');shutil.copyfile(path,saved)
  subprocess.run(r.ADB+['install','-r',str(saved)],check=True)
  artifacts[name]={'path':str(saved),'bytes':saved.stat().st_size,'sha256':r.sha(saved)}
 with zipfile.ZipFile(artifacts['apk']['path']) as z:identities={name:{'bytes':z.getinfo(name).file_size,'sha256':hashlib.sha256(z.read(name)).hexdigest()} for name in z.namelist() if name.endswith('.dex') or name.endswith('.so') or name=='AndroidManifest.xml'}
 r.save(record,dict(artifacts,scope='Only alias shard filename normalization changes production behavior; storage measurements use earlier separately pinned APK with identical import code',source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),previous_apk=original['apk'],import_code_equivalence=changes,packaged_identities=identities))
r.push(ROOT/'tools/evaluation/full-capacity/redirect-regression.json','files/capacity-redirect.json')
r.step('redirect-repair','redirect')
