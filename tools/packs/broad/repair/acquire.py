#!/usr/bin/env python3
"""Bounded serial acquisition of exact rendered Wikipedia revisions; resumable immutable files."""
import urllib.request,urllib.parse,urllib.error,json,time,hashlib,sqlite3,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'downloads/broad-reference/html-v2';OUT.mkdir(parents=True,exist_ok=True)
HEAD={'User-Agent':'PocketLore/0.1 (bounded offline reference development; no media acquisition)'}
def get(url,path):
 if path.exists():return path.read_bytes()
 for attempt in range(2):
  time.sleep(3 if '/w/api.php?' in url else 0.5)
  start=time.monotonic()
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers=HEAD),timeout=30) as r:
    data=r.read(8*1024*1024+1);assert len(data)<=8*1024*1024
    entry={'url':url,'status':r.status,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'seconds':time.monotonic()-start,'file':path.name}
   path.write_bytes(data)
   with (OUT/'receipts.jsonl').open('a') as f:f.write(json.dumps(entry)+'\n')
   return data
  except Exception as e:
   with (OUT/'failures.jsonl').open('a') as f:f.write(json.dumps({'url':url,'attempt':attempt,'error':str(e),'headers':dict(e.headers) if isinstance(e,urllib.error.HTTPError) else {}})+'\n')
   if isinstance(e,urllib.error.HTTPError) and e.code==429: raise SystemExit('Rate limited; acquisition stopped, preserve partial files and respect upstream limits')
   time.sleep(1)
 raise RuntimeError(url)
if __name__=='__main__':
 con=sqlite3.connect(ROOT/'downloads/broad-reference/v1/index.sqlite')
 records=list(con.execute('select id,title,area from documents order by rowid'))
 # Batched lookup reduces the request count; saved per-document metadata stays immutable.
 for offset in range(0,len(records),50):
  batch=records[offset:offset+50];missing=[r for r in batch if not (OUT/(r[0]+'.json')).exists()]
  if missing:
   query=urllib.parse.urlencode({'action':'query','prop':'revisions','rvprop':'ids|timestamp','pageids':'|'.join(r[0] for r in missing),'format':'json'})
   meta=json.loads(get('https://en.wikipedia.org/w/api.php?'+query,OUT/('batch-'+str(offset)+'.json')))
   for page in meta['query']['pages'].values():
    path=OUT/(str(page['pageid'])+'.json')
    if not path.exists():path.write_text(json.dumps({'query':{'pages':{str(page['pageid']):page}}}))
  for ident,title,area in batch:
   try:
    meta=json.loads((OUT/(ident+'.json')).read_text());page=next(iter(meta['query']['pages'].values()));rev=page['revisions'][0]['revid']
    url='https://en.wikipedia.org/w/index.php?'+urllib.parse.urlencode({'title':page['title'],'oldid':rev})
    get(url,OUT/(ident+'.html'))
    print(ident,rev,flush=True)
   except Exception as e:print('FAILED',ident,str(e),flush=True)
