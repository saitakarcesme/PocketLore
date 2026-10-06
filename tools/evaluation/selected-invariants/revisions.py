"""Frozen independent expectations exercised against real disk-backed producer ingest."""
import hashlib, importlib.util, json, pathlib, sqlite3, sys, tempfile
ROOT=pathlib.Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('producer',ROOT/'tools/packs/selected-source/producer.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
LICENSE=json.dumps([{'identifier':'CC-BY-SA-4.0','url':'https://creativecommons.org/licenses/by-sa/4.0/'}])
def row(seq,page=7,rev=101,digest='a',error=None):return [seq,page,rev,'member.ndjson',seq*100,100,hashlib.sha256(digest.encode()).hexdigest(),LICENSE,'Public algorithm fixture',error]
def run():
 cases=json.loads((ROOT/'docs/evidence/selected-source-invariants/independent-expectations.json').read_text())['revision_cases'];results=[]
 with tempfile.TemporaryDirectory(prefix='selected-invariants-') as temp:
  for i,case in enumerate(cases):
   d=sqlite3.connect(pathlib.Path(temp)/str(i));d.executescript(p.SCHEMA)
   for seq,page,rev,digest,error in case['rows']:p.ingest(d,[row(seq,page,rev,digest,error)]);d.commit()
   actual=d.execute('SELECT revision,sequence,sha,blocked FROM latest WHERE page=7').fetchone();expect=case['expected'];ok=actual[0]==expect['revision'] and bool(actual[3])==expect['blocked']
   if 'sequence' in expect:ok &= actual[1]==expect['sequence']
   results.append({'case':case['case'],'expected':expect,'actual':actual,'pass':bool(ok),'dispositions':d.execute('SELECT sequence,outcome FROM originals ORDER BY sequence').fetchall()});d.close()
  extras=[('late lower conflict',[row(0,rev=101),row(1,rev=100,digest='b'),row(2,rev=100,digest='c')],False),('changed duplicate title',[row(0),row(1)],True)]
  extras[1][1][1][8]='Changed title'
  for label,rows,blocked in extras:
   d=sqlite3.connect(':memory:');d.executescript(p.SCHEMA)
   for r in rows:p.ingest(d,[r]);d.commit()
   actual=d.execute('SELECT blocked FROM latest WHERE page=7').fetchone()[0];results.append({'case':label,'pass':bool(actual)==blocked,'actual':actual,'expected_blocked':blocked});d.close()
  for field,value in [(1,0),(2,-1),(4,-1),(4,'bad'),(5,0),(5,'100'),(6,'z'*64),(6,'abc'),(7,'[]'),(7,LICENSE.encode()),(7,'{'),(7,LICENSE.replace('4.0/','3.0/')),(8,''),(3,'')]:
   d=sqlite3.connect(':memory:');d.executescript(p.SCHEMA);r=row(0);r[field]=value;p.ingest(d,[r]);d.commit();observed=d.execute('SELECT blocked FROM latest WHERE page=7').fetchone();outcome=d.execute('SELECT outcome FROM originals').fetchone()[0];ok=outcome=='metadata-unverified' and (observed is None or observed[0]==1);results.append({'case':'invalid field '+str(field)+' '+repr(value),'pass':ok,'actual':[observed,outcome]});d.close()
 return {'source_sha256':hashlib.sha256(pathlib.Path(p.__file__).read_bytes()).hexdigest(),'cases':results,'pass':all(r['pass'] for r in results),'factual_fixture_count':0}
if __name__=='__main__':
 result=run();print(json.dumps(result,indent=2));sys.exit(0 if result['pass'] else 1)
