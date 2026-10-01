"""Acquire official license texts serially, preserving unsuccessful responses."""
import hashlib,json,pathlib,time,requests
from common import atomic_json
ROOT=pathlib.Path('/home/isa/PocketLore-control/scale-workers/places');D=ROOT/'data'/'notices';D.mkdir(exist_ok=True)
urls={'CDLA-Permissive-2.0':'https://cdla.dev/permissive-2-0/','Apache-2.0':'https://www.apache.org/licenses/LICENSE-2.0.txt','CC0-1.0':'https://creativecommons.org/publicdomain/zero/1.0/legalcode.en','CC-BY-4.0':'https://creativecommons.org/licenses/by/4.0/legalcode.en','CC-BY-SA-4.0':'https://creativecommons.org/licenses/by-sa/4.0/legalcode.en','ODbL-1.0':'https://opendatacommons.org/licenses/odbl/1-0/'}
s=requests.Session();s.headers['User-Agent']='PocketLore-source-provenance/1.0';out=[]
for name,url in urls.items():
 receipt=D/(name+'.receipt.json')
 if receipt.exists():out.append(json.loads(receipt.read_text()));continue
 r=s.get(url,timeout=(20,120));p=D/(name+'.html');p.write_bytes(r.content);record={'name':name,'url':url,'response_url':r.url,'status':r.status_code,'path':str(p),'bytes':len(r.content),'sha256':hashlib.sha256(r.content).hexdigest(),'retrieved_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'content_type':r.headers.get('Content-Type')};atomic_json(receipt,record);out.append(record)
 if r.status_code in (429,503):break
atomic_json('docs/evidence/scale/places/license-text-receipts.json',out);print(json.dumps(out,indent=2))
