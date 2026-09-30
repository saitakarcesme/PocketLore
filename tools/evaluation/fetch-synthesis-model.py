#!/usr/bin/env python3
"""Explicit download of the pinned public synthesis model into an ignored path."""
import hashlib,json,os,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[2];pin=json.loads(Path(__file__).with_name('synthesis-model.json').read_text());out=root/'downloads/synthesis/model'/pin['filename'];out.parent.mkdir(parents=True,exist_ok=True)
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
if not out.exists():
 partial=out.with_suffix('.partial')
 with urllib.request.urlopen(pin['source_url'],timeout=120) as src,partial.open('wb') as dst:
  total=0
  while chunk:=src.read(1048576):
   total+=len(chunk)
   if total>pin['bytes']:raise ValueError('Download exceeded pinned size')
   dst.write(chunk)
 if partial.stat().st_size!=pin['bytes'] or digest(partial)!=pin['sha256']:raise ValueError('Pinned download mismatch; failed artifact preserved')
 os.replace(partial,out)
assert digest(out)==pin['sha256'] and out.stat().st_size==pin['bytes']
print(out,pin['sha256'],out.stat().st_size)
