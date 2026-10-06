"""Verify actual current linked artifacts and executions, freezing every raw receipt."""
import base64,copy,hashlib,json,lzma,pathlib,subprocess,time,sys,zipfile
from validate import validate,sha,R
O=R/'downloads/strong-native-host';A=R/'docs/evidence/strong-native-host-review.json'
def frozen(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'encoding':'lzma+base64','data':base64.b64encode(lzma.compress(b,preset=3)).decode()}
def command(argv):
 p=subprocess.run(argv,capture_output=True,timeout=30);return {'argv':argv,'exit':p.returncode,'stdout':p.stdout.decode(errors='replace'),'stderr':p.stderr.decode(errors='replace')}
r={'run_id':time.strftime('%Y%m%dT%H%M%SZ',time.gmtime()),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'errors':[],'commands':[],'files':[],'android_executed':False,'product_qualified':False}
try:
 for name in ['android-build','host-configure','host-build']:assert (O/(name+'.exit')).read_text().strip()=='0',name+' failed'
 source=pathlib.Path(subprocess.check_output([sys.executable,str(R/'tools/runtime/sparse/prepare.py')],text=True).strip());r['derivation']=json.loads((source.parent/'derivation.json').read_text())
 control=O/'gate-native-controls'
 for argv in [['g++','-std=c++17','-I'+str(R/'tools/runtime/sparse'),'-I'+str(R/'android/app/src/main/cpp'),'-I'+str(source/'include'),'-I'+str(source/'ggml/include'),str(R/'tools/evaluation/strong-sparse/native_controls.cpp'),'-o',str(control)],[str(control)],[sys.executable,str(R/'tools/evaluation/strong-sparse/residency_controls.py')]]:
  c=command(argv);r['commands'].append(c);assert c['exit']==0,'Constructed control failure'
 r['constructed_controls_scope']='13 native identity/budget and 15 residency mutations; not actual-model success or generation'
 readelf='/home/isa/Android/atlas-toolchain/android-ndk-r27c/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf'
 apk=R/'android/app/build/outputs/apk/debug/app-debug.apk';r['apk_sha256']=sha(apk);r['native']={}
 with zipfile.ZipFile(apk) as z:
  for abi in ['arm64-v8a','x86_64']:
   p=R/f'android/app/build/generated/nativeLibs/{abi}/libpocketlore.so';raw=p.read_bytes();assert z.read(f'lib/{abi}/libpocketlore.so')==raw
   elf=command([readelf,'-lW','-sW',str(p)]);r['commands'].append(elf);assert elf['exit']==0 and 'pocketlore_sparse_diagnostic_parameters' in elf['stdout']
   loads=[line.split() for line in elf['stdout'].splitlines() if line.strip().startswith('LOAD')];assert loads and all(int(line[-1],16)>=16384 for line in loads)
   relro=[line.split() for line in elf['stdout'].splitlines() if line.strip().startswith('GNU_RELRO')];assert relro and all((int(line[2],16)+int(line[5],16))%16384==0 for line in relro)
   r['native'][abi]={'sha256':sha(p),'bytes':len(raw)}
 r['commands'].append(command(['/home/isa/Android/atlas-toolchain/sdk/build-tools/35.0.0/zipalign','-c','-P','16','4',str(apk)]));assert r['commands'][-1]['exit']==0
 r['commands'].append(command(['ldd',str(O/'host-build/sparse-host')]));assert r['commands'][-1]['exit']==0 and 'not found' not in r['commands'][-1]['stdout']
 execution=sorted(O.glob('execution-*/receipt.json'))[-1];actual=json.loads(execution.read_text());r['execution_sha256']=sha(execution)
 # Negatives mutate real receipts; incomplete baseline remains incomplete, never fabricated positive execution.
 negatives=[]
 for label in ['wrong_model','wrong_binary','missing_cases','missing_loaded_window','wrong_process']:
  bad=copy.deepcopy(actual)
  if label=='wrong_model':bad['model']['sha256']='0'*64
  elif label=='wrong_binary':bad['binary_sha256']='0'*64
  elif label=='missing_cases':bad['cases']=[]
  elif label=='missing_loaded_window':
   for c in bad['cases']:c['samples']=[s for s in c['samples'] if s['phase']!='loaded']
  else:
   for c in bad['cases']:
    if c['samples']:c['samples'][0]['pid']=-1
  try:validate(bad);denied=False
  except Exception:denied=True
  negatives.append({'mutation':label,'rejected':denied,'discriminating_only_if_baseline_passes':True})
 r['negative_controls']=negatives
 r['measurements']=validate(actual);assert all(x['rejected'] for x in negatives)
except Exception as e:r['errors'].append(type(e).__name__+': '+str(e))
finally:
 for p in sorted(O.glob('*')):
  if p.is_file() and p.suffix in ('.json','.stdout','.stderr','.exit'):r['files'].append(frozen(p))
 for p in sorted(O.glob('execution-*/receipt.json')):r['files'].append(frozen(p))
 for folder in ['tools/runtime/sparse','tools/evaluation/strong-native-host','docs/evidence/strong-native-host-fixtures']:
  for p in sorted((R/folder).glob('*')):
   if p.is_file():r['files'].append(frozen(p))
 for p in [R/'tools/runtime/build-native.sh',R/'android/app/src/main/cpp/CMakeLists.txt',R/'android/app/src/main/cpp/sparse_link.cpp',R/'android/app/src/main/cpp/resource_budget.h']:r['files'].append(frozen(p))
 provenance=pathlib.Path('/home/isa/PocketLore-control/overnight-20261005/strong-model-identity-research')
 for n in ['identity.json','base-LICENSE','base-config.json','base-README.md','quant-README.md','gguf-tensor-layout.json']:r['files'].append(frozen(provenance/n))
 r['exit']=int(bool(r['errors']));r['classification']='HOST_LINK_AND_EXECUTION_PASS' if not r['errors'] else 'HOST_ENGINEERING_INCOMPLETE';r['open_gates']=['Android JNI/UI execution/publication and cancellation/reuse/restart','Independent explanation/comparison/synthesis entailment and useful answers','Actual aggregate device12GB and complete50GB installation/update/provider/rollback','Physical GrapheneOS/noGMS and independent unseen matched comparison']
 prior=json.loads(A.read_text()) if A.exists() else {'runs':[]};prior['runs'].append(r);A.write_text(json.dumps(prior,indent=2)+'\n')
print(json.dumps({k:r[k] for k in ['run_id','classification','errors','exit']},indent=2));sys.exit(r['exit'])
