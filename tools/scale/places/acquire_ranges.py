"""Pin and fetch official Overture objects in bounded serial 16 MiB HTTP ranges."""
import hashlib,json,pathlib,time,requests
from acquire import ROOT
objects=json.loads(pathlib.Path('docs/evidence/scale/places/overture-objects.json').read_text())
s=requests.Session();s.trust_env=False
for obj in objects:
 path=ROOT/'data'/pathlib.Path(obj['Key']).name
 if path.exists():continue
 size=int(obj['Size']);part=path.with_suffix(path.suffix+'.partial');url='https://overturemaps-us-west-2.s3.amazonaws.com/'+obj['Key'];start=time.time()
 with part.open('ab') as f:
  offset=f.tell()
  while offset<size:
   end=min(size-1,offset+16*1024*1024-1)
   for attempt in range(3):
    try:
     r=s.get(url,headers={'Range':f'bytes={offset}-{end}','User-Agent':'PocketLoreBulkResearch/1.0'},timeout=60)
     r.raise_for_status()
     assert r.status_code==206 and r.headers['Content-Range']==f'bytes {offset}-{end}/{size}'
     assert len(r.content)==end-offset+1
     f.write(r.content);f.flush();offset=end+1
     print(path.name,offset,size,round(time.time()-start,2),flush=True);break
    except Exception as e:
     with (ROOT/'range-failures.jsonl').open('a') as log:log.write(json.dumps({'url':url,'offset':offset,'error':str(e),'attempt':attempt})+'\n')
     if attempt==2:raise
     time.sleep(10*(attempt+1))
 part.rename(path)
 receipt={'url':url,'release':'2026-09-23.1','mirror_history':['official Azure','official S3'],'listed_s3_etag':obj['ETag'],'bytes':size,'sha256':hashlib.file_digest(path.open('rb'),'sha256').hexdigest(),'retrieved_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'seconds':time.time()-start}
 path.with_suffix(path.suffix+'.receipt.json').write_text(json.dumps(receipt,indent=2));print(receipt,flush=True)
