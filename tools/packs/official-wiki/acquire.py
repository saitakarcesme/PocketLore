"""Download one predeclared official shard, streaming and preserving partial failures."""
import argparse,hashlib,json,urllib.request,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('pin',type=Path);p.add_argument('out',type=Path);a=p.parse_args();pin=json.loads(a.pin.read_text());a.out.mkdir(parents=True,exist_ok=True)
f=a.out/pin['name'];receipt=a.out/(pin['name']+'.receipt.json');start=time.monotonic()
def digest(path,algorithm):
 with path.open('rb') as stream:return hashlib.file_digest(stream,algorithm).hexdigest()
if f.exists():
 assert f.stat().st_size==pin['size'] and digest(f,'sha1')==pin['sha1'];print('Verified existing shard; no duplicate download');raise SystemExit(0)
partial=f.with_suffix(f.suffix+'.partial');assert not partial.exists(),'Preserve previous partial; explicit recovery required'
r={'url':pin['url'],'pin':pin,'status':'FAILED'}
try:
 with urllib.request.urlopen(urllib.request.Request(pin['url'],headers={'User-Agent':'PocketLore/0.1 bounded offline research acquisition'}),timeout=45) as response,partial.open('xb') as stream:
  r['http_status']=response.status;r['final_url']=response.url;r['headers']=dict(response.headers);size=0
  while True:
   b=response.read(1024*1024)
   if not b:break
   size+=len(b)
   if size>pin['size']:raise ValueError('Declared shard size exceeded')
   stream.write(b)
 assert partial.stat().st_size==pin['size'] and digest(partial,'sha1')==pin['sha1'],'Official checksum mismatch'
 r.update(status='VERIFIED',bytes=partial.stat().st_size,sha256=digest(partial,'sha256'));partial.rename(f)
except Exception as e:r['error']=str(e);raise
finally:
 r['elapsed_s']=time.monotonic()-start;receipt.write_text(json.dumps(r,indent=2)+'\n')
