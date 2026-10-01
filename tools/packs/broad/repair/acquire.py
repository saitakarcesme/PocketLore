#!/usr/bin/env python3
"""Bounded serial acquisition of exact rendered Wikipedia revisions; resumable immutable files."""
import urllib.request,urllib.parse,json,time,hashlib,sqlite3,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'downloads/broad-reference/html-v2';OUT.mkdir(parents=True,exist_ok=True)
HEAD={'User-Agent':'PocketLore/0.1 (bounded offline reference development; no media acquisition)'}
def get(url,path):
 if path.exists():return path.read_bytes()
 for attempt in range(2):
  start=time.monotonic()
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers=HEAD),timeout=30) as r:
    data=r.read(8*1024*1024+1);assert len(data)<=8*1024*1024
    entry={'url':url,'status':r.status,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'seconds':time.monotonic()-start,'file':path.name}
   path.write_bytes(data)
   with (OUT/'receipts.jsonl').open('a') as f:f.write(json.dumps(entry)+'\n')
   return data
  except Exception as e:
   with (OUT/'failures.jsonl').open('a') as f:f.write(json.dumps({'url':url,'attempt':attempt,'error':str(e)})+'\n')
   time.sleep(1)
 raise RuntimeError(url)
if __name__=='__main__':
 con=sqlite3.connect(ROOT/'downloads/broad-reference/v1/index.sqlite')
 for i,(ident,title,area) in enumerate(con.execute('select id,title,area from documents order by rowid')):
  try:
   query=urllib.parse.urlencode({'action':'query','prop':'revisions','rvprop':'ids|timestamp','titles':title,'format':'json'})
   meta=json.loads(get('https://en.wikipedia.org/w/api.php?'+query,OUT/(ident+'.json')))
   page=next(iter(meta['query']['pages'].values()));rev=page['revisions'][0]['revid']
   url='https://en.wikipedia.org/w/index.php?'+urllib.parse.urlencode({'title':page['title'],'oldid':rev})
   get(url,OUT/(ident+'.html'))
   print(i+1,ident,rev,flush=True)
  except Exception as e:print('FAILED',ident,str(e),flush=True)
