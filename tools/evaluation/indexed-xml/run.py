#!/usr/bin/env python3
import copy,json,os,pathlib,resource,shutil,signal,sqlite3,statistics,sys,time,traceback
import check,fixtures,owned
A=check.A;I=check.I;ROOT=check.ROOT;BASE=ROOT/'downloads/indexed-xml-542';cancelled=False
def signal_cancel(*args):
 global cancelled
 cancelled=True
for sig in [signal.SIGTERM,signal.SIGINT]:signal.signal(sig,signal_cancel)
def preflight():
 raw=pathlib.Path('/proc/meminfo').read_text();check.need(int(next(l.split()[1] for l in raw.splitlines() if l.startswith('MemAvailable:')))*1024>=11*1024**3,'available');return {'meminfo':raw,'affinity':sorted(os.sched_getaffinity(0)),'session':os.environ.get('CODEX_THREAD_ID','not-exposed'),'sample':A.sample('preflight')}
class CountIndex(I.Reader):
 def inspect(self,ident):
  r=super().inspect(ident);self.inspections+=1;self.text_bytes+=len(r['text'].encode());return r
class CountLegacy(A.Reader):
 def inspect(self,ident):
  r=super().inspect(ident);self.inspections+=1;return r

def trial(legacy,index,query,oracle):
 legacy.guard=A.Guard(10);legacy.inspections=0;index.inspections=0;index.text_bytes=0;begin=time.monotonic_ns();c=time.process_time_ns();u=resource.getrusage(resource.RUSAGE_SELF);l=legacy.search(query);end=time.monotonic_ns();legacy_ns=end-begin;legacy_cpu=time.process_time_ns()-c;v=resource.getrusage(resource.RUSAGE_SELF)
 begin=time.monotonic_ns();c=time.process_time_ns();u2=resource.getrusage(resource.RUSAGE_SELF);r=index.search(query);end=time.monotonic_ns();v2=resource.getrusage(resource.RUSAGE_SELF)
 row={'query':query,'frozen_query':query,'legacy':l,'oracle':oracle,'result':r,'legacy_ns':legacy_ns,'indexed_ns':end-begin,'legacy_cpu_ns':legacy_cpu,'indexed_cpu_ns':time.process_time_ns()-c,'legacy_decompressions':legacy.inspections,'observed_inspections':index.inspections,'observed_text_bytes':index.text_bytes,'legacy_faults':{'major':v.ru_majflt-u.ru_majflt,'minor':v.ru_minflt-u.ru_minflt},'indexed_faults':{'major':v2.ru_majflt-u2.ru_majflt,'minor':v2.ru_minflt-u2.ru_minflt},'begin_ns':begin,'end_ns':end}
 check.validate_query(row);return row

def synthetic():
 out=BASE/'synthetic-v5';out.mkdir(exist_ok=False);sources=check.freeze();A.atomic(out/'freeze.json',{'sources':sources,'executable':{'path':sys.executable,'sha256':A.filehash(sys.executable),'version':A.version(sys.executable)},'preflight':preflight()});samples=[A.sample('synthetic-start')];fixture_base=BASE/'synthetic';frozen_fixtures=json.loads((fixture_base/'fixture-identities.json').read_text());check.need(all(A.filehash(fixture_base/n/'index.sqlite')==h for n,h in frozen_fixtures.items()),'frozen-fixture');rows=fixtures.oracle_rows(12);performance=fixtures.oracle_rows(8192);policy=json.loads((ROOT/'docs/evidence/indexed-xml-inputs/policy.json').read_text());A.atomic(out/'fixture-identities.json',{n:A.filehash(fixture_base/n/'index.sqlite') for n in ['functional','performance']})
 builds={}
 for name in ['functional']:
  builds[name]=owned.build(fixture_base/name,out/(name+'-index'),cancel=lambda:cancelled);check.need(builds[name]['status']=='BUILT_INSPECTION_ONLY','build-'+name)
 performance_index=BASE/'synthetic-v3/performance-index';old_worker=json.loads((BASE/'synthetic-v3/performance-index-worker/worker.json').read_text());runtime_inputs=['tools/packs/current-xml/adapter.py','tools/packs/current-xml/indexed.py','tools/evaluation/indexed-xml/fixtures.py'];check.need(all(old_worker['sources_before'][k]==sources[k] for k in runtime_inputs),'reused-index-runtime');builds['performance']=json.loads((performance_index/'index-receipt.json').read_text());check.need(A.filehash(performance_index/'index.sqlite')==builds['performance']['output_sha256'],'reused-index-hash')
 r=I.Reader(out/'functional-index');l=A.Reader(fixture_base/'functional');controls={}
 for q in ['😀é','otherwise','<math>','{{T|','TitleOnlyNeedle','Repeat','(OR "quoted")']:
  result=r.search(q);check.need(result['hits']==l.search(q)==fixtures.expected(A,rows,q),'functional-oracle')
  for hit in result['hits']:r.resolve(hit)
 ident=rows[0]['id'];ex=r.export(ident,out/'export');check.need((out/'export/original.wikitext').read_bytes()==rows[0]['text'].encode(),'export')
 try:r.search('ab');raise AssertionError('short query accepted')
 except A.Refused as e:controls['short']=str(e)
 r.guard.deadline=0;r.db.set_progress_handler(lambda:r.guard.sql(),1);check.need(r.search('Common')['hits']==fixtures.expected(A,rows,'Common'),'aged-reader');controls['aged-reader']=True
 first=r.search('Common',3);second=r.search('Common',3,first['cursor']);check.need([x['id'] for x in first['hits']+second['hits']]==[x['id'] for x in rows[:6]],'pagination');controls['pagination']=True;r.close();l.close()
 r=I.Reader(out/'functional-index',cancel=lambda:False);r.cancel=lambda:True
 try:r.search('Common');raise AssertionError('cancel accepted')
 except A.Refused as e:controls['cancel']=str(e)
 finally:r.close()
 fail=I.build(fixture_base/'functional',out/'deadline',seconds=0.000001);controls['deadline']=fail['status'];fail2=I.build(fixture_base/'functional',out/'cancelled',cancel=lambda:True);controls['rollback']=fail['status']==fail2['status']=='FAILED' and not (out/'deadline/index.sqlite').exists() and A.filehash(fixture_base/'functional/index.sqlite')==builds['functional']['input_sha256']
 calls=[0]
 def midcancel():
  calls[0]+=1;return calls[0]>50
 mc=I.build(fixture_base/'functional',out/'mid-cancel',cancel=midcancel);controls['mid-cancel']=mc['status']=='FAILED' and any('cancelled' in e for e in mc['errors']) and not (out/'mid-cancel/index.sqlite').exists()
 race=out/'race-input';shutil.copytree(fixture_base/'functional',race);calls=[0]
 def mutate_input():
  calls[0]+=1
  if calls[0]==4:
   p=race/'index.sqlite';st=p.stat();os.utime(p,ns=(st.st_atime_ns,st.st_mtime_ns+1000000))
  return False
 rc=I.build(race,out/'race-output',cancel=mutate_input);controls['input-race']=rc['status']=='FAILED' and any('input-mutated' in e for e in rc['errors']) and not (out/'race-output/index.sqlite').exists()
 database=[]
 for name,sql,guard in [('schema','PRAGMA user_version=0','index-schema'),('tokenizer',"UPDATE index_contract SET value='{}' WHERE key='configuration'",'tokenizer'),('source',"UPDATE index_contract SET value='\"wrong\"' WHERE key='source_id'",'index-source'),('record-count',"DELETE FROM records WHERE id=1",'record-count'),('index-digest',"UPDATE terms SET gram=x'010203' WHERE term=1",'index-digest'),('index-hash',None,'index-hash')]:
  good=I.Reader(out/'functional-index');good.close();child=out/('bad-'+name);shutil.copytree(out/'functional-index',child)
  db=sqlite3.connect(child/'index.sqlite');db.execute(sql or 'PRAGMA user_version=999');db.commit();db.close()
  if sql:
   h=A.filehash(child/'index.sqlite')
   for receipt in ['receipt.json','index-receipt.json']:
    j=json.loads((child/receipt).read_text());j['output_sha256']=h;A.atomic(child/receipt,j)
  try:bad=I.Reader(child);bad.close();raise AssertionError('corruption accepted')
  except A.Refused as e:check.need(str(e)==guard,'unexpected guard '+str(e));database.append({'name':name,'guard':str(e),'path':str(child.relative_to(ROOT)),'output_sha256':A.filehash(child/'index.sqlite')})
 begin=time.monotonic_ns();l=CountLegacy(fixture_base/'performance');r=CountIndex(performance_index);open_ns=time.monotonic_ns()-begin;trials=[]
 for repeat in range(10):
  for q in policy['queries']:trials.append(trial(l,r,q,fixtures.expected(A,performance,q)))
  samples.append(A.sample('trial-'+str(repeat)))
 l.close();r.close();mutants=[]
 for name,guard,edit in [('query','query-literal',lambda m:m.update(query='changed')),('counter','candidate-count',lambda m:m.update(observed_inspections=8192)),('fullscan','full-scan',lambda m:m['result']['stats'].update(full_scan=True)),('range','exact-results',lambda m:m['result']['hits'][0].update(start_utf16=0)),('quote','exact-results',lambda m:m['result']['hits'][0].update(quote='fake'))]:
  check.validate_query(trials[0]);m=copy.deepcopy(trials[0]);edit(m)
  try:check.validate_query(m);raise AssertionError('mutation accepted')
  except ValueError as e:check.need(str(e)==guard,'mutation-guard');f=out/(name+'.mutation.json');A.atomic(f,m);mutants.append({'name':name,'guard':str(e),'file':str(f.relative_to(BASE)),'base_sha256':A.sha(A.canonical(trials[0])),'mutated_sha256':A.sha(A.canonical(m))})
 summary={}
 for q in policy['queries']:
  rowsq=[x for x in trials if x['query']==q];summary[q]={}
  for key in ['legacy_ns','indexed_ns']:
   values=sorted(x[key] for x in rowsq);summary[q][key]={'p50':statistics.median(values),'p95':values[9]}
  summary[q]['decompressions']={'legacy':rowsq[0]['legacy_decompressions'],'indexed':rowsq[0]['observed_inspections']}
 workers=[]
 for name,code,seconds,expected in [('failure','import time;time.sleep(0.1);raise SystemExit(7)',2,7),('hung','import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(5)',0.2,-9)]:
  w=owned.run([sys.executable,'-c',code],out/('worker-'+name),seconds);check.validate_worker(w,expected);workers.append({'name':name,'expected_exit':expected,'receipt':w})
 for failure in ['initial-stat','collection']:
  w=owned.run([sys.executable,'-c','import time;time.sleep(5)'],out/('worker-'+failure),2,inject=failure);check.validate_worker(w,-15,True);workers.append({'name':failure,'expected_exit':-15,'allow_unobserved':True,'receipt':w})
 worker_mutations=[];positive_worker_file=str((out/'functional-index-worker/worker.json').relative_to(BASE));positive=json.loads((BASE/positive_worker_file).read_text())
 for name,guard,edit in [('PID','worker-pidfd',lambda m:m.update(pid=0)),('startticks','worker-startticks',lambda m:m.update(startticks='0')),('reap','worker-reap',lambda m:m.update(reaped=False)),('deadline','worker-deadline',lambda m:m.update(ended_ns=m['started_ns']+200*10**9)),('source','worker-source',lambda m:m['sources_before'].update({next(iter(m['sources_before'])):'0'*64})),('observations','worker-observations',lambda m:m.update(samples=[])),('outcome','worker-outcome',lambda m:m.update(exit=9)),('swap','resource',lambda m:m['resource_samples'][0]['kernel'].update({'memory.swap.current':'1'}))]:
  check.validate_worker(positive,0);m=copy.deepcopy(positive);edit(m)
  try:check.validate_worker(m,0);raise AssertionError('worker corruption accepted')
  except ValueError as e:check.need(str(e)==guard,'worker mutant guard '+str(e));path=out/('worker-'+name+'.mutation.json');A.atomic(path,m);worker_mutations.append({'name':name,'guard':str(e),'file':str(path.relative_to(BASE))})
 samples.append(A.sample('synthetic-closed'));check.validate_samples(samples);check.need(sources==check.freeze(),'source-mutated');result={'status':'PASS','sources':sources,'workers':workers,'positive_worker_file':positive_worker_file,'worker_mutations':worker_mutations,'controls':controls,'database_mutations':database,'receipt_mutations':mutants,'trials':trials,'summary':summary,'open_validation_ns':open_ns,'samples':samples,'builds':builds,'functional_index':str((out/'functional-index').relative_to(ROOT)),'fixture_input_hashes':frozen_fixtures,'fixture_path':str(fixture_base.relative_to(ROOT)),'reused_index':{'path':str(performance_index.relative_to(ROOT)),'runtime_inputs':{k:old_worker['sources_before'][k] for k in runtime_inputs},'historical_worker_file':str((BASE/'synthetic-v3/performance-index-worker/worker.json').relative_to(BASE)),'scope':'Same exact adapter/index-builder/fixture code and input; prior build timings remain historical; all query trials rerun on current reader.'},'fixed_fixture_rows':8192,'output_bytes':sum(p.stat().st_size for p in out.rglob('*') if p.is_file())};A.atomic(BASE/'synthetic.json',result);print(json.dumps({'status':'PASS','summary':summary,'bytes':result['output_bytes']}))

def derive():
 sources=check.freeze();s=json.loads((BASE/'synthetic.json').read_text());check.need(s['status']=='PASS' and s['sources']==sources,'synthetic-current');source=ROOT/'downloads/current-xml-541/prefix';before=A.version(source/'index.sqlite');h=A.filehash(source/'index.sqlite');check.need(h=='1c58d27e72af460b549f868a1d2ce72401281400e322c4825aaf44aa20629daf','prefix-input');preflight_data=preflight()
 with open(BASE/'derivation-attempt.json','x') as f:json.dump({'sources':sources,'input_version':before,'sha256':h,'preflight':preflight_data},f)
 samples=[A.sample('derive-start')];r=owned.build(source,BASE/'derived',cancel=lambda:cancelled);check.need(r['status']=='BUILT_INSPECTION_ONLY','derivation-failed');l=A.Reader(source);l.guard=A.Guard(180);i=I.Reader(BASE/'derived');i.guard=A.Guard(180);l.db.set_progress_handler(l.guard.sql,1000);count=0;hashes=[]
 for a,b in zip(l.db.execute('SELECT * FROM records ORDER BY id'),i.db.execute('SELECT * FROM records ORDER BY id')):
  check.need(a==b,'original-record-changed');orig=l.inspect(a[1]);current=i.inspect(a[1]);check.need(orig==current,'inspection-changed');count+=1;hashes.append({'id':a[1],'text_sha256':orig['text_sha256'],'lexical_sha256':orig['lexical_sha256'],'metadata_sha256':A.sha(a[6].encode())})
 check.need(count==256 and l.db.execute('SELECT count(*) FROM records').fetchone()[0]==i.db.execute('SELECT count(*) FROM records').fetchone()[0],'derived-count')
 flow=json.loads((ROOT/'downloads/current-xml-541/prefix-flow.json').read_text());queries=[]
 for q in [flow['query'],flow['inspection']['title'],'AbsentNeedleZZZ']:
  l.guard=A.Guard(10);result=i.search(q);legacy=l.search(q);check.need(result['hits']==legacy,'prefix-query');queries.append({'query':q,'result':result,'legacy':legacy})
 ex=i.export(flow['inspection']['id'],BASE/'export');l.close();i.close();after=A.version(source/'index.sqlite');check.need(before==after and A.filehash(source/'index.sqlite')==h,'input-mutated');samples.append(A.sample('derive-closed'));check.validate_samples(samples);check.need(sources==check.freeze(),'source-changed');A.atomic(BASE/'derived.json',{'status':'PASS','sources':sources,'input_sha256':h,'before':before,'after':after,'output':str((BASE/'derived').relative_to(ROOT)),'records':count,'all_original_fields_equal':True,'record_hashes':hashes,'queries':queries,'export_path':str((BASE/'export/original.wikitext').relative_to(ROOT)),'export_sha256':ex['sha256'],'samples':samples,'build':r});print(json.dumps({'status':'PASS','records':count,'bytes':r['storage']}))

def packet():
 raw={}
 for p in BASE.rglob('*'):
  if p.is_file() and p.suffix not in ['.sqlite'] and p.name!='review.json':
   check.need(p.stat().st_size<16*1024**2,'raw-size');raw[str(p.relative_to(BASE))]=check.envelope(p)
 sources=json.loads((BASE/'synthetic.json').read_text())['sources'];p={'task':'542-indexed-original-wikitext-search','sources_before':sources,'sources_after':check.freeze(),'source_content':{n:check.envelope(ROOT/n) for n in check.INPUTS},'raw':raw,'build':json.loads((BASE/'android-build.json').read_text()),'status':'UNVALIDATED'}
 try:check.validate(p);p['status']='PASS_HOST_INDEXED_ENGINEERING_ONLY'
 except Exception as e:p['status']='FAIL';p['error']=str(e)
 A.atomic(ROOT/'docs/evidence/indexed-xml-search-review.json',p);print(p['status']);return int(p['status']=='FAIL')
if __name__=='__main__':
 try:preflight();sys.exit({'synthetic':synthetic,'derive':derive,'packet':packet}[sys.argv[1]]() or 0)
 except Exception:
  e=traceback.format_exc();(BASE/('failure-'+str(time.time_ns())+'.txt')).write_text(e);print(e,file=sys.stderr);sys.exit(1)
