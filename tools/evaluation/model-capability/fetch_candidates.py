#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,urllib.request
R=Path(__file__).resolve().parents[3];F=Path(__file__).resolve().parent
out=R/'downloads/model-capability/models';out.mkdir(parents=True,exist_ok=True)
for name in ['qwen3-4b','phi35-mini']:
 pin=json.loads((F/(name+'.json')).read_text());path=out/pin['filename']
 if not path.exists():
  assert pin['bytes']<=4*1024**3
  temp=path.with_suffix('.partial')
  with urllib.request.urlopen(pin['source_url'],timeout=60) as src,temp.open('wb') as dst:
   while data:=src.read(8*1024**2):dst.write(data)
  assert temp.stat().st_size==pin['bytes']
  with temp.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==pin['sha256']
  temp.rename(path)
 with path.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==pin['sha256']
 print(name,pin['sha256'],path.stat().st_size,flush=True)
