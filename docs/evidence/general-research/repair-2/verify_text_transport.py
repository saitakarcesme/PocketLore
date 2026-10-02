#!/usr/bin/env python3
"""Exercise a LF-normalized committed snapshot, without acquisition cache or devices."""
import pathlib,subprocess,tempfile,json,hashlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[4]
def check():
    selected=['docs/evidence/general-research/source-packet','docs/evidence/general-research/source-review.json','docs/evidence/general-research/original-artifacts.json','docs/evidence/general-research/candidate.json','tools/packs/research-primary','tools/packs/broad/repair/extract.py']
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',commit,'--',*selected],cwd=ROOT).decode().splitlines()
    with tempfile.TemporaryDirectory(prefix='pocketlore-source-transport-') as temp:
        base=pathlib.Path(temp);changed=[];bindings={}
        for name in names:
            raw=subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT)
            transported=raw.replace(b'\r\n',b'\n')
            if raw!=transported:changed.append(name)
            p=base/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(transported)
            bindings[name]=hashlib.sha256(transported).hexdigest()
        run=subprocess.run([sys.executable,'-B',str(base/'docs/evidence/general-research/source-packet/verify.py')],cwd=base,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        result={'commit':commit,'kind':'Fresh Git snapshot with textual CRLF-to-LF transport and no downloads directory','files':len(names),'lf_normalized_paths':changed,'transport_hashes':bindings,'validator_exit':run.returncode,'validator_output':run.stdout}
        print(json.dumps(result,indent=2));assert run.returncode==0,'Fresh textual transport validation failed'
if __name__=='__main__':check()
