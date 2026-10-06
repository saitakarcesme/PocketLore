#!/usr/bin/env python3
"""Independent byte counts and real-process kernel lease probes; no factual corpus counts."""
import argparse,hashlib,json,os,signal,sqlite3,subprocess,sys,tempfile,time,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import production as p
from test_safety import stage,record,append
ROOT=Path(__file__).resolve().parents[4];BASE=ROOT/'downloads/complete-source-ownership';BASE.mkdir(exist_ok=True)
RUN=Path(tempfile.mkdtemp(prefix='controls-',dir=BASE));observations=[]
def wait(fn):
 end=time.monotonic()+15
 while time.monotonic()<end:
  x=fn()
  if x:return x
  time.sleep(.02)
 raise AssertionError('bounded probe wait expired')
def snap(out):return {str(x.relative_to(out)):hashlib.sha256(x.read_bytes()).hexdigest() for x in out.rglob('*') if x.is_file()}
def base(root):return [sys.executable,str(ROOT/'tools/packs/complete-source/production.py'),'--mode','short','--stage',str(root/'stage.sqlite'),'--out',str(root/'out'),'--ceiling','1','--seconds','30','--cutoff',str(p.CUTOFF)]
def execute(cmd,log):
 r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=35);log.write_bytes(r.stdout);observations.append({'command':cmd,'exit':r.returncode,'log':str(log),'sha256':hashlib.sha256(r.stdout).hexdigest()});return r
class Tests(unittest.TestCase):
 def test_batch_boundaries(self):
  rowsizes=[[8388608],[8388607,1],[8388607,2],[8388609,1],[16777216,1],[16777217,1],[0,8388608,1]]
  expected=[[0],[0,1],[0],[0],[0],[0,1],[0,1]]
  for k,(sizes,want) in enumerate(zip(rowsizes,expected)):
   root=RUN/('batch'+str(k));root.mkdir();dbpath=root/'stage.sqlite';stage(dbpath,[]);db=sqlite3.connect(dbpath)
   for i,n in enumerate(sizes):db.execute('INSERT INTO records VALUES(?,?,?,?,?,?,?,?,?,?,zeroblob(?))',(i,'test',i,n,'digest',i+1,1,'constructed','[]',None,n))
   db.commit();db.close();batch=p.read_batch(dbpath,0,len(sizes)-1,p.Guard(20,time.time()+20,root))
   self.assertEqual([x[0] for x in batch],want);actual=sum(len(x[10]) if x[10] is not None else 0 for x in batch)
   self.assertLessEqual(actual,16777216 if len(batch)==1 else 8388608)
   if sizes[0]>16777216:self.assertIsNone(batch[0][10]);self.assertIn('refused',batch[0][9])
   # Independent SQLite writer can checkpoint after early boundary return.
   db=sqlite3.connect(dbpath,timeout=.2);db.execute('BEGIN IMMEDIATE');db.execute("UPDATE records SET title='writer' WHERE sequence=0");db.commit();cp=db.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone();self.assertEqual(cp[0],0);db.close()
   observations.append({'boundary_sizes':sizes,'returned_sequences':want,'actual_compressed_bytes':actual,'checkpoint':cp})
  # Actual metadata-only disposition advances into a valid later record.
  root=RUN/'refusal-progress';root.mkdir();stage(root/'stage.sqlite',[record(page=1),record(page=2)])
  db=sqlite3.connect(root/'stage.sqlite');db.execute('UPDATE records SET original_zlib=zeroblob(16777217) WHERE sequence=0');db.commit();db.close()
  r=execute(base(root),root/'run.log');self.assertEqual(r.returncode,0)
  s=json.loads((root/'out/status.json').read_text());self.assertEqual(s['counts']['dispositions'],2);self.assertEqual(s['counts']['articles'],1);self.assertEqual(s['dispositions']['oversized_unverified'],1)
  class Stop(p.Guard):
   def check(self,write=False):raise p.Stopped('injected exceptional source read')
  with self.assertRaises(p.Stopped):p.read_batch(root/'stage.sqlite',0,1,Stop(20,time.time()+20,root))
  db=sqlite3.connect(root/'stage.sqlite',timeout=.2);self.assertEqual(db.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()[0],0);db.close()
 def test_real_ownership(self):
  for phase,termination in [('ingest',None),('wait_source',signal.SIGTERM),('index',None),('ingest',signal.SIGTERM),('ingest',signal.SIGXCPU),('hash',signal.SIGTERM)]:
   root=RUN/(phase+'-'+str(termination));root.mkdir();stage(root/'stage.sqlite',[record(page=1),record(page=2)] if phase!='wait_source' else [record(page=1)])
   (root/'acquisition.json').write_text('{}');(root/'stage-status.json').write_text('{}')
   cmd=[sys.executable,str(Path(__file__).with_name('ownership_probe.py')),'--root',str(root),'--phase',phase,'--tag','owner']
   with (root/'owner.log').open('wb') as log:
    owner=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
    try:
     wait(lambda:(root/'owner-ready.json').exists());before=snap(root/'out')
     competing=base(root)+['--resume'];r=execute(competing,root/'competing.log');self.assertNotEqual(r.returncode,0);self.assertIn(b'already active',r.stdout)
     after=snap(root/'out');self.assertEqual(before,after);self.assertIsNone(owner.poll());(root/'lease-snapshots.json').write_text(json.dumps({'before':before,'after':after,'owner_alive':owner.poll() is None},indent=2)+'\n')
     if termination:
      if phase=='wait_source':
       db=sqlite3.connect(root/'stage.sqlite');append(db,1,record(page=2));db.commit();db.close();(root/'release').write_text('release')
       wait(lambda:json.loads((root/'out/status.json').read_text()).get('committed_through')==1)
      owner.send_signal(termination)
     else:(root/'release').write_text('release')
     code=owner.wait(timeout=15);self.assertEqual(code,1 if termination else 0)
    finally:
     if owner.poll() is None:owner.kill();owner.wait()
   observations.append({'phase':phase,'signal':signal.Signals(termination).name if termination else None,'owner_exit':code,'concurrent_output_bit_identical':True,'owner_alive_after_refusal':True,'command':cmd,'output_snapshot_sha256':hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest()})
   # Independent new process obtains the real kernel lease after owner exit.
   code='import fcntl,sys; f=open(sys.argv[1],"r+"); fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB); print("released")'
   self.assertEqual(execute([sys.executable,'-c',code,str(root/'out/.producer.lock')],root/'released.log').returncode,0)
   if phase=='ingest' and termination:
    self.assertEqual(execute(base(root)+['--resume'],root/'resumed.log').returncode,0)
   elif phase in ['index','hash']:
    self.assertNotEqual(execute(base(root)+['--resume'],root/'replay.log').returncode,0)
 def test_two_fresh_starts(self):
  root=RUN/'fresh-race';root.mkdir();stage(root/'stage.sqlite',[record(page=1),record(page=2)])
  children=[];logs=[]
  try:
   for tag in ['one','two']:
    log=(root/(tag+'.log')).open('wb');logs.append(log);children.append(subprocess.Popen([sys.executable,str(Path(__file__).with_name('ownership_probe.py')),'--root',str(root),'--phase','ingest','--tag',tag,'--barrier'],stdout=log,stderr=subprocess.STDOUT))
   (root/'start').write_text('start');wait(lambda:list(root.glob('*-ready.json')));wait(lambda:any(x.poll() is not None for x in children));self.assertEqual(len(list(root.glob('*-ready.json'))),1)
   (root/'release').write_text('release');codes=[x.wait(timeout=15) for x in children];self.assertEqual(sorted(codes),[0,1]);observations.append({'two_fresh_exit_codes':codes,'owners':1})
  finally:
   for x in children:
    if x.poll() is None:x.kill();x.wait()
   for x in logs:x.close()
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
 receipt={'success':result.wasSuccessful(),'constructed_only':True,'run':str(RUN),'observations':observations,'files':{str(x.relative_to(RUN)):hashlib.sha256(x.read_bytes()).hexdigest() for x in RUN.rglob('*') if x.is_file() and x.suffix in ['.json','.log','.jsonl']}}
 (RUN/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(RUN);sys.exit(0 if result.wasSuccessful() else 1)
