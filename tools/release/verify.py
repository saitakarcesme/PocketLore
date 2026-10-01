#!/usr/bin/env python3
"""Exact versioned multi-pack candidate, existing build/audit checks and actual fresh-demo receipts."""
import argparse,copy,hashlib,importlib.util,json,os,subprocess,tempfile,zipfile,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];EVIDENCE=ROOT/'docs/evidence/release-v4';MANIFEST=EVIDENCE/'manifest.json'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def run(args):
 p=subprocess.run(list(map(str,args)),cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 if p.returncode:raise RuntimeError(p.stdout.decode(errors='replace'))
 return p.stdout.decode()
def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def entries(apk):
 with zipfile.ZipFile(apk) as z:return {n:{'bytes':len(z.read(n)),'sha256':hashlib.sha256(z.read(n)).hexdigest()} for n in sorted(z.namelist()) if not n.endswith('/')}
def read_demo(path):
 names=['summary.json','fresh.json','combined.json','disabled.json','enabled.json','model-ui/result.json','reference-ui/result.json','science-ui/result.json']
 return {n:json.loads((path/n).read_text()) for n in names}
def check_demo(d):
 s=d['summary.json'];assert s['schema']==2 and s['status']=='PASS' and 'x86_64 emulator' in s['environment']
 assert s['fresh_empty'] and s['distinct_processes'] and s['radio']=={'airplane_mode_on':'1','wifi_on':'0','mobile_data':'0'}
 assert [s['final_collections'],s['final_documents'],s['final_passages']]==[2,18,210]
 p=json.loads((ROOT/'tools/release/multi-pack/protocol.json').read_text());expected=p['expected'];assert s['protocol_sha256']==sha(ROOT/'tools/release/multi-pack/protocol.json')
 assert s['saved_model_sha256']==expected['model_sha256']
 assert {e['sha256'] for e in s['catalog']['collections']}=={expected['reference_sha256'],expected['science_sha256']} and all(e['active'] for e in s['catalog']['collections'])
 modes=['fresh','combined','disabled','enabled'];assert len({d[m+'.json']['pid'] for m in modes})==4
 for m in modes:assert d[m+'.json']['status']=='PASS' and d[m+'.json']['mode']==m
 assert d['fresh.json']['empty_model_and_catalog'] and d['disabled.json']['disabled_persisted']
 assert d['combined.json']['passages']==186 and d['disabled.json']['passages']==210 and d['enabled.json']['passages']==210
 for m in ['combined','enabled']:
  r=d[m+'.json'];a=r['answer'];assert a['question']=='What is magma?' and a['tokens']>0 and a['raw'] and a['prompt'] and a['first_token_ms']>0 and a['total_ms']>=a['first_token_ms']
  assert a['route'] in ['GENERATED','FALLBACK','ABSTAINED'] # No quality inference from successful JNI execution.
  assert r['saved_model_bytes']==491400032 and len(r['dialogs'])>=2
  editions=set()
  for x in r['dialogs']:
   assert not x['invoked'] and x['citation'] in x['visible'];h=x['citation'].split('_')[0][1:];editions.add(h)
   assert h in x['visible'] and 'Source SHA-256:' in x['visible'] and 'Rights:' in x['visible']
  assert editions=={expected['reference_sha256'],expected['science_sha256']}
 model=d['model-ui/result.json'];assert model['status']=='pass' and model['model_sha256']==expected['model_sha256'] and len(model['checks'])==3
 for label in ['reference','science']:
  row=d[label+'-ui/result.json'];assert row['status']=='PASS' and row['method']=='real DocumentsUI local SAF import' and row['pack_sha256']==expected[label+'_sha256']
 return s
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--freeze',type=Path,help='Freeze one completed fresh multi-pack demonstration; never overwrite an existing candidate');args=parser.parse_args()
 tc=Path(os.environ.get('POCKETLORE_TOOLCHAIN','/home/isa/Android/atlas-toolchain'));apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk'
 if args.freeze:
  source=args.freeze.resolve();s=check_demo(read_demo(source));assert not MANIFEST.exists(),'Candidate already frozen; version explicitly'
  assert s['artifacts']['android/app/build/outputs/apk/debug/app-debug.apk']=={'bytes':apk.stat().st_size,'sha256':sha(apk)}
  EVIDENCE.mkdir(parents=True,exist_ok=True)
  # Only public fixture receipts, UI dumps and screenshots; never archive app-data tar or binaries.
  names=[]
  for f in source.rglob('*'):
   if f.is_file() and f.suffix in ['.json','.txt','.log','.png','.xml']:
    name=str(f.relative_to(source));dest=EVIDENCE/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest);names.append(name)
  files=run(['git','ls-files','android','tools/runtime','tools/answers','tools/packs','tools/android-build.sh','tools/release','tools/distribution']).splitlines()
  manifest={'schema':2,'candidate':'Development debug, not accepted or published','source_commit':run(['git','rev-parse','HEAD']).strip(),'demo_run':source.name,'artifacts':s['artifacts'],'apk_entries':entries(apk),'signer':run([tc/'sdk/build-tools/35.0.0/apksigner','verify','--print-certs',apk]),'source_files':{n:sha(ROOT/n) for n in files if (ROOT/n).is_file()},'distribution_inventory_sha256':sha(ROOT/'docs/distribution-inventory.json'),'evidence':{n:sha(EVIDENCE/n) for n in names},'limits':['same rig/toolchain only','production signing owner decision','physical Android/GrapheneOS open','human/independent research acceptance open']}
  MANIFEST.write_text(json.dumps(manifest,indent=2)+'\n')
 print(run(['python3','tools/release/check_reproducibility.py']).strip())
 m=json.loads(MANIFEST.read_text())
 for n,v in m['artifacts'].items():assert (ROOT/n).stat().st_size==v['bytes'] and sha(ROOT/n)==v['sha256'],n
 for n,h in m['source_files'].items():assert sha(ROOT/n)==h,n
 for n,h in m['evidence'].items():assert sha(EVIDENCE/n)==h,n
 assert sha(ROOT/'docs/distribution-inventory.json')==m['distribution_inventory_sha256']
 assert entries(apk)==m['apk_entries'] # All DEX, native, assets, manifest and signature entries, no ignored byte identities.
 assert run([tc/'sdk/build-tools/35.0.0/apksigner','verify','--print-certs',apk])==m['signer']
 with zipfile.ZipFile(apk) as z:
  assert any(n.startswith('classes') and n.endswith('.dex') for n in z.namelist())
  for abi in ['arm64-v8a','x86_64']:assert z.read('lib/'+abi+'/libpocketlore.so')[:4]==b'\x7fELF'
  for name in ['llama.cpp.txt','qwen2.5-Apache-2.0.txt','answer-model-notice.txt','travel-wikidata-notice.txt']:assert len(z.read('assets/licenses/'+name))>100
 assert 'uses-permission:' not in run([tc/'sdk/build-tools/35.0.0/aapt','dump','permissions',apk])
 assert 'No dependencies' in run(['bash','tools/android-build.sh',':app:dependencies','--configuration','debugRuntimeClasspath'])
 d=read_demo(EVIDENCE);s=check_demo(d);assert s['artifacts']==m['artifacts']
 for case in ['no_inference','wrong_question','restored_assets','disabled_lost','wrong_model','wrong_edition','missing_source']:
  bad=copy.deepcopy(d)
  if case=='no_inference':bad['enabled.json']['answer']['tokens']=0
  elif case=='wrong_question':bad['enabled.json']['answer']['question']='substituted'
  elif case=='restored_assets':bad['fresh.json']['empty_model_and_catalog']=False
  elif case=='disabled_lost':bad['disabled.json']['disabled_persisted']=False
  elif case=='wrong_model':bad['summary.json']['saved_model_sha256']='0'*64
  elif case=='wrong_edition':bad['science-ui/result.json']['pack_sha256']='0'*64
  else:bad['enabled.json']['dialogs']=[]
  try:check_demo(bad)
  except AssertionError:pass
  else:raise AssertionError('Damaged demo accepted: '+case)
 pack=module('release_pack','tools/packs/build_pack.py')
 with tempfile.TemporaryDirectory() as directory:
  a,_=pack.build(output=Path(directory)/'a.plpack');b,_=pack.build(output=Path(directory)/'b.plpack');assert a.read_bytes()==b.read_bytes()==(ROOT/'downloads/packs/english-reference.plpack').read_bytes()
 sys.path.insert(0,str(ROOT/'tools/packs'));science=module('release_science','tools/packs/build_science.py')
 with tempfile.TemporaryDirectory() as directory:
  a,_=science.build(output=Path(directory)/'a.plpack');b,_=science.build(output=Path(directory)/'b.plpack');assert a.read_bytes()==b.read_bytes()==(ROOT/'downloads/science/science-supplement-2026-10-01-v1.plpack').read_bytes()
 print(run(['bash','tools/android-check.sh']).strip())
 print(run(['bash','tools/evaluation/check_distribution_inventory.sh']).strip())
 print('PASS: exact full APK/DEX/native/asset/source/inventory identities, forced build reproduction, permission/dependency/notice audit, real fresh multi-pack demo replay, seven damaged-demo regressions, pack rebuild and host behavior.')
 print('No new emulator execution during replay; fresh.py creates a new destructive project-fixture-only demo. No physical, signing, clean-machine, quality or human acceptance.')
if __name__=='__main__':main()
