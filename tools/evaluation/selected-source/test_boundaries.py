import hashlib,importlib.util,json,pathlib,signal,sqlite3,subprocess,sys,time,zlib
ROOT=pathlib.Path(__file__).resolve().parents[3];P=ROOT/'tools/packs/selected-source/producer.py';spec=importlib.util.spec_from_file_location('p',P);p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
def sha(b):return hashlib.sha256(b).hexdigest()
def main(out):
 out=pathlib.Path(out);out.mkdir();base=ROOT/'downloads/selected-source-production/final-controls';stage=out/'stage.sqlite';src=sqlite3.connect('file:'+str(base/'stage.sqlite')+'?mode=ro',uri=True);dst=sqlite3.connect(stage);src.backup(dst);src.close()
 # This copy is an algorithm fixture. Restore its earlier deliberately corrupted digest from retained bytes only.
 for seq,blob in dst.execute('SELECT sequence,original_zlib FROM records').fetchall():dst.execute('UPDATE records SET raw_sha256=? WHERE sequence=?',(sha(zlib.decompress(blob)),seq))
 dst.commit();dst.close();rank=base/'ranking.sqlite';command=['python3',str(P),'--mode','engineering','--stage',str(stage),'--ranking',str(rank),'--ranking-sha256',sha(rank.read_bytes()),'--through','3','--count','4','--seconds','30','--cutoff','1791269964'];results=[]
 def run(name,extra=[]):
  cmd=command+['--out',str(out/name)]+extra;start=time.time();r=subprocess.run(cmd,capture_output=True,timeout=45);(out/(name+'.stdout')).write_bytes(r.stdout);(out/(name+'.stderr')).write_bytes(r.stderr);receipt={'name':name,'command':cmd,'exit':r.returncode,'start_epoch':start,'end_epoch':time.time(),'stdout_sha256':sha(r.stdout),'stderr_sha256':sha(r.stderr)};results.append(receipt);return r.returncode
 for name in ('unknown-uri','malformed-license','oversized'):
  copy=out/(name+'-stage.sqlite');src=sqlite3.connect(stage);d=sqlite3.connect(copy);src.backup(d);src.close()
  if name=='unknown-uri':
   raw=zlib.decompress(d.execute('SELECT original_zlib FROM records WHERE sequence=0').fetchone()[0]);x=json.loads(raw);x['license'][0]['url']='https://invalid.example/license';raw=json.dumps(x,ensure_ascii=False).encode();d.execute('UPDATE records SET original_zlib=?,raw_bytes=?,raw_sha256=?,license_json=? WHERE sequence=0',(zlib.compress(raw),len(raw),sha(raw),json.dumps(x['license'])))
  elif name=='malformed-license':d.execute("UPDATE records SET license_json='{' WHERE sequence=0")
  else:d.execute('UPDATE records SET raw_bytes=16000001 WHERE sequence=0')
  d.commit();d.close();assert run(name,['--stage',str(copy)])==0;state=json.loads((out/name/'status.json').read_text());assert state['counts']['articles']==3 and state['outcomes']['retained-refusal']==1 and not state['source_admission_established']
 assert run('missing',['--stage',str(out/'absent.sqlite')])!=0;assert run('expired',['--cutoff','1'])!=0
 before=sha(stage.read_bytes());target=out/'fresh-race';cmd=command+['--out',str(target)];start=time.time();children=[subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE) for _ in range(2)];exits=[]
 for i,child in enumerate(children):
  stdout,stderr=child.communicate(timeout=45);(out/f'fresh-{i}.stdout').write_bytes(stdout);(out/f'fresh-{i}.stderr').write_bytes(stderr);exits.append(child.returncode)
 assert sorted(exits)==[0,1] and sha(stage.read_bytes())==before;state=json.loads((target/'status.json').read_text());assert state['counts']['articles']==4;results.append({'name':'two fresh processes','command':cmd,'exits':exits,'start_epoch':start,'end_epoch':time.time(),'stage_sha256_unchanged':before})
 lock=sqlite3.connect(stage);lock.execute('BEGIN EXCLUSIVE');cmd=command+['--out',str(out/'xcpu')];child=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE);deadline=time.monotonic()+5
 while child.poll() is None and time.monotonic()<deadline:
  path=out/'xcpu/status.json'
  if path.exists() and json.loads(path.read_text()).get('phase')=='metadata':break
  time.sleep(.005)
 assert child.poll() is None and json.loads(path.read_text())['phase']=='metadata';child.send_signal(signal.SIGXCPU);stdout,stderr=child.communicate(timeout=10);lock.rollback();lock.close();(out/'xcpu.stdout').write_bytes(stdout);(out/'xcpu.stderr').write_bytes(stderr);state=json.loads(path.read_text());assert child.returncode!=0 and state['status']=='STOPPED_RETAINED' and 'SIGXCPU' in state['error'];results.append({'name':'actual SIGXCPU delivery, not artificial CPU exhaustion','command':cmd,'exit':child.returncode,'state':state})
 for delta in (-1,0):
  guard=p.safety.Guard(30,1791269964,out,free=lambda _:p.safety.RESERVE+p.safety.MARGIN+delta)
  try:guard.check(write=True);assert delta==0
  except p.safety.Stopped:assert delta==-1
 report={'status':'PASS','producer_sha256':sha(P.read_bytes()),'executed_test_sha256':sha(pathlib.Path(__file__).read_bytes()),'fixture_sha256':sha((ROOT/'docs/evidence/selected-source-production/boundary-fixtures.json').read_bytes()),'runs':results,'reserve_boundary':'virtual bytes; no disk filling','fixture_source_is_not_corpus_breadth':True};(out/'boundary-controls.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main(sys.argv[1])
