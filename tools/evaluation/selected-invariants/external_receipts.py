"""Bounded offline validation of independently pinned producer/kernel receipts.

This establishes engineering identity/containment only, never rights or admission.
"""
import hashlib,json,pathlib,sqlite3,time
LIMIT=536870912
CUTOFF=1791269964

def require(value,message):
 if not value:raise ValueError(message)
def digest(path,deadline):
 h=hashlib.sha256()
 with path.open('rb') as f:
  while True:
   require(time.monotonic()<deadline,'Receipt audit deadline')
   b=f.read(1048576)
   if not b:break
   h.update(b)
 return h.hexdigest()
def code_map(code):
 result={}
 for path,sha in code.items():
  require('/tools/' in path,'Unbound executable path');name='tools/'+path.split('/tools/',1)[1]
  require(name not in result,'Duplicate executable identity');result[name]=sha
 return result
def load_packet(root,manifest_sha):
 root=pathlib.Path(root);deadline=time.monotonic()+30;require(digest(root/'manifest.json',deadline)==manifest_sha,'Independent manifest pin mismatch')
 manifest=json.loads((root/'manifest.json').read_text());files=manifest['files'];require(isinstance(files,list) and len(files)<=512,'Manifest file bound');names={}
 for entry in files:
  name=entry['path'];path=root/name;require(not pathlib.Path(name).is_absolute() and '..' not in pathlib.Path(name).parts and name not in names,'Unsafe/duplicate manifest path')
  require(path.resolve().is_relative_to(root.resolve()) and path.stat().st_size==entry['bytes']<=4194304,'Receipt path/size mismatch');require(digest(path,deadline)==entry['sha256'],'Receipt hash mismatch: '+name);names[name]=entry
 wanted=['snapshot/plan.json','snapshot/actual-kernel-start.json','snapshot/actual-child-start.json','snapshot/actual-kernel-final.json','snapshot/output/owner.json','snapshot/output/status.json','snapshot/output/events.jsonl']
 require(all(n in names for n in wanted),'Missing required kernel/owner/phase receipt')
 packet={n.split('/')[-1]:json.loads((root/n).read_text()) for n in wanted if n.endswith('.json')}
 packet['events']=[json.loads(line) for line in (root/'snapshot/output/events.jsonl').read_text().splitlines()]
 packet['manifest_sha256']=manifest_sha;packet['verified_files']=len(names);packet['manifest']=manifest
 return packet

def validate_bindings(p,expected_code,count,through):
 plan=p['plan.json'];before=p['actual-kernel-start.json'];child=p['actual-child-start.json'];after=p['actual-kernel-final.json'];owner=p['owner.json'];status=p['status.json'];events=p['events']
 require(code_map(owner['code'])==expected_code,'Stale producer/dependency identity')
 require(status['configuration']==owner and all(e['configuration']==owner for e in events),'Owner/event configuration disagreement')
 require(events and all(e['run_id']==status['run_id'] and e['pid']==status['pid'] and e['boot_id']==status['boot_id'] for e in events),'Run/process/boot disagreement')
 require(owner['count']==count and owner['through']==through,'Wrong selection/prefix')
 require(plan['argv']==child['argv'],'Executed argv differs from plan')
 argv=plan['argv'];arg=lambda name:argv[argv.index(name)+1]
 require(int(arg('--count'))==count and int(arg('--through'))==through,'CLI count/prefix disagreement')
 require(owner['stage']=='/home/isa/PocketLore-control/overnight-20261005/source-original-staging/run-originals/original-records.sqlite' and owner['ranking']=='/home/isa/PocketLore-control/scale-workers/wiki/priority-2000000.sqlite' and owner['ranking_sha256']=='2f1e6f9171154d2b315188ed421ee6370146a31d5c1aac768d5267c2f953261e','Frozen source/ranking identity mismatch')
 require(owner['stage']==arg('--stage') and owner['ranking']==arg('--ranking') and owner['ranking_sha256']==arg('--ranking-sha256'),'Source/ranking argv disagreement')
 require(float(arg('--cutoff'))<=CUTOFF and before['at']<=child['at']<=events[0]['updated_epoch']<=status['updated_epoch']<=after['at']<=CUTOFF,'Unbracketed or expired execution')
 require(all(a['updated_epoch']<=b['updated_epoch'] for a,b in zip(events,events[1:])),'Phase time regression')
 require(events[-1]['index_sha256']==status['index_sha256'] and events[-1]['status']==status['status'],'Terminal event mismatch')
 phases={e['phase'] for e in events};require({'metadata','materialize','final-identity','fts','hash','complete'}<=phases,'Missing actual finalization phases')
 require(after['child_returncode']==0 and status['status']=='PROVISIONAL_PREFIX_COMPLETE' and status['phase']=='complete','Failed/incomplete child')
 require(not status['source_admission_established'] and not status['whole_source_identity_verified'],'False full-source promotion')
 require(status['counts']['selected']==count==status['counts']['receipts'] and status['counts']['originals']==through+1,'Incomplete selected/disposition accounting')
 require(plan['limits']['Restart']=='no' and plan['limits']['KillMode']=='control-group' and 0<plan['limits']['TimeoutStopSec']<=10,'Unbounded restart/cleanup plan')
 require(after['at']-before['at']<=plan['limits']['RuntimeMaxSec']<=7200,'Observed wall bound exceeded')
 kernels=[before['kernel'],after['kernel']];first=kernels[0]
 require(first['path'].endswith('/'+plan['unit']+'.service'),'Wrong owned unit')
 for k in kernels:
  require(k['path']==first['path'] and 'pocketlore-runner.service' not in k['path'],'Shared/different kernel group')
  require(k['coordinator_pid']==first['coordinator_pid']>1,'Coordinator PID mismatch')
  require(k['memory.max']!='max' and 0<int(k['memory.max'])<=LIMIT and k['memory.swap.max']=='0','Memory/swap enforcement missing')
  quota,period=k['cpu.max'].split();require(quota!='max' and 0<int(quota)<=4*int(period) and int(period)>0,'CPU enforcement missing')
  require(k['pids.max']!='max' and 0<int(k['pids.current'])<=int(k['pids.max'])<=32,'Tasks enforcement missing')
  require(0<int(k['memory.peak'])<=int(k['memory.max']),'Invalid/exceeded kernel peak')
  values=dict(line.split() for line in k['memory.events'].splitlines());require(all(int(values[n])==0 for n in ('max','oom','oom_kill')),'Memory limit/OOM event')
 require(int(after['kernel']['memory.peak'])>=int(before['kernel']['memory.peak']),'Peak counter regression')
 pid=child['host_child_pid'];require(type(pid) is int and pid>1,'Missing positive host PID')
 proc={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in child['proc_status_identity']}
 require(int(proc['PPid'])==first['coordinator_pid'] and int(proc['NSpid'].split()[0])==pid and int(proc['NSpid'].split()[-1])==status['pid'],'Host/namespace PID mapping disagreement')
 require(status['cgroup']['path'].removeprefix('/sys/fs/cgroup')==first['path'],'Producer group disagreement')
 # Actual plan-byte hash is checked against manifest below, not reserialized JSON.
 plan_entry=next(e for e in p['manifest']['files'] if e['path']=='snapshot/plan.json');require(before['plan_sha256']==plan_entry['sha256'],'Kernel sample bound to another plan')
 for e in events:require(e['storage']['free_host_bytes']>=107374182400,'Host reserve breached')
 expected_files={e['path']:e['sha256'] for e in p['manifest']['files']}
 for name,hashvalue in expected_code.items():require(expected_files.get('snapshot/code/'+name)==hashvalue,'Frozen executed module missing/mismatched')
 return {'run_id':status['run_id'],'source_code':expected_code,'requested_originals':count,'prefix_dispositions':through+1,'kernel_peak_bytes':int(after['kernel']['memory.peak']),'kernel_group':first['path'],'host_pid':pid,'source_admission_established':False}

def validate_index(p,path,deadline_seconds=30):
 path=pathlib.Path(path);deadline=time.monotonic()+deadline_seconds;before=path.stat();expected=p['status.json']['index_sha256'];require(digest(path,deadline)==expected,'Actual index digest mismatch')
 d=sqlite3.connect('file:'+str(path.resolve())+'?mode=ro',uri=True);d.execute('PRAGMA query_only=ON');d.execute('PRAGMA cache_size=-2048');d.execute('PRAGMA mmap_size=0');d.set_progress_handler(lambda: int(time.monotonic()>deadline),1000)
 try:
  counts={t:d.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ('selected','originals','receipts','articles','contexts')};require(all(v==p['status.json']['counts'][t] for t,v in counts.items()),'Actual index counts mismatch')
  require(d.execute('SELECT last FROM progress').fetchone()[0]==p['owner.json']['through'],'Index prefix incomplete')
  search=d.execute("SELECT sql FROM sqlite_master WHERE name='search'").fetchone()[0];require('fts4' in search.lower(),'Wrong actual FTS schema')
  content='texts' if 'content=texts' in search else 'contexts';require(d.execute('SELECT count(*) FROM search').fetchone()[0]==d.execute('SELECT count(*) FROM '+content).fetchone()[0],'FTS/content counts mismatch')
  require(d.execute('SELECT count(*) FROM selected s LEFT JOIN receipts r ON r.sequence=s.sequence WHERE r.sequence IS NULL OR r.sha!=s.sha OR r.outcome!=s.outcome').fetchone()[0]==0,'Source receipt join mismatch')
  require(d.execute('PRAGMA quick_check').fetchone()[0]=='ok','Index integrity failure')
 finally:d.close()
 after=path.stat();require((before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'Index changed during read-only audit')
 return {'index_sha256':expected,'logical_bytes':after.st_size,'allocated_bytes':after.st_blocks*512,'actual_counts':counts,'source_semantic_admission':False}
