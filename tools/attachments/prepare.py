"""Explicit rig setup only. App and build verification never download optional weights."""
import argparse,hashlib,json,tarfile,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];CACHE=ROOT/'downloads/attachments'
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--fetch',action='store_true');ap.add_argument('--models',action='store_true');a=ap.parse_args();CACHE.mkdir(exist_ok=True,parents=True)
 for name,pin in json.loads((ROOT/'tools/attachments/sources.json').read_text()).items():
  archive=CACHE/(name+'.tar.gz')
  if not archive.exists() and a.fetch:archive.write_bytes(urllib.request.urlopen(pin['url']).read())
  assert digest(archive)==pin['sha256'],'Changed source archive '+name
  destination=CACHE/name
  with tarfile.open(archive) as tar:
   if not destination.exists() and a.fetch:
    destination.mkdir()
    for m in tar.getmembers():
     m.name='/'.join(m.name.split('/')[1:])
     if m.name:tar.extract(m,destination,filter='data')
  with tarfile.open(archive) as tar:
   for m in tar.getmembers():
    if m.isfile():
     p=destination/('/'.join(m.name.split('/')[1:]));assert p.read_bytes()==tar.extractfile(m).read(),'Changed engine source '+str(p)
 if a.models:
  for name,pin in json.loads((ROOT/'tools/attachments/models.json').read_text()).items():
   path=CACHE/('models/'+pin['file'] if name=='speech' else pin['file']);path.parent.mkdir(exist_ok=True)
   if not path.exists() and a.fetch:
    with urllib.request.urlopen(pin['url']) as response,path.open('wb') as out:
     while b:=response.read(1024*1024):out.write(b)
   assert path.stat().st_size==pin['bytes'] and digest(path)==pin['sha256'],'Changed optional asset '+name
 print('Pinned engine sources verified'+('; optional weights verified' if a.models else '; weights not required for build'))
if __name__=='__main__':main()
