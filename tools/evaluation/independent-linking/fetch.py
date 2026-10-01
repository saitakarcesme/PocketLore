"""Fetch only the declared CPU verifier, never remote inference; refuse changed bytes."""
from pathlib import Path
import hashlib,json,urllib.request,os
R=Path(__file__).resolve().parents[3];F=Path(__file__).parent;D=R/'downloads/independent-linking/model';D.mkdir(parents=True,exist_ok=True)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
pin=json.loads((F/'protocol.json').read_text())['verifier'];base=f"https://huggingface.co/{pin['repo']}/resolve/{pin['revision']}/"
files=[pin['file'],'tokenizer.json','tokenizer_config.json','special_tokens_map.json','config.json','README.md'];receipt={'pin':pin,'assets':{}}
for name in files:
 p=D/name;p.parent.mkdir(parents=True,exist_ok=True);url=base+name
 if not p.exists():
  tmp=p.with_suffix(p.suffix+'.partial')
  with urllib.request.urlopen(url,timeout=90) as src,tmp.open('wb') as dst:
   while b:=src.read(1024*1024):dst.write(b)
  os.replace(tmp,p)
 if name==pin['file']:assert p.stat().st_size==pin['bytes'] and sha(p)==pin['sha256']
 receipt['assets'][name]={'url':url,'sha256':sha(p),'bytes':p.stat().st_size}
license=D/'LICENSE';url='https://www.apache.org/licenses/LICENSE-2.0.txt'
if not license.exists():license.write_bytes(urllib.request.urlopen(url,timeout=30).read())
assert 'Apache License' in license.read_text() and 'Version 2.0' in license.read_text()
receipt['assets']['LICENSE']={'url':url,'sha256':sha(license),'bytes':license.stat().st_size,'basis':'Model card at immutable revision declares apache-2.0; repository has no separate LICENSE file. Canonical unmodified license text retained.'}
(D/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
