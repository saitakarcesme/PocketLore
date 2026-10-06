"""Real processes/SQLite/signals; fixture state only, never live source outputs."""
import hashlib,importlib.util,json,os,pathlib,signal,sqlite3,subprocess,sys,time
from structure_controls import make_inputs,sha,ROOT
P=ROOT/'tools/packs/selected-source/producer.py'
def main(out):
 out.mkdir();stage,rank,sources=make_inputs(out);base=['--mode','engineering','--stage',str(stage),'--ranking',str(rank),'--ranking-sha256',sha(rank.read_bytes()),'--through','7','--count','7','--seconds','45','--cutoff','1791269954'];checks=[]
 # Hook only pauses at an actual committed phase receipt. Ownership and all writes are real.
 wrapper=out/'phase_entry.py';wrapper.write_text('''import importlib.util,pathlib,sys,time,json
spec=importlib.util.spec_from_file_location('p',sys.argv[1]);p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
phase=sys.argv[2];ready=pathlib.Path(sys.argv[3]);original=p.receipt
held=False
def receipt(out,state,guard,db=None):
 global held
 original(out,state,guard,db)
 if guard.phase==phase and not held:
  held=True;ready.write_text(json.dumps({'phase':phase,'pid':__import__('os').getpid()}))
  while not ready.with_suffix('.continue').exists():guard.check();time.sleep(.01)
p.receipt=receipt;sys.argv=[sys.argv[1]]+sys.argv[4:];sys.exit(p.main())
''')
 def snapshot(root):return {f.name:sha(f.read_bytes()) for f in root.iterdir() if f.is_file()}
 for phase in ['metadata','materialize','hash']:
  target=out/phase;ready=out/(phase+'.ready');command=['python3',str(wrapper),str(P),phase,str(ready)]+base+['--out',str(target)];proc=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE);deadline=time.monotonic()+8
  while not ready.exists() and proc.poll() is None and time.monotonic()<deadline:time.sleep(.01)
  assert ready.exists() and proc.poll() is None,phase
  before=snapshot(target);r=subprocess.run(['python3',str(P)]+base+['--out',str(target),'--resume'],capture_output=True,timeout=10);(out/(phase+'-competitor.stderr')).write_bytes(r.stderr);assert r.returncode!=0 and proc.poll() is None and snapshot(target)==before
  proc.send_signal(signal.SIGTERM);stdout,stderr=proc.communicate(timeout=12);(out/(phase+'.stdout')).write_bytes(stdout);(out/(phase+'.stderr')).write_bytes(stderr);state=json.loads((target/'status.json').read_text());assert proc.returncode!=0 and state['status']=='STOPPED_RETAINED' and 'SIGTERM' in state['error']
  resume=subprocess.run(['python3',str(P)]+base+['--out',str(target),'--resume'],capture_output=True,timeout=30);(out/(phase+'-resume.stdout')).write_bytes(resume.stdout);(out/(phase+'-resume.stderr')).write_bytes(resume.stderr)
  assert (resume.returncode==0)==(phase!='hash')
  checks.append({'phase':phase,'owner_pid':proc.pid,'competitor_exit':r.returncode,'owner_signal_exit':proc.returncode,'resume_exit':resume.returncode,'protected_before':before,'state_after_signal':state})
 # Two actual fresh starts, exactly one succeeds with no output replacement.
 target=out/'fresh-race';a=subprocess.Popen(['python3',str(P)]+base+['--out',str(target)],stdout=subprocess.PIPE,stderr=subprocess.PIPE);b=subprocess.Popen(['python3',str(P)]+base+['--out',str(target)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 codes=[]
 for n,proc in enumerate([a,b]):
  stdout,stderr=proc.communicate(timeout=30);codes.append(proc.returncode);(out/('race-'+str(n)+'.stdout')).write_bytes(stdout);(out/('race-'+str(n)+'.stderr')).write_bytes(stderr)
 assert sum(c==0 for c in codes)==1;checks.append({'fresh_process_exits':codes})
 # Production Guard really interrupts expensive SQLite, not a mock exception.
 spec=importlib.util.spec_from_file_location('p',P);p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
 guard=p.safety.Guard(.08,time.time()+.08,out);guard.phase='fts-finalization';d=sqlite3.connect(':memory:');d.set_progress_handler(guard.progress,100);start=time.monotonic();caught=False
 try:d.execute('WITH RECURSIVE a(x) AS (VALUES(1) UNION ALL SELECT x+1 FROM a WHERE x<100000000) SELECT sum(x) FROM a').fetchone()
 except sqlite3.OperationalError:caught=True
 finally:d.close()
 assert caught and guard.reason and time.monotonic()-start<2;checks.append({'actual_sql_timeout_seconds':time.monotonic()-start,'reason':guard.reason})
 # Hash cancellation checks between actual chunks; use already-present bounded fixture DB.
 guard=p.safety.Guard(0,time.time()-1,out);guard.phase='hash';caught=False
 try:p.file_hash(stage,guard)
 except p.safety.Stopped:caught=True
 assert caught;checks.append({'expired_hash_refused':True})
 # Detached source snapshots allow real WAL writer checkpoint; no live source mutation.
 db=sqlite3.connect(stage);db.execute('PRAGMA journal_mode=WAL');db.commit();guard=p.safety.Guard(5,time.time()+5,out)
 rows=p.headers(stage,0,7,guard);db.execute("UPDATE records SET title=title WHERE sequence=0");db.commit();wal=db.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone();db.close();assert wal==(0,0,0) and [r[0] for r in rows]==list(range(8));checks.append({'detached_wal_checkpoint':wal,'merged_sequences':[r[0] for r in rows]})
 report={'pass':True,'producer_sha256':sha(P.read_bytes()),'test_sha256':sha(pathlib.Path(__file__).read_bytes()),'checks':checks,'actual_kernel':p.safety.cgroup_limits(),'dedicated_limits_qualified':False,'constructed_fixture_counts_are_not_corpus':True};(out/'result.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main(pathlib.Path(sys.argv[1]))
