"""Synthetic-only task535 binding and resource primitives; no model access."""
import sys,pathlib,importlib.util,json,hashlib,os
R=pathlib.Path(__file__).resolve().parents[3];O=R/'downloads/weight-fault-535'
sys.path.insert(0,str(R/'tools/evaluation/native-cache'))
from contract import identity,sha,version,process_stat,status_pid,sample_identity,SOURCES as PRIOR,BINARIES as OLD_BINARIES
spec=importlib.util.spec_from_file_location('owned_cleanup',R/'tools/evaluation/native-cache/run.py');owned=importlib.util.module_from_spec(spec);spec.loader.exec_module(owned)
BINARIES=OLD_BINARIES[:-1]+['downloads/native-cache-build/host/fault-policy-controls',OLD_BINARIES[-1]]
SOURCES=list(dict.fromkeys(PRIOR+['tools/runtime/sparse/scalar.h','tools/runtime/sparse/fault_controls.cpp']+['tools/evaluation/strong-native-host/'+n for n in ['run.py','support.py','validate.py','preflight.py','check.py','controls.py']]+['tools/evaluation/weight-fault/'+n for n in ['common.py','run.py','check.py','controls.py']]+['tools/evaluation/check_weight_fault_policy.sh','docs/evidence/weight-fault-inputs/policy.json','docs/evidence/weight-fault-inputs/api-sources.md']))
def sources():return {p:identity(R/p,True) for p in SOURCES}
def verify_sources(d):
 assert set(d)==set(SOURCES) and d
 for p,v in d.items():assert identity(R/p,True)==v,p

def preflight():
 k=owned.preflight();k['free_bytes']=os.statvfs(O).f_bavail*os.statvfs(O).f_frsize;return k

def atomic(p,data):
 raw=json.dumps(data,indent=2).encode();archive=O/'observations';archive.mkdir(exist_ok=True)
 target=archive/(hashlib.sha256(raw).hexdigest()+'.json')
 if not target.exists():target.write_bytes(raw)
 temp=p.with_name(p.name+'.tmp')
 with temp.open('wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 os.replace(temp,p)

def freeze():
 p=O/'frozen.json';assert not p.exists()
 src=pathlib.Path((O/'source-path.txt').read_text().strip())
 d={'source':sources(),'binary':{p:identity(R/p) for p in BINARIES},'source_path':str(src),'derivation':identity(src.parent/'native-manifest.json',True),'policy':json.loads((R/'docs/evidence/weight-fault-inputs/policy.json').read_text()),'kernel':preflight(),'inputs':json.loads((O/'inputs.json').read_text())}
 atomic(p,d)
