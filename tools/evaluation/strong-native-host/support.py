"""Current explicit source contract; imports immutable ownership primitives."""
import sys,pathlib,importlib.util,json,os,hashlib,base64
R=pathlib.Path(__file__).resolve().parents[3];O=R/'downloads/strong-scalar-534'
sys.path.insert(0,str(R/'tools/evaluation/native-cache'))
from contract import identity,sha,version,process_stat,status_pid,sample_identity,elf_machine,SOURCES as PARENT_SOURCES,BINARIES
spec=importlib.util.spec_from_file_location('owned_runner',R/'tools/evaluation/native-cache/run.py');owned=importlib.util.module_from_spec(spec);spec.loader.exec_module(owned)
SOURCES=list(PARENT_SOURCES)
SOURCES+=['tools/runtime/sparse/scalar.h']+['tools/evaluation/strong-native-host/'+n for n in ['support.py','run.py','validate.py','check.py','controls.py','preflight.py']]+['tools/evaluation/check_strong_native_host.sh','docs/evidence/strong-scalar-inputs/route.json','docs/evidence/strong-native-host-fixtures/freeze.json','docs/evidence/strong-native-host-fixtures/probe-1.txt','docs/evidence/strong-native-host-fixtures/probe-2.txt']
SOURCES=list(dict.fromkeys(SOURCES))
POLICY=R/'docs/evidence/strong-scalar-inputs/route.json'
MODEL=owned.MODEL

def sources():return {p:identity(R/p,True) for p in SOURCES}
def source_check(d):
 assert set(d)==set(SOURCES) and d
 for p,v in d.items():assert identity(R/p,True)==v,p

def freeze():
 from preflight import capture
 k=capture();p=O/'frozen.json';assert not p.exists(),'Frozen inputs cannot be replaced'
 source=pathlib.Path((O/'source-path.txt').read_text().strip())
 d={'source':sources(),'binary':{p:identity(R/p) for p in BINARIES},'derivation':identity(source.parent/'native-manifest.json',True),'source_path':str(source),'policy':json.loads(POLICY.read_text()),'kernel':k}
 d['configuration']={str(p.relative_to(R)):identity(p,True) for p in [R/'downloads/native-cache-build/host/CMakeCache.txt']+[R/f'downloads/native-cache-build/android/{abi}/CMakeCache.txt' for abi in ['arm64-v8a','x86_64']]}
 assert d['policy']['original_freeze_sha256']==sha(R/'docs/evidence/strong-native-host-fixtures/freeze.json')
 for i,h in enumerate(d['policy']['probes'],1):assert h==sha(R/f'docs/evidence/strong-native-host-fixtures/probe-{i}.txt')
 p.write_text(json.dumps(d,indent=2));return d

def atomic(path,data):
 raw=json.dumps(data,indent=2).encode();history=O/'observations';history.mkdir(exist_ok=True)
 h=history/(hashlib.sha256(raw).hexdigest()+'.json')
 if not h.exists():h.write_bytes(raw)
 tmp=path.with_name(path.name+'.tmp')
 with tmp.open('wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 os.replace(tmp,path)

def collect_outputs(out,case):
 case['collection_errors']=[];case['raw_bytes']={};case.setdefault('raw',{})
 try:paths=[out/'stdout',out/'stderr']+list(out.glob('*.json'))
 except Exception as e:case['collection_errors'].append(repr(e));paths=[]
 for p in paths:
  if p.name in ['receipt.json','attempt.json']:continue
  try:
   if not p.exists():continue
   with p.open('rb') as f:raw=f.read(4194305)
   case['raw_bytes'][p.name]={'sha256':hashlib.sha256(raw).hexdigest(),'base64':base64.b64encode(raw).decode(),'truncated':len(raw)>4194304}
   assert len(raw)<=4194304,'Bounded observation size exceeded'
   text=raw.decode('utf-8')
   if p.name in ['stdout','stderr']:case[p.name]=text
   else:case['raw'][p.name]=text
  except Exception as e:case['collection_errors'].append(p.name+': '+repr(e))
 if case['collection_errors']:case['failure']='Incomplete raw collection'
