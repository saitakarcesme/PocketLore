#!/usr/bin/env python3
"""Exact release-v5 development freeze: three real editions, fresh JNI links and rollback."""
import argparse,copy,hashlib,importlib.util,json,shutil,subprocess,tempfile,zipfile,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=ROOT/'docs/evidence/release-v5';M=E/'manifest.json'
spec=importlib.util.spec_from_file_location('legacy_release',ROOT/'tools/release/verify.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
sha=old.sha;run=old.run
NAMES=['summary.json','fresh.json','combined.json','disabled.json','enabled.json','rollback.json','model-ui/result.json','reference-ui/result.json','science-ui/result.json','broad-ui/result.json']
def read(path):return {n:json.loads((path/n).read_text()) for n in NAMES}
def behavior(d):
 s=d['summary.json'];p=json.loads((ROOT/'tools/release/broad/protocol.json').read_text());e=p['expected'];assert s['schema']==3 and s['status']=='PASS' and s['fresh_empty'] and s['distinct_processes']
 assert s['protocol_sha256']==sha(ROOT/'tools/release/broad/protocol.json') and s['radio']=={'airplane_mode_on':'1','wifi_on':'0','mobile_data':'0'}
 assert [s['final_collections'],s['final_documents'],s['final_passages']]==[3,1113,40891]
 assert {x['sha256'] for x in s['catalog']['collections']}=={e[x+'_sha256'] for x in ('reference','science','broad')} and all(x['active'] for x in s['catalog']['collections'])
 assert s['saved_model_sha256']==e['model_sha256'] and d['fresh.json']['empty_model_and_catalog']
 assert len({d[x+'.json']['pid'] for x in ('fresh','combined','disabled','enabled')})==4
 assert d['disabled.json']['disabled_persisted'] and d['combined.json']['passages']==210 and d['enabled.json']['passages']==40891
 for mode in ('combined','enabled'):
  r=d[mode+'.json'];assert r['status']=='PASS';a=r['answer'];nav=r['generated_navigation'];assert a['question']==p['questions'][0] and a['route']=='GENERATED' and a['tokens']>0 and a['raw'] and a['prompt']
  assert nav['span_count']>0 and nav['citation'] in a['text'] and nav['citation'] in nav['visible'] and 'hands-free' in nav['visible']
  assert a['first_token_ms']>0 and a['total_ms']>=a['first_token_ms'] and r['opening_pss_kib']>0 and r['end_pss_kib']>0
  assert r['broad_license_visible'] and any(x['citation'].startswith('p'+e['broad_sha256']) for x in r['dialogs'])
  for x in r['dialogs']:assert x['citation'] in x['visible'] and 'Rights:' in x['visible'] and not x['invoked']
 for label in ('reference','science','broad'):
  r=d[label+'-ui/result.json'];assert r['status']=='PASS' and r['method']=='real DocumentsUI local SAF import' and r['pack_sha256']==e[label+'_sha256']
 assert d['model-ui/result.json']['model_sha256']==e['model_sha256']
 r=d['rollback.json'];assert r['status']=='PASS' and r['model_sha256']==e['model_sha256'] and r['sampled_staging_peak_bytes']>0
 assert {x['case']:x['rejected'] for x in r['checks']}=={'corrupt':True,'cancel-before':True,'cancel-during':True,'duplicate-retry':False}
 assert r['installed_files_after_bytes']+r['cache_bytes']+r['sampled_staging_peak_bytes']+s['artifacts']['android/app/build/outputs/apk/debug/app-debug.apk']['bytes']<50_000_000_000
 return s

def main():
 p=argparse.ArgumentParser();p.add_argument('--freeze',type=Path);a=p.parse_args();apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk';tc=Path('/home/isa/Android/atlas-toolchain')
 if a.freeze:
  d=read(a.freeze);s=behavior(d);assert not M.exists(),'Never overwrite a release freeze';assert sha(apk)==s['artifacts'][str(apk.relative_to(ROOT))]['sha256'];E.mkdir(parents=True,exist_ok=True)
  for f in a.freeze.rglob('*'):
   if f.is_file() and f.suffix in ('.json','.txt','.xml','.png','.log'):
    dest=E/f.relative_to(a.freeze);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest)
  files=run(['git','ls-files','android','tools/runtime','tools/answers','tools/packs','tools/android-build.sh','tools/release','tools/distribution','tools/verify-release.sh']).splitlines()
  manifest={'schema':3,'candidate':'Current development debug; no full-scale/model/phone acceptance','artifacts':s['artifacts'],'apk_entries':old.entries(apk),'source_files':{n:sha(ROOT/n) for n in files if (ROOT/n).is_file()},'distribution_inventory_sha256':sha(ROOT/'docs/distribution-inventory.json'),'evidence':{str(f.relative_to(E)):sha(f) for f in E.rglob('*') if f.is_file()},'signer':run([tc/'sdk/build-tools/35.0.0/apksigner','verify','--print-certs',apk])};M.write_text(json.dumps(manifest,indent=2)+'\n')
 print(run(['python3','tools/release/check_reproducibility.py']))
 m=json.loads(M.read_text())
 for n,s in m['artifacts'].items():assert (ROOT/n).stat().st_size==s['bytes'] and sha(ROOT/n)==s['sha256'],n
 for n,h in m['source_files'].items():assert sha(ROOT/n)==h,n
 for n,h in m['evidence'].items():assert sha(E/n)==h,n
 assert old.entries(apk)==m['apk_entries'] and sha(ROOT/'docs/distribution-inventory.json')==m['distribution_inventory_sha256']
 assert run([tc/'sdk/build-tools/35.0.0/apksigner','verify','--print-certs',apk])==m['signer']
 assert 'uses-permission:' not in run([tc/'sdk/build-tools/35.0.0/aapt','dump','permissions',apk])
 assert 'No dependencies' in run(['bash','tools/android-build.sh',':app:dependencies','--configuration','debugRuntimeClasspath'])
 d=read(E);behavior(d)
 for field in ('fresh','navigation','model','rollback','license','selection'):
  damaged=copy.deepcopy(d)
  if field=='fresh':damaged['fresh.json']['empty_model_and_catalog']=False
  elif field=='navigation':damaged['enabled.json']['generated_navigation']['span_count']=0
  elif field=='model':damaged['summary.json']['saved_model_sha256']='0'*64
  elif field=='rollback':damaged['rollback.json']['checks'][0]['rejected']=False
  elif field=='license':damaged['enabled.json']['broad_license_visible']=''
  else:damaged['disabled.json']['disabled_persisted']=False
  try:behavior(damaged)
  except AssertionError:pass
  else:raise AssertionError('Damaged evidence accepted: '+field)
 with tempfile.TemporaryDirectory() as temp:
  for n in ('enabled.json','rollback.json'):
   f=Path(temp)/n;shutil.copyfile(E/n,f);h=sha(f)
   with f.open('r+b') as stream:v=stream.read(1);stream.seek(0);stream.write(bytes([v[0]^1]))
   assert sha(f)!=h;f.unlink();assert not f.exists()
 pack=old.module('release_pack','tools/packs/build_pack.py')
 with tempfile.TemporaryDirectory() as folder:
  a,_=pack.build(output=Path(folder)/'a.plpack');b,_=pack.build(output=Path(folder)/'b.plpack');assert a.read_bytes()==b.read_bytes()==(ROOT/'downloads/packs/english-reference.plpack').read_bytes()
 sys.path.insert(0,str(ROOT/'tools/packs'));science=old.module('release_science','tools/packs/build_science.py')
 with tempfile.TemporaryDirectory() as folder:
  a,_=science.build(output=Path(folder)/'a.plpack');b,_=science.build(output=Path(folder)/'b.plpack');assert a.read_bytes()==b.read_bytes()==(ROOT/'downloads/science/science-supplement-2026-10-01-v1.plpack').read_bytes()
 inventory=json.loads((ROOT/'docs/distribution-inventory.json').read_text());assert {r['abi'] for r in inventory['index_native']}=={'arm64-v8a','x86_64'}
 for r in inventory['index_native']:
  assert any(x['artifact']['path'].endswith('sqlite3.c.o') for x in r['inputs']) and any(x['artifact']['path'].endswith('index.cpp.o') for x in r['inputs'])
  assert old.entries(apk)['lib/'+r['abi']+'/libpocketlore_index.so']['sha256']==r['library']['sha256']
 print(run(['bash','tools/android-check.sh']))
 print(run(['bash','tools/evaluation/check_distribution_inventory.sh']))
 print('PASS: release-v5 exact current identities, fresh three-edition offline imports, real generated citation navigation, rollback, measured resource receipts and negative regressions. Full-scale/chosen-model, physical, signing, independent reproduction and human gates OPEN.')
if __name__=='__main__':main()
