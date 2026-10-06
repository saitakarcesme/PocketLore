"""Explicit reused semantic controls; all JSON consumers use verified bytes."""
import json,pathlib
import contract as C
ROOT=C.ROOT;OUT=C.OLD;need=C.need
RUNTIME=['tools/packs/current-xml/indexed.py','tools/packs/current-xml/integrity.py','tools/packs/current-xml/adapter.py']
def load(name,rel,commit='a4739d145b2fd92c4f350a25f7d8a014e9ef6fa7'):
 import types
 b=C.git_bytes(commit,rel);r={'path':rel,'bytes':len(b),'sha256':C.sha(b)};source=C.consume(r);m=types.ModuleType(name);m.__file__=str(ROOT/rel);exec(compile(source,m.__file__,'exec'),m.__dict__);return m
I=load('indexed545','tools/packs/current-xml/indexed.py');A=I.A
V=load('integrity545','tools/packs/current-xml/integrity.py');F=load('fixtures545','tools/evaluation/indexed-xml/fixtures.py')
# Evidence-only adapter: unchanged historical runtime source consumes fixture
# receipt bytes through the same verified-FD API, rather than reopening JSON.
# Kernel proc/sys observations remain live reads, not historical authorities.
import types
class EvidencePath(type(pathlib.Path())):
 def read_text(self,*args,**kwargs):
  if str(self).startswith(str(C.OLD)+'/'):
   return C.consume(C.old_ref(self)).decode('utf-8')
  C.need(str(self).startswith('/proc/') or str(self).startswith('/sys/'),'unregistered-json-consumer')
  return super().read_text(*args,**kwargs)
I.pathlib=types.SimpleNamespace(Path=EvidencePath)
A.pathlib=types.SimpleNamespace(Path=EvidencePath)

def samples(rows):
 need(len(rows)>=2,'resource-samples');first=rows[0];last=0;initial=None
 for s in rows:
  st=dict(l.split(':',1) for l in s['status'].splitlines() if ':' in l);need(s['pid']==int(st['Pid'])==int(s['stat'].split(' (')[0])==first['pid'],'resource-PID');need(s['stat'].rsplit(')',1)[1].split()[19]==first['stat'].rsplit(')',1)[1].split()[19],'resource-startticks');need(s['namespaces']==first['namespaces'] and s['group_identity']==first['group_identity'],'resource-namespace');need(s['monotonic_ns']>last,'resource-chronology');last=s['monotonic_ns'];k=s['kernel'];need(int(k['memory.current'])<9*1024**3 and int(k['memory.swap.current'])==0,'resource-budget');need(int(k['memory.max'])==9*1024**3 and int(k['memory.swap.max'])==0 and k['cpu.max'].strip()=='200000 100000' and int(k['pids.max'])==512,'resource-containment');events=dict((a,int(b)) for a,b in (l.split() for l in k['memory.events'].splitlines()))
  if initial is None:initial=events
  need(set(events)==set(initial) and all(events[x]>=initial[x] for x in initial) and all(events[x]==initial[x] for x in ['max','oom','oom_kill']),'resource-events')

def runtime_bindings(source_hashes):
 m=C.manifest()
 for n in RUNTIME:need(C.hash_file(ROOT/n)==source_hashes[n]==m['references']['git:'+n]['sha256'],'historical-runtime')
 return True

def historical():
 m=C.manifest();verified={}
 for name in m['references']:verified[name]=C.verify_reference(name)
 _,d=C.verify_reference('audit',read_json=True);_,w=C.verify_reference('worker',read_json=True)
 need(d['status']=='PASS' and not d['errors'] and d['before']==d['after'],'historical-outcome');need(d['sources']==d['sources_after']==w['sources_before']==w['sources_after'],'historical-sources')
 runtime_bindings(d['sources'])
 a=d['admission'];need(a['records']==256 and a['postings']==1255814 and a['source_sha256']==m['references']['original']['sha256']=='1c58d27e72af460b549f868a1d2ce72401281400e322c4825aaf44aa20629daf' and a['index_sha256']==m['references']['indexed']['sha256']=='5cff5b277f6bc151a2eb1719f262ee49c449d8f0e4e9024c307796e874adbef1','historical-capsules')
 commitments=json.loads(C.old_git('tools/evaluation/indexed-recovery/original-commitments.json'));need(C.sha(C.old_git('tools/evaluation/indexed-recovery/original-commitments.json'))==m['references']['git:tools/evaluation/indexed-integrity/original-commitments.json']['sha256'],'historical-commitments');rows=d['original_rows'];need(len(rows)==len(commitments['records'])==256,'historical-count')
 for r,c in zip(rows,commitments['records']):need(r['id']==c['id'] and C.sha(r['text'].encode())==c['text_sha256'] and A.sha(A.canonical(r['metadata']))==c['metadata_sha256'] and r['title']==r['metadata']['title'],'historical-original')
 need([q['query'] for q in d['queries']]==['#REDIRECT [[Computer accessibili','AccessibleComputing','AbsentNeedleZZZ'],'historical-query-roster')
 for q in d['queries']:V.validate_hits(A,q['result']['hits'],rows,q['query'])
 need(w['exit']==0 and w['error'] is None and w['reaped'] and w['process_absent'],'historical-reap');need(d['export_sha256']==m['references']['export']['sha256'],'historical-export');samples(d['samples']);samples(w['resource_samples'])
 for s in w['samples']:
  st=dict(x.split(':',1) for x in s['status'].splitlines() if ':' in x);need(s['pid']==w['pid']==int(st['Pid'])==int(s['stat'].split(' (')[0]) and s['startticks']==w['startticks']==s['stat'].rsplit(')',1)[1].split()[19],'historical-worker-identity')
 return {'classification':'HISTORICAL_543_EXECUTION_ONLY_FAILED_TASK_CAP','references':verified,'records':256,'postings':1255814,'admission_ns':a['ended_ns']-a['started_ns'],'open_ns':d['open_ns'],'raw_worker_pid':w['pid'],'raw_worker_startticks':w['startticks'],'replay_queries':[{'query':q['query'],'hits':q['result']['hits']} for q in d['queries']],'old_logical_debt_bytes':m['old_logical_debt_bytes']}

def functional(s):
 rows=F.oracle_rows(8);need(s['status']=='PASS','functional-outcome');need([x['query'] for x in s['queries']]==C.POLICY['queries'],'query-roster')
 for q in s['queries']:V.validate_hits(A,q['result']['hits'],rows,q['query']);need(q['result']['stats']['full_scan'] is False,'no-full-scan')
 need(set(x['name'] for x in s['hit_mutations'])==set(C.POLICY['hit_guards']),'hit-control-roster')
 for m in s['hit_mutations']:
  V.validate_hits(A,s['queries'][0]['result']['hits'],rows,s['queries'][0]['query']);p=OUT/'functional'/m['file'];x=C.consume(C.old_ref(p),True);need(C.sha(A.canonical(x))==m['sha256'] and x['result']['hits']==x['oracle']==x['legacy'],'hit-rebound')
  try:V.validate_hits(A,x['result']['hits'],rows,x['query'])
  except A.Refused as e:need(str(e)==m['guard']==C.POLICY['hit_guards'][m['name']],'hit-guard')
  else:raise C.Refused('hit-accepted')
 need(set(x['name'] for x in s['database_mutations'])==set(C.POLICY['posting_guards']),'posting-control-roster')
 for m in s['database_mutations']:
  r=I.Reader(OUT/'functional/current');r.admit(OUT/'functional/original',s['source_sha256'],s['index_sha256']);r.close();r=None
  try:r=I.Reader(OUT/'functional'/m['path']);r.admit(OUT/'functional/original',m['source_anchor'],m['index_anchor'])
  except A.Refused as e:need(str(e)==m['guard']==C.POLICY['posting_guards'][m['name']],'posting-guard')
  else:raise C.Refused('posting-accepted')
  finally:
   if r:r.close()
 c=s['controls'];need(c['pagination'] and c['export'] and c['inspection'] and c['rollback'] and c['version-change']=='admission-version-changed' and c['cancel']=='cancelled' and c['short']=='indexed-query-length' and c['unadmitted']=='source-admission-required' and c['deadline'],'functional-controls')
 return True
