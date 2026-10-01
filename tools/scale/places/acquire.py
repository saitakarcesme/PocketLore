"""Serial, resumable bulk acquisition; immutable completed files and hashed receipts."""
import hashlib,json,pathlib,sys,time,urllib.request,urllib.error
ROOT=pathlib.Path('/home/isa/PocketLore-control/scale-workers/places')
def fetch(url,path):
 path=pathlib.Path(path); path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists(): return
 part=path.with_suffix(path.suffix+'.partial')
 for attempt in range(5):
  try:
   offset=part.stat().st_size if part.exists() else 0
   req=urllib.request.Request(url,headers={'User-Agent':'PocketLoreResearch/1.0 (https://github.com/saitakarcesme/PocketLore)','Range':f'bytes={offset}-'} if offset else {'User-Agent':'PocketLoreResearch/1.0 (https://github.com/saitakarcesme/PocketLore)'})
   with urllib.request.urlopen(req,timeout=120) as r:
    if offset and r.status!=206: raise RuntimeError('Server refused byte resume; partial preserved')
    with part.open('ab' if offset else 'wb') as f:
     while b:=r.read(8*1024*1024): f.write(b)
   part.rename(path); break
  except Exception as e:
   with (ROOT/'acquisition-failures.jsonl').open('a') as f:f.write(json.dumps({'url':url,'attempt':attempt,'error':str(e),'time':time.time()})+'\n')
   if attempt==4: raise
   time.sleep(min(60,2**attempt*5))
 h=hashlib.file_digest(path.open('rb'),'sha256').hexdigest()
 path.with_suffix(path.suffix+'.receipt.json').write_text(json.dumps({'url':url,'bytes':path.stat().st_size,'sha256':h,'retrieved_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2))
 print(path.name,path.stat().st_size,h,flush=True)
if __name__=='__main__':
 objs=json.loads(pathlib.Path('docs/evidence/scale/places/overture-objects.json').read_text())
 for o in objs:
  fetch('https://overturemapswestus2.blob.core.windows.net/'+o['Key'],ROOT/'data'/pathlib.Path(o['Key']).name)
