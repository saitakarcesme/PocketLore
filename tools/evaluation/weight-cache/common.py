import sys,pathlib,importlib.util,json,hashlib,os
R=pathlib.Path(__file__).resolve().parents[3];O=R/'downloads/weight-cache-537'
sys.path.insert(0,str(R/'tools/evaluation/native-cache'))
from contract import identity,sha,version,process_stat,status_pid,sample_identity,SOURCES as PRIOR,BINARIES as OLD
spec=importlib.util.spec_from_file_location('owned_runner',R/'tools/evaluation/native-cache/run.py');owned=importlib.util.module_from_spec(spec);spec.loader.exec_module(owned)
BINARIES=OLD+['downloads/native-cache-build/host/fault-policy-controls','downloads/native-cache-build/host/cache-reuse-controls']
SOURCES=list(dict.fromkeys(PRIOR+['tools/runtime/sparse/scalar.h','tools/runtime/sparse/fault_controls.cpp','tools/runtime/sparse/reuse_controls.cpp']+['tools/evaluation/strong-native-host/'+n for n in ['support.py','run.py','validate.py','check.py','controls.py','validator_controls.py','preflight.py']]+['tools/evaluation/weight-cache/'+n for n in ['common.py','run.py','check.py']]+['tools/evaluation/check_weight_cache_reuse.sh','docs/evidence/weight-cache-inputs/policy.json']))
def sources():return {p:identity(R/p,True) for p in SOURCES}
def source_check(s):
 assert s and set(s)==set(SOURCES)
 for p,v in s.items():assert identity(R/p,True)==v,p

def atomic(p,d):
 b=json.dumps(d,indent=2).encode();archive=O/'observations';archive.mkdir(exist_ok=True);h=archive/(hashlib.sha256(b).hexdigest()+'.json')
 if not h.exists():h.write_bytes(b)
 temp=p.with_name(p.name+'.tmp')
 with temp.open('wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 os.replace(temp,p)
def freeze():
 assert not (O/'frozen.json').exists()
 src=pathlib.Path((O/'source-path.txt').read_text().strip());k=owned.preflight()
 d={'source':sources(),'binary':{p:identity(R/p) for p in BINARIES},'derivation':identity(src.parent/'native-manifest.json',True),'source_path':str(src),'kernel':k,'policy':json.loads((R/'docs/evidence/weight-cache-inputs/policy.json').read_text())}
 atomic(O/'frozen.json',d)
