"""Compare actual linked outputs and retain build configuration, never execute models."""
import json,pathlib,sys
from contract import ROOT,BINARIES,identity,sha,elf_machine
from run import BASE,preflight

def capture():
 result={'kernel':preflight(),'native':{p:identity(ROOT/p) for p in BINARIES[:-1]},'configuration':{}}
 for p in [ROOT/'downloads/native-cache-build/host/CMakeCache.txt']+[ROOT/f'downloads/native-cache-build/android/{abi}/CMakeCache.txt' for abi in ['arm64-v8a','x86_64']]:
  result['configuration'][str(p.relative_to(ROOT))]={'sha256':sha(p),'text':p.read_text()}
 for p in BINARIES[:-1]:assert elf_machine(ROOT/p)==(183 if 'arm64-v8a' in p else 62)
 return result
if __name__=='__main__':
 mode=sys.argv[1];result=capture()
 if mode=='first':
  path=BASE/'first-linked.json';assert not path.exists();path.write_text(json.dumps(result,indent=2))
 elif mode=='second':
  first=json.loads((BASE/'first-linked.json').read_text());assert set(first['native'])==set(result['native'])
  for p,v in first['native'].items():assert v['sha256']==result['native'][p]['sha256'],p
  metadata=json.loads((BASE/'metadata-controls.json').read_text());assert metadata['status']=='PASS_METADATA_AND_FINALIZATION_CONTROLS'
  packet={'status':'PASS','first':first,'second':result,'metadata_controls':metadata,'native_hashes':{p:v['sha256'] for p,v in result['native'].items()},'scope':'Same build paths and toolchain; recompiled loader, metadata and executable translation units after checkpoint; no cross-toolchain reproducibility claim.'}
  (BASE/'reproducibility.json').write_text(json.dumps(packet,indent=2))
 else:raise ValueError(mode)
