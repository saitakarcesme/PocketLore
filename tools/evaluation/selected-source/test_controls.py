"""Independent controls: actual subprocess ownership/signals and genuine source oracles."""
import argparse,base64,hashlib,importlib.util,json,os,pathlib,signal,sqlite3,subprocess,sys,time,zlib
ROOT=pathlib.Path(__file__).resolve().parents[3];P=ROOT/'tools/packs/selected-source/producer.py';spec=importlib.util.spec_from_file_location('p',P);p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
EXT=pathlib.Path('/home/isa/PocketLore-control/overnight-20261005/source-reader-genuine-extended-review-20261006T0403Z');OLD=pathlib.Path('/home/isa/PocketLore-control/overnight-20261005/source-reader-prerequisite-review-20261006T0323Z')
def sha(b):return hashlib.sha256(b).hexdigest()
def stop_if_not_raises(fn):
 try:fn()
 except (ValueError,AssertionError):return
 raise AssertionError('Negative was accepted')
def main(out):
 out.mkdir();checks=[];frozen=json.loads((ROOT/'docs/evidence/selected-source-production/frozen-controls.json').read_text());(out/'frozen-controls.json').write_text(json.dumps(frozen,indent=2))
 # Unit metadata fixtures have no external factual status; production functions exercised with an independent expected result.
 d=sqlite3.connect(out/'metadata.sqlite');d.executescript(p.SCHEMA)
 def row(seq,page,rev,digest='a'):return (seq,page,rev,'fixture',0,20,digest*64,'[]','Fixture',None)
 for rows in [[row(0,10,1)],[row(1,10,3)],[row(2,10,2),row(3,20,1),row(4,20,1),row(5,30,1),row(6,30,1,'b')]]:p.ingest(d,rows);d.commit()
 assert d.execute('select revision from latest where page=10').fetchone()==(3,);assert d.execute('select blocked from latest where page=30').fetchone()==(1,);assert d.execute("select count(*) from originals where outcome='duplicate-revision'").fetchone()==(1,);checks+=['separate-batch latest does not regress','same revision conflict blocks','duplicate is one page']
 d.executescript('CREATE TABLE priority(id INTEGER PRIMARY KEY,views INTEGER,full INTEGER);INSERT INTO priority VALUES(30,5,1),(10,5,1),(20,7,1);');assert [r[0] for r in d.execute('SELECT id FROM priority ORDER BY views DESC,id')]==[20,10,30];checks.append('fixed importance ties');d.close()
 # Frozen genuine extended fragments are independently hashed, then required to survive the actual enriched tree.
 examples=[]
 for packet in [OLD,EXT]:
  for name,item in json.loads((packet/'manifest.json').read_text()).items():
   if isinstance(item,dict) and 'sha256' in item:assert sha((packet/name).read_bytes())==item['sha256']
 for entry in json.loads((EXT/'oracles.json').read_text())['records']:
  seq=entry['sequence'];raw=(EXT/f'original-{seq}.json').read_bytes();page,rev,html,nodes,meta=p.structure.inspect(raw);h16=html.encode('utf-16-le');fragments=[]
  def walk(x):
   if isinstance(x,dict):
    if 'original_start16' in x and 'original_end16' in x:
     a,b=x['original_start16'],x['original_end16'];fragment=h16[2*a:2*b].decode('utf-16-le');assert sha(fragment.encode())==x['utf8_fragment_sha256'];fragments.append([a,b,sha(fragment.encode())])
    for v in x.values():walk(v)
   elif isinstance(x,list):
    for v in x:walk(v)
  walk(entry)
  if seq==1263712:assert any(n[2]=='math' for n in nodes) and any(n[2]=='annotation' and json.loads(n[3]).get('encoding')=='application/x-tex' for n in nodes)
  if seq==342233:assert any(n[2]=='blockquote' for n in nodes)
  examples.append({'sequence':seq,'raw_sha':sha(raw),'html_sha':sha(html.encode()),'page':page,'revision':rev,'fragments':fragments,'license':meta['license'],'nodes':len(nodes)})
 checks.append('independent genuine MathML/conditional quote/long-context oracles; no genuine nonBMP claim')
 # Real bounded source fixtures drive subprocess CLI, not a mocked lock/guard.
 stage=out/'stage.sqlite';s=sqlite3.connect(stage);s.execute('CREATE TABLE records(sequence INTEGER PRIMARY KEY,member TEXT,member_offset INTEGER,raw_bytes INTEGER,raw_sha256 TEXT,page INTEGER,revision INTEGER,title TEXT,license_json TEXT,metadata_error TEXT,original_zlib BLOB)');pages=[]
 for seq,n in enumerate([2956,30000,100000,200000]):
  raw=(OLD/f'original-{n}.json').read_bytes();x=json.loads(raw);pages.append(x['identifier']);s.execute('INSERT INTO records VALUES(?,?,?,?,?,?,?,?,?,?,?)',(seq,'genuine-fixture',n,len(raw),sha(raw),x['identifier'],x['version']['identifier'],x['name'],json.dumps(x['license']),None,zlib.compress(raw)))
 s.commit();s.close();rank=out/'ranking.sqlite';r=sqlite3.connect(rank);r.execute('CREATE TABLE priority(id INTEGER PRIMARY KEY,views INTEGER,full INTEGER)');r.executemany('INSERT INTO priority VALUES(?,?,1)',[(x,10) for x in pages]);r.commit();r.close();ranksha=sha(rank.read_bytes());base=['python3',str(P),'--mode','engineering','--stage',str(stage),'--ranking',str(rank),'--ranking-sha256',ranksha,'--through','3','--count','4','--seconds','30','--cutoff','1791269964']
 def run(name,extra=None):
  command=base+['--out',str(out/name)]+(extra or []);start=time.time();r=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=45);(out/(name+'.log')).write_bytes(r.stdout);(out/(name+'.command.json')).write_text(json.dumps({'command':command,'exit':r.returncode,'start':start,'end':time.time()}));return r
 assert run('positive').returncode==0;state=json.loads((out/'positive/status.json').read_text());assert state['counts']['articles']==4 and not state['source_admission_established'];checks.append('real originals mixed-license CLI capsules, incomplete promotion denied')
 assert run('bad-rank',['--ranking-sha256','0'*64]).returncode!=0;checks.append('changed ranking rejected')
 # Hold a real kernel lease in another process; resume cannot touch any owner files.
 owner=out/'held';owner.mkdir();(owner/'status.json').write_text('protected-status');(owner/'events.jsonl').write_text('protected-events')
 lockscript="import fcntl,sys,time,pathlib; f=open(sys.argv[1],'a'); fcntl.flock(f,fcntl.LOCK_EX); print('held',flush=True); time.sleep(20)"
 child=subprocess.Popen(['python3','-c',lockscript,str(owner/'.lock')],stdout=subprocess.PIPE,text=True);assert child.stdout.readline().strip()=='held';before={f.name:sha(f.read_bytes()) for f in owner.iterdir()};r=run('held',['--resume']);assert r.returncode!=0 and child.poll() is None and before=={f.name:sha(f.read_bytes()) for f in owner.iterdir()};child.terminate();child.wait(timeout=5);checks.append('real competing process denied with identical owner files')
 # Actual SIGTERM during metadata: a larger declared prefix retains failure rather than fake completion.
 command=base+['--out',str(out/'signal'),'--through','999999'];proc=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);deadline=time.monotonic()+5
 while not (out/'signal/status.json').exists() and proc.poll() is None and time.monotonic()<deadline:time.sleep(.005)
 if proc.poll() is None:proc.send_signal(signal.SIGTERM)
 stdout=proc.communicate(timeout=10)[0];(out/'signal.log').write_bytes(stdout);assert proc.returncode!=0;checks.append('actual termination or missing-prefix refusal retained; not success')
 # Mutate a source digest (fixture only), preserving original fixture copy and each failed output.
 s=sqlite3.connect(stage);s.execute("UPDATE records SET raw_sha256=? WHERE sequence=0",('f'*64,));s.commit();s.close();assert run('bad-body').returncode==0;bad=json.loads((out/'bad-body/status.json').read_text());assert bad['counts']['articles']==3 and bad['outcomes']['retained-refusal']==1 and bad['independently_eligible_full_articles']==0;checks.append('digest corruption retained as refusal, no filler')
 # Production requires actual external cgroup enforcement, not the engineering RSS observation.
 limits=p.safety.cgroup_limits();rejected=False
 try:p.safety.verify_long_limits(limits)
 except ValueError:rejected=True
 checks.append('actual inherited cgroup sampled; production enforcement '+('unqualified' if rejected else 'bounded'))
 report={'status':'PASS','checks':checks,'genuine_extended_examples':examples,'actual_cgroup':limits,'external_production_cgroup_qualified':not rejected,'nonBMP_genuine':False,'fixture_rows_not_corpus':True};(out/'controls.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main(pathlib.Path(sys.argv[1]))
