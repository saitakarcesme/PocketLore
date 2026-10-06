"""Fault injection after real SQLite RELEASE in actual old/new producer processes."""
import hashlib,json,pathlib,shutil,sqlite3,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[3]
def sha(b):return hashlib.sha256(b).hexdigest()
def run(out):
 out=pathlib.Path(out);out.mkdir();stage=ROOT/'downloads/selected-source-production/boundaries-v1/stage.sqlite';rank=ROOT/'downloads/selected-source-production/final-controls/ranking.sqlite';old=out/'before/tools/packs/selected-source/producer.py';old.parent.mkdir(parents=True)
 old.write_bytes((ROOT/'downloads/selected-source-production/scale-6000-v3/executed-producer.py').read_bytes())
 for name in ('source-structure/produce.py','complete-source/production.py','complete-source/compact.py'):
  dest=out/'before/tools/packs'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/'tools/packs'/name).read_bytes())
 wrapper='''import sqlite3,os,sys,importlib.util
original=sqlite3.connect
class CrashAfterRelease(sqlite3.Connection):
 def execute(self,sql,*args,**kwargs):
  result=super().execute(sql,*args,**kwargs)
  if sql=='RELEASE article':os._exit(77)
  return result
def connect(*args,**kwargs):kwargs['factory']=CrashAfterRelease;return original(*args,**kwargs)
sqlite3.connect=connect
path=sys.argv.pop(1);spec=importlib.util.spec_from_file_location('actual_producer',path);p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p);sys.exit(p.main())
''';(out/'fault-wrapper.py').write_text(wrapper);results=[]
 for name,code in [('before',old),('after',ROOT/'tools/packs/selected-source/producer.py')]:
  target=out/(name+'-output');args=['--mode','engineering','--stage',str(stage),'--ranking',str(rank),'--ranking-sha256',sha(rank.read_bytes()),'--out',str(target),'--through','3','--count','4','--seconds','30','--cutoff','1791269964'];command=['python3',str(out/'fault-wrapper.py'),str(code),*args];r=subprocess.run(command,capture_output=True,timeout=45);(out/(name+'-invocation.json')).write_text(json.dumps({'command':command,'exit':r.returncode}));assert r.returncode==77
  (out/(name+'.stdout')).write_bytes(r.stdout);(out/(name+'.stderr')).write_bytes(r.stderr);d=sqlite3.connect(target/'index.sqlite');counts={table:d.execute('SELECT count(*) FROM '+table).fetchone()[0] for table in ('articles','receipts')};pending=d.execute("SELECT count(*) FROM selected WHERE outcome='pending'").fetchone()[0];integrity=d.execute('PRAGMA integrity_check').fetchall();d.close()
  if name=='after':assert integrity==[('ok',)]
  assert counts==({'articles':1,'receipts':0} if name=='before' else {'articles':0,'receipts':0});assert pending==4;results.append({'name':name,'command':command,'exit':r.returncode,'producer_sha256':sha(code.read_bytes()),'counts_after_actual_process_exit':counts,'pending':pending,'integrity':integrity})
  if name=='after':
   command=['python3',str(code),*args,'--resume'];r=subprocess.run(command,capture_output=True,timeout=45);(out/'resume.stdout').write_bytes(r.stdout);(out/'resume.stderr').write_bytes(r.stderr);assert r.returncode==0;state=json.loads((target/'status.json').read_text());assert state['counts']['articles']==4 and state['counts']['receipts']==4;results.append({'name':'manual resume after forced exit','command':command,'exit':r.returncode,'state':state})
 report={'status':'PASS','test_sha256':sha(pathlib.Path(__file__).read_bytes()),'fault_injection':'real producer execute wrapper exits AFTER actual RELEASE SQL; no SQLite/flock simulation','source_admission_established':False,'results':results};(out/'atomic-controls.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':run(sys.argv[1])
