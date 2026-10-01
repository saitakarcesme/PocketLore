"""Duplication-only stress packs: no new factual coverage; original rights retained."""
import copy,hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'downloads/packs/english-reference.plpack'
def sha(b):return hashlib.sha256(b).hexdigest()
def content(copies):
 with zipfile.ZipFile(BASE) as z:original=json.loads(z.read('manifest.json'));rows=z.read('passages.tsv').decode().splitlines()
 m=copy.deepcopy(original);m.update(id='duplication-stress-'+str(copies),warning='TEST ONLY: duplication-only stress fixture, not a corpus or added factual coverage.',transformation='Exact licensed passage text repeated under stress-only document IDs; source provenance retained.')
 m['documents']=[];data=[]
 for i in range(copies):
  mapping={}
  for d in original['documents']:
   d=copy.deepcopy(d);old=d['id'];d['id']='stress'+str(i)+'-'+old
   for p in d['passages']:new=d['id']+'-'+p['sha256'][:16];mapping[p['id']]=new;p['id']=new
   m['documents'].append(d)
  for row in rows:
   v=row.split('\t');v[0]=mapping[v[0]];data.append('\t'.join(v))
 payload=('\n'.join(data)+'\n').encode();m['passage_count']=len(data);m['passages_sha256']=sha(payload)
 manifest=json.dumps(m,separators=(',',':'),ensure_ascii=False).encode()
 return manifest,payload,len(m['documents']),len(data)
def make(out):
 assert sha(BASE.read_bytes())=='567e9bbbaab896826809ec20f81ae1c4b3f421b011931edae0989d28cfce10ea'
 out.mkdir(parents=True,exist_ok=True);boundary=0
 for n in range(1,109):
  m,p,docs,rows=content(n)
  if len(m)>2*1024*1024 or len(m)+len(p)+226>16*1024*1024 or docs>1000 or rows>20000:break
  boundary=n
 records=[]
 for n in sorted(set([1,5,20,50,boundary,boundary+1])):
  m,p,docs,rows=content(n);path=out/('copies-'+str(n)+'.plpack')
  with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_STORED) as z:
   for name,data in [('manifest.json',m),('passages.tsv',p)]:
    entry=zipfile.ZipInfo(name,(2026,10,1,0,0,0));entry.external_attr=0o100644<<16;z.writestr(entry,data)
  records.append({'copies':n,'file':path.name,'archive_bytes':path.stat().st_size,'manifest_bytes':len(m),'payload_bytes':len(p),'documents':docs,'passages':rows,'sha256':sha(path.read_bytes()),'expected':'accept' if n<=boundary else 'reject'})
 return records
if __name__=='__main__':print(json.dumps(make(ROOT/'downloads/scale-latency/fixtures'),indent=2))
