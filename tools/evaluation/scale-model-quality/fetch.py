#!/usr/bin/env python3
"""Serial pinned artifact acquisition; no credentials or model execution."""
from pathlib import Path
import json,hashlib,time,urllib.request
R=Path(__file__).resolve().parents[3];F=Path(__file__).resolve().parent
for name in ['qwen25-7b','qwen15-moe']:
 p=json.loads((F/(name+'.json')).read_text());target=R/p['path'];target.parent.mkdir(parents=True,exist_ok=True)
 def sha(f):
  with f.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
 if target.exists():assert target.stat().st_size==p['bytes'] and sha(target)==p['sha256'];print('REUSE',name,flush=True);continue
 url='https://huggingface.co/'+p['repo']+'/resolve/'+p['revision']+'/'+p['filename'];partial=target.with_suffix('.partial');start=time.monotonic()
 try:
  with urllib.request.urlopen(url,timeout=120) as response,partial.open('wb') as out:
   total=0
   while data:=response.read(4*1024*1024):
    total+=len(data);assert total<=p['bytes'];out.write(data)
  assert partial.stat().st_size==p['bytes'] and sha(partial)==p['sha256'];partial.rename(target)
  receipt={'url':url,'bytes':p['bytes'],'sha256':p['sha256'],'elapsed_s':time.monotonic()-start,'status':'verified'}
 except Exception as e:
  receipt={'url':url,'status':'failed','error':str(e),'partial_bytes':partial.stat().st_size if partial.exists() else 0};raise
 finally:
  with (R/'downloads/scale-model-quality/acquisition.jsonl').open('a') as f:f.write(json.dumps(receipt)+'\n')
 print('VERIFIED',name,flush=True)
