"""Finite same-input storage comparison, no old producer scale-credit transfer."""
import hashlib,json,pathlib,sqlite3,sys,time,resource
from observe import load,Guard
ROOT=pathlib.Path(__file__).resolve().parents[3]
def main(inputs,out):
 out.mkdir(parents=True);old=ROOT/'downloads/selected-source-query/before-code/tools/packs/selected-source/producer.py';assert hashlib.sha256(old.read_bytes()).hexdigest()=='feff9992ea969f53ff9df35d8df668bf40e52d8655f8f9a8ded6444a3bbf928e';p=load('baseline_producer',old);d=sqlite3.connect(out/'index.sqlite');d.executescript(p.SCHEMA);guard=Guard();identities={};started=time.time()
 for seq,path in enumerate(sorted(inputs.glob('*.json'))):
  raw=path.read_bytes();x=json.loads(raw);digest=hashlib.sha256(raw).hexdigest();identities[path.name]=digest;row=(seq,x['identifier'],x['version']['identifier'],'same-frozen-input',seq,len(raw),digest,json.dumps(x['license']),x['name'],None);p.transform(d,row,raw,guard)
 d.execute("INSERT INTO search(search) VALUES('rebuild')");d.execute("INSERT INTO search(search) VALUES('integrity-check')");d.commit();components=dict(d.execute('SELECT name,sum(pgsize) FROM dbstat GROUP BY name'));d.close();index=out/'index.sqlite';result={'producer_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'input_hashes':identities,'index_bytes':index.stat().st_size,'index_sha256':hashlib.sha256(index.read_bytes()).hexdigest(),'components':components,'elapsed_seconds':time.time()-started,'maxrss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'scope':'Finite authored/genuine same-input engineering comparison; not full-profile storage projection'};(out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
