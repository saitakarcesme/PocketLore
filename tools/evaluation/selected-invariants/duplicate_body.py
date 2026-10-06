"""A declared duplicate is not equivalent until its actual raw bytes verify."""
import json,pathlib,sqlite3,subprocess,sys,time,zlib
from structure_controls import make_inputs,ROOT,sha

def main(out):
 out.mkdir();stage,rank,source=make_inputs(out);d=sqlite3.connect(stage)
 row=list(d.execute('SELECT * FROM records WHERE sequence=0').fetchone());row[0]=8;row[2]+=1;row[-1]=zlib.compress(b'corrupt duplicate');d.execute('INSERT INTO records VALUES(?,?,?,?,?,?,?,?,?,?,?)',row);d.commit();d.close()
 p=ROOT/'tools/packs/selected-source/producer.py';command=['python3',str(p),'--mode','engineering','--stage',str(stage),'--ranking',str(rank),'--ranking-sha256',sha(rank.read_bytes()),'--through','8','--count','7','--seconds','45','--cutoff','1791269954','--out',str(out/'candidate')];start=time.time();r=subprocess.run(command,capture_output=True,timeout=55);(out/'stdout').write_bytes(r.stdout);(out/'stderr').write_bytes(r.stderr);assert r.returncode==0,r.stderr.decode()
 state=json.loads((out/'candidate/status.json').read_text());d=sqlite3.connect(out/'candidate/index.sqlite');assert d.execute('SELECT count(*) FROM articles').fetchone()==(6,);assert d.execute('SELECT outcome FROM originals WHERE sequence=8').fetchone()==('duplicate-revision',);outcome,detail=d.execute('SELECT outcome,detail FROM receipts WHERE sequence=0').fetchone();assert outcome=='retained-refusal' and 'inflate/digest' in detail;assert d.execute('SELECT count(*) FROM originals').fetchone()==(9,);d.close()
 report={'pass':True,'argv':command,'start':start,'end':time.time(),'exit':r.returncode,'producer_sha256':sha(p.read_bytes()),'expected_articles':6,'actual_counts':state['counts'],'duplicate_disposition':'duplicate-revision','materialization_refusal':json.loads(detail),'fixture_only':True};(out/'result.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main(pathlib.Path(sys.argv[1]))
