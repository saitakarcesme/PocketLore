#!/usr/bin/env python3
"""Independent byte/UTF16 oracle; no transform or production approval function."""
import base64,hashlib,html,json,sqlite3,sys,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/packs/complete-source'))
import compact as codec  # Only the declared binary codec, not the transform/mapping oracle.
def sha(b):return hashlib.sha256(b).hexdigest()
def inspect(sample):
 raw=zlib.decompress(base64.b64decode(sample['original_zlib_base64']));cap=codec.unpack_capsule(zlib.decompress(base64.b64decode(sample['capsule_zlib_base64'])))
 assert sha(raw)==sample['identity']['raw_sha256']==cap['identity']['raw_sha256']
 assert len(raw)==cap['identity']['raw_bytes'];assert cap['identity']==sample['identity']
 d=json.loads(raw);source=d['article_body']['html'];assert sha(source.encode())==cap['html_sha256']
 for key in ['identifier','name','version','license','date_modified']:assert d[key]==cap['metadata'][key]
 lic=d['license'];assert len(lic)==1
 assert (lic[0]['identifier'],lic[0]['url']) in [('CC-BY-SA-3.0','https://creativecommons.org/licenses/by-sa/3.0/'),('CC-BY-SA-4.0','https://creativecommons.org/licenses/by-sa/4.0/')]
 assert str(d['version']['identifier']) in cap['metadata']['attribution']['revision_url']
 assert 'action=history' in cap['metadata']['attribution']['history_url']
 src=source.encode('utf-16-le');txt=cap['text'].encode('utf-16-le');end=0
 assert sha(cap['text'].encode())==cap['text_sha256'] and len(src)//2==cap['html_utf16_units']
 for a,b,x,y,kind in cap['mapping']:
  assert a==end and a<b and 0<=x<=y<=len(src)//2
  original=src[2*x:2*y].decode('utf-16-le');quote=txt[2*a:2*b].decode('utf-16-le')
  if kind=='literal':assert original==quote
  elif kind=='entity':assert html.unescape(original)==quote
  elif kind=='break':assert original.lower().startswith('<br') and quote=='\n'
  else:assert kind=='separator' and x==y and quote=='\n'
  end=b
 assert end==len(txt)//2
 return {'sequence':cap['identity']['sequence'],'page':d['identifier'],'revision':d['version']['identifier'],'license':lic[0]['identifier'],'raw_sha256':sha(raw),'html_sha256':sha(source.encode()),'mapping_segments':len(cap['mapping']),'utf16_units':len(txt)//2,'source_admission_established':False}
def collect(run,destination):
 destination.mkdir(exist_ok=True,parents=True)
 now=sqlite3.connect('file:'+str(run/'resumed/index.sqlite')+'?mode=ro',uri=True)
 old=sqlite3.connect('file:'+str(ROOT/'downloads/complete-source-producer/engineering-6000-compact-v1/index.sqlite')+'?mode=ro',uri=True)
 columns='page,revision,sequence,title,license,raw_sha256,capsule_sha256'
 # Discover exact declared column names; schema is frozen, not arbitrary source SQL.
 current=now.execute('SELECT '+columns+' FROM articles ORDER BY page').fetchall();historical=old.execute('SELECT '+columns+' FROM articles ORDER BY page').fetchall()
 assert current==historical and len(current)==5944
 selected=[current[(i*(len(current)-1))//31] for i in range(32)]
 state=json.loads((run/'resumed/status.json').read_text());samples=[]
 for row in selected:
  # A fresh source read per sample cannot pin the append-only writer across transformation.
  db=sqlite3.connect('file:'+state['stage']+'?mode=ro',uri=True)
  original=db.execute('SELECT original_zlib FROM records WHERE sequence=?',(row[2],)).fetchone()[0];db.close()
  capsule=now.execute('SELECT payload FROM articles WHERE page=?',(row[0],)).fetchone()[0]
  cap=codec.unpack_capsule(zlib.decompress(capsule))
  samples.append({'identity':cap['identity'],'original_zlib_base64':base64.b64encode(original).decode(),'capsule_zlib_base64':base64.b64encode(capsule).decode(),'scope':'Actual resumed 6000-record run'})
 # Preserve independently acquired actual mixed-license originals; outside prefix counts.
 prior=json.loads((ROOT/'docs/evidence/complete-source-producer/original-samples.json').read_text())
 for sample in prior['samples']:
  raw=zlib.decompress(base64.b64decode(sample['original_zlib_base64']))
  if json.loads(raw)['license'][0]['identifier']!='CC-BY-SA-4.0':continue
  cap=codec.transform(raw,sample['identity'])
  samples.append({**sample,'capsule_zlib_base64':base64.b64encode(zlib.compress(codec.pack_capsule(cap))).decode(),'scope':'Preserved actual 4.0 original, codec reconstruction only, excluded from production article count'})
 observations=[inspect(s) for s in samples]
 (destination/'original-roundtrips.json').write_text(json.dumps({'samples':samples,'observations':observations},sort_keys=True)+'\n')
 result={'all_article_identities_and_capsule_hashes_equal_frozen_oracle':True,'article_count':len(current),'ordered_identity_sha256':sha(json.dumps(current,sort_keys=True).encode()),'sample_count':len(samples),'actual_prefix_sample_count':32,'last_sample_sequence':max(o['sequence'] for o in observations[:32]),'licenses':sorted(set(o['license'] for o in observations)),'source_admission_established':False}
 (destination/'oracle.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
 now.close();old.close()
if __name__=='__main__':collect(Path(sys.argv[1]),Path(sys.argv[2]))
