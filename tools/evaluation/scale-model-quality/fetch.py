#!/usr/bin/env python3
"""Serial immutable provisioning; reuse valid files and preserve failed attempts."""
from pathlib import Path
import argparse,datetime,json,hashlib,time,urllib.request
R=Path(__file__).resolve().parents[3];F=Path(__file__).resolve().parent
pins={
 'baseline':(R/'tools/evaluation/model-capability/baseline.json','downloads/answers/model/qwen2.5-0.5b-instruct-q4_k_m.gguf'),
 'qwen3-4b':(R/'tools/evaluation/model-capability/qwen3-4b.json','downloads/model-capability/models/Qwen3-4B-Q4_K_M.gguf'),
 'qwen25-7b':(F/'qwen25-7b.json',None),
 'qwen15-moe':(F/'qwen15-moe.json',None),
}
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('models',nargs='*',metavar='MODEL',help='baseline, qwen3-4b, qwen25-7b or qwen15-moe; default all');args=parser.parse_args()
if set(args.models)-set(pins):parser.error('Unknown model: '+', '.join(sorted(set(args.models)-set(pins))))
root=R/'downloads/scale-model-quality';root.mkdir(parents=True,exist_ok=True)
def sha(path):
 with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
for name in args.models or list(pins):
 pinfile,path=pins[name];p=json.loads(pinfile.read_text());target=R/(path or p['path']);target.parent.mkdir(parents=True,exist_ok=True)
 assert len(p['revision'])==40 and p['bytes']<=6_000_000_000
 url='https://huggingface.co/'+p['repo']+'/resolve/'+p['revision']+'/'+p['filename'];start=time.monotonic();partial=None
 receipt={'model':name,'url':url,'pin_sha256':sha(pinfile),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  if target.exists():
   assert target.stat().st_size==p['bytes'] and sha(target)==p['sha256'],'Existing model is changed; preserved without overwrite'
   receipt.update(status='verified reuse',bytes=p['bytes'],sha256=p['sha256'])
  else:
   partial=target.with_suffix('.partial')
   if partial.exists():raise RuntimeError('Existing partial download preserved; inspect/archive it before an explicit retry')
   with urllib.request.urlopen(url,timeout=120) as response,partial.open('xb') as out:
    total=0
    while data:=response.read(4*1024*1024):
     total+=len(data);assert total<=p['bytes'];out.write(data)
   assert partial.stat().st_size==p['bytes'] and sha(partial)==p['sha256'];partial.rename(target)
   receipt.update(status='verified acquisition',bytes=p['bytes'],sha256=p['sha256'])
 except Exception as e:
  receipt.update(status='failed',error=str(e),partial_bytes=partial.stat().st_size if partial and partial.exists() else 0);raise
 finally:
  receipt['elapsed_s']=time.monotonic()-start
  with (root/'acquisition.jsonl').open('a') as f:f.write(json.dumps(receipt)+'\n')
 print(name,receipt['status'],p['sha256'],flush=True)
