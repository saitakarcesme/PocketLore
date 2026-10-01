from pathlib import Path
import json,zipfile,hashlib,copy,sys
R=Path(__file__).resolve().parents[3]
def build(out):
 out.mkdir(parents=True,exist_ok=True);spec=json.loads((Path(__file__).parent/'protocol.json').read_text())
 for name,p in zip(['reference','science'],spec['packs']):
  b=(R/p['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==p['sha256'];(out/(name+'.plpack')).write_bytes(b)
 with zipfile.ZipFile(out/'reference.plpack') as z:files={n:z.read(n) for n in z.namelist()}
 def write(name,data):
  with zipfile.ZipFile(out/(name+'.plpack'),'w',compression=zipfile.ZIP_DEFLATED) as z:
   for n,b in data.items():
    info=zipfile.ZipInfo(n,(2026,10,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b)
 m=json.loads(files['manifest.json']);m['id']='duplicate-reference-test-only';duplicate=dict(files);duplicate['manifest.json']=json.dumps(m).encode();write('duplicate',duplicate)
 m=json.loads(files['manifest.json']);m['warning']+=' Test-only same-name edition identity fixture.'
 same=dict(files);same['manifest.json']=json.dumps(m).encode();write('same-name',same)
 bad=dict(files);bad['passages.tsv']=bad['passages.tsv'].replace(b'water',b'woter',1);assert bad['passages.tsv']!=files['passages.tsv'];write('conflicting-id',bad)
 (out/'corrupt.plpack').write_bytes(files['passages.tsv'][:99])
 # Metadata-padding stress only: real licensed passages unchanged, no corpus expansion.
 for suffix in ['a','b']:
  m=json.loads(files['manifest.json']);m['id']='manifest-padding-'+suffix+'-test-only'
  payload=json.dumps(m,separators=(',',':')).encode()+b' '*1100000
  write('large-'+suffix,{'manifest.json':payload,'passages.tsv':files['passages.tsv']})
 return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.plpack')}
if __name__=='__main__':print(json.dumps(build(Path(sys.argv[1])),indent=2))
