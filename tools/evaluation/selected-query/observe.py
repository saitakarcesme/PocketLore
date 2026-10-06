import hashlib,importlib.util,json,pathlib,sqlite3,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[3]
PACKET=pathlib.Path('/home/isa/PocketLore-control/overnight-20261005/source-v3-cross-inline-prerequisites-20261006T0600Z')
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class Guard:
 def __init__(self):self.deadline=time.monotonic()+20
 def check(self,**kwargs):
  if time.monotonic()>self.deadline:raise TimeoutError('Fixture deadline')
def run(root,out):
 out.mkdir(parents=True);producer=load('producer',root/'tools/packs/selected-source/producer.py');reader=load('reader',root/'tools/packs/selected-source/read.py');d=sqlite3.connect(out/'index.sqlite');d.executescript(producer.SCHEMA);policy=json.loads((ROOT/'docs/evidence/selected-source-query/frozen-policy.json').read_text());guard=Guard()
 for i,f in enumerate(policy['fixtures']):
  raw=(PACKET/(f['id']+'.schema-corrected.original.json')).read_bytes();x=json.loads(raw);row=(i,x['identifier'],x['version']['identifier'],'frozen-authored',0,len(raw),hashlib.sha256(raw).hexdigest(),json.dumps(x['license']),x['name'],None);producer.transform(d,row,raw,guard)
 d.execute("INSERT INTO search(search) VALUES('rebuild')");d.commit();d.close();r=reader.InspectionReader(out/'index.sqlite');rows=[]
 for f in policy['fixtures']:
  for q in f['queries']:
   hits=r.search(q);rows.append({'query':q,'expected_page':f['page'],'pages':[h[1] for h in hits],'pass':any(h[1]==f['page'] for h in hits)})
 r.close();result={'source':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ['tools/packs/selected-source/producer.py','tools/packs/selected-source/read.py']},'results':rows,'all_expected_pass':all(x['pass'] for x in rows)};(out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));return 0 if result['all_expected_pass'] else 1
if __name__=='__main__':sys.exit(run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2])))
