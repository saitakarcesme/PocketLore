"""Named, length-delimited derivation identities; no mutable source reuse."""
import hashlib,json,pathlib,subprocess
NAMES=['tools/runtime/sparse/reuse_controls.cpp','tools/runtime/sparse/fault_controls.cpp','tools/runtime/sparse/scalar.h','tools/runtime/sparse/host.cpp','tools/runtime/sparse/profile.h','tools/runtime/sparse/build_identity.py','tools/runtime/sparse/CMakeLists.txt','tools/runtime/build-native.sh','android/app/src/main/cpp/CMakeLists.txt','tools/runtime/sparse/prepare_native.py','tools/runtime/sparse/derive.py','tools/runtime/sparse/binding.py','tools/runtime/sparse/identity.json','tools/runtime/sparse/lazy-mmap.patch','tools/runtime/pins.env','tools/runtime/sparse/native/pocketlore-owned.h','tools/runtime/sparse/native/pocketlore-sha.c']
def canonical_key(inputs):
 h=hashlib.sha256()
 for name,value in sorted(inputs.items()):
  for v in [name,json.dumps(value,sort_keys=True,separators=(',',':'))]:
   b=v.encode();h.update(len(b).to_bytes(8,'big'));h.update(b)
 return h.hexdigest()
def derivation_inputs(root):
 data={}
 for name in NAMES:
  b=(root/name).read_bytes();data[name]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
 src=root/'downloads/runtime/llama.cpp';pin=json.loads((root/'tools/runtime/sparse/identity.json').read_text())['base_revision']
 actual=subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD'],timeout=10).decode().strip()
 assert actual==pin and not subprocess.check_output(['git','-C',str(src),'status','--porcelain','--untracked-files=all'],timeout=10)
 data['pinned_git_commit']={'revision':actual}
 return data

def validate_cache(out,inputs):
 m=json.loads((out/'native-manifest.json').read_text());assert m['input_sha256']==canonical_key(inputs) and m['inputs']==inputs
 files=m['files'];source=out/'source'
 assert files and set(files)=={str(p.relative_to(source)) for p in source.rglob('*') if p.is_file()}
 for p,h in files.items():
  assert not pathlib.PurePath(p).is_absolute() and '..' not in pathlib.PurePath(p).parts
  assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
 return m
