"""Immutable input and live-process oracles for repair1; never executes inference."""
import hashlib,json,os,pathlib,re,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[3]
SOURCES=[
 'tools/runtime/sparse/build_identity.py','tools/evaluation/native-cache/reproducibility.py','tools/evaluation/native-cache/build_receipts.py',
 'tools/runtime/sparse/binding.py','tools/runtime/sparse/derive.py','tools/runtime/sparse/prepare_native.py','tools/runtime/sparse/identity.json','tools/runtime/sparse/lazy-mmap.patch','tools/runtime/pins.env',
 'tools/runtime/sparse/native/pocketlore-owned.h','tools/runtime/sparse/native/pocketlore-sha.c','tools/runtime/sparse/native_controls.cpp','tools/runtime/sparse/host.cpp','tools/runtime/sparse/profile.h','tools/runtime/sparse/CMakeLists.txt',
 'tools/android-build.sh','tools/release/finalize_apk.py','tools/release/debug-signing.gradle','android/app/build.gradle','android/build.gradle','android/settings.gradle','android/gradle.properties','android/app/src/main/AndroidManifest.xml','android/app/src/main/cpp/resource_budget.h',
 'tools/runtime/build-native.sh','android/app/src/main/cpp/CMakeLists.txt','android/app/src/main/cpp/sparse_link.cpp','android/app/src/main/cpp/runtime.cpp',
 'tools/evaluation/native-cache/contract.py','tools/evaluation/native-cache/run.py','tools/evaluation/native-cache/check.py','tools/evaluation/native-cache/controls.py','tools/evaluation/check_native_cache_lifecycle.sh',
 'docs/evidence/native-cache-inputs/repair-2/policy.json','docs/evidence/native-cache-inputs/repair-2/tensor-layout.json']
BINARIES=['downloads/native-cache-build/host/native-cache-controls','downloads/native-cache-build/host/sparse-host','android/app/build/generated/nativeLibs/arm64-v8a/libpocketlore.so','android/app/build/generated/nativeLibs/x86_64/libpocketlore.so','android/app/build/outputs/apk/debug/app-debug.apk']
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def version(p):
 s=os.stat(p);return {'device':s.st_dev,'inode':s.st_ino,'size':s.st_size,'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns}
def identity(p,text=False):
 before=version(p);h=sha(p);after=version(p);assert before==after,'Mutated during hash'
 d={'version':before,'sha256':h}
 if text:d['text']=pathlib.Path(p).read_text()
 return d
def source_manifest():return {p:identity(ROOT/p,True) for p in SOURCES}
def source_contract(d,current=True):
 assert set(d)==set(SOURCES) and d,'Incomplete source set'
 for p,v in d.items():
  assert hashlib.sha256(v['text'].encode()).hexdigest()==v['sha256'],p
  if current:assert identity(ROOT/p)=={k:v[k] for k in ['version','sha256']},p
 return True
def process_stat(raw):
 pid=int(raw.split(' ',1)[0]);tail=raw[raw.rfind(')')+2:].split();return pid,int(tail[19])
def status_pid(raw):return int(re.search(r'^Pid:\s+(\d+)$',raw,re.M)[1])
def sample_identity(s,pid,start,ns):
 assert s['pid']==pid==status_pid(s['status'])==process_stat(s['stat'])[0],'PID disagreement'
 assert process_stat(s['stat'])[1]==start and s['namespaces']==ns,'Process lifetime disagreement'
 for field in ['VmRSS','VmHWM','VmSwap','Threads']:
  assert re.search(r'^'+field+r':\s+\d+',s['status'],re.M),field
 assert 'Pss:' in s['smaps_rollup'] and 'memory.current' in s and 'memory.events' in s
 assert int(s['memory.current'])<8053063680,'Execution aggregate stop crossed'
 assert int(re.search(r'^VmSwap:\s+(\d+)',s['status'],re.M)[1])==0,'Process swap'
 return True
def elf_machine(path):
 with open(path,'rb') as f:b=f.read(20)
 assert b[:4]==b'\x7fELF' and b[4]==2 and b[5]==1
 return int.from_bytes(b[18:20],'little')
