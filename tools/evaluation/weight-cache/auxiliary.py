"""Raw auxiliary contracts. Guard names are independent mutation-test targets."""
import json,re,base64,hashlib,copy,gzip
from common import R,SOURCES,BINARIES,process_stat,status_pid,sample_identity
class Refused(AssertionError):pass
def need(ok,guard):
 if not ok:raise Refused(guard)
def envelopes(run):
 need(run.get('stream_contract')=='stdout_and_stderr_combined_by_supervisor','stream')
 need(not run.get('collection_errors') and run.get('raw_bytes'),'collection')
 need(set(run['raw_bytes'])=={'stdout.log'}|set(run['observations']),'envelope-coverage')
 for key,v in run['raw_bytes'].items():
  b=base64.b64decode(v['base64'],validate=True);need(hashlib.sha256(b).hexdigest()==v['sha256'],'envelope-hash')
  need(b.decode()==(run['stdout'] if key=='stdout.log' else run['observations'][key]),'envelope-content')
def process(run,expected_error=None):
 need(run.get('samples') and run.get('pidfd_opened'),'live-required')
 need(run['executable_before']==run['executable_after'],'executable-stable')
 need(not run.get('cleanup_failure') and not run.get('post_identity_failure'),'cleanup-failure')
 need(bool(run.get('failure'))==bool(expected_error),'outcome')
 if expected_error:need(expected_error in run['failure'],'expected-error')
 else:need(run['exit']==0,'exit')
 need(int(re.search(r'^Pid:\s+(\d+)',run['pidfd_fdinfo'],re.M)[1])==run['pid'],'pidfd')
 ns=run['samples'][0]['namespaces'];last=run['start_ns']
 for s in run['samples']:
  need(s['pid']==run['pid']==status_pid(s['status'])==process_stat(s['stat'])[0],'sample-pid')
  need(process_stat(s['stat'])[1]==run['startticks'],'sample-startticks')
  need(s['namespaces']==ns,'sample-namespace')
  need(last<=s['monotonic_ns']<=run['end_ns'],'sample-chronology');last=s['monotonic_ns']
  need(0<int(s['memory.current'])<8053063680 and int(s['memory.peak'])>=int(s['memory.current']),'aggregate')
  need(int(s['memory.swap.current'])==0,'swap')
  need('Pss:' in s['smaps_rollup'] and 'Rss:' in s['smaps_rollup'],'rollup')
  need(all(x in s['memory.events'] for x in ['oom ','oom_kill ','max ']),'events')
  sample_identity(s,run['pid'],run['startticks'],ns)
 need(run['end_ns']-run['start_ns']<int((run['limits']['wall_seconds']+4)*1e9),'wall')
 cleanup=run['cleanup'];need(cleanup and cleanup[-1]['action']=='REAPED','reaped')
 need(cleanup[-1]['exit']==run['exit'],'reap-exit')
 last=run['start_ns']
 for c in cleanup:
  need(c['pid']==run['pid'],'cleanup-pid');need(last<=c['monotonic_ns']<=run['end_ns'],'cleanup-chronology');last=c['monotonic_ns']
  if c['action']!='REAPED':need(c['startticks']==run['startticks'],'cleanup-startticks')
 if expected_error:
  actions=[c['action'] for c in cleanup];need(actions[0]=='TERM' and actions[-1]=='REAPED','termination')
  need(run['exit'] in [-9,-15],'signal-exit')
  if expected_error=='Owned child deadline':need(actions==['TERM','KILL','REAPED'] and run['exit']==-9,'hung-kill')
 envelopes(run)
 from semantic import resource_contract
 resource_contract(run)
 return ns
LIFECYCLE={
 'unaligned':'Unsafe mapping range','oversized':'Unsafe mapping range',
 'absent-map':'Alias, retiring mapping or async reader still active',
 'scalar-multitoken':'Scalar diagnostic requires exactly one token',
 'scalar-live-reader':'Alias, retiring mapping or async reader still active',
 'scalar-exception':'Engineered decode exception','scalar-cancel':'Cancelled or expired native operation',
 'async-reader':'Alias, retiring mapping or async reader still active','alias-mapping':'Unsafe mapping registration',
 'live-lifetime':'Cannot release mapping with live readers','nested-owner':'Nested mapping owner','partial-map':'Unbound partial/alias mapping',
 'cancelled':'Cancelled or expired native operation','closed-map':'Alias, retiring mapping or async reader still active',
 'reader-after-unregister':'No live owned mapping for reader','retiring-reader':'No live owned mapping for reader',
 'retiring-advice':'Alias, retiring mapping or async reader still active','exception-unmapped':'Alias, retiring mapping or async reader still active',
 'wrong-inode':'Loader descriptor differs from verified original','wrong-size':'Wrong original length','wrong-hash':'Wrong original digest',
 'deadline':'Cancelled or expired native operation','renamed':'Changed original version/path'}
FAULT={'double-owner':'Dedicated policy owner already active','writable-inherited':'Inherited descriptor is not readonly',
 'live-reader-advice':'Alias, retiring mapping or async reader still active','alias':'Unsafe mapping registration',
 'cancel':'Cancelled or expired native operation','exception-release':'Alias, retiring mapping or async reader still active',
 'hash':'Wrong original digest','deadline':'Cancelled or expired native operation'}
def trace(run,inp):
 ns=''.join(run['samples'][0]['namespaces'][x] for x in ['mnt','pid','user']);groups={}
 for name,raw in run['observations'].items():
  if '-trace-' not in name:continue
  entries=[json.loads(l) for l in raw.splitlines()];need(entries,'trace-nonempty');pid=entries[0]['pid'];groups[pid]=entries
  if pid==run['pid']:
   from semantic import verified_phase
   verified_phase(entries)
  last=run['start_ns'];ticks=process_stat(entries[0]['stat'])[1]
  for i,e in enumerate(entries):
   need(e['sequence']==i,'operation-sequence');need(e['pid']==pid==status_pid(e['status'])==process_stat(e['stat'])[0],'trace-pid')
   need(process_stat(e['stat'])[1]==ticks and (pid!=run['pid'] or ticks==run['startticks']),'trace-startticks')
   need(last<=e['monotonic_ns']<=run['end_ns'],'trace-chronology');last=e['monotonic_ns']
   need(e['namespaces']==ns,'trace-namespace');need(e['cgroup']==run['samples'][0]['cgroup'],'trace-cgroup')
   if pid!=run['pid']:need(int(re.search(r'^PPid:\s+(\d+)',e['status'],re.M)[1])==run['pid'],'child-parent')
   mapped={'scalar-multitoken','scalar-live-reader','scalar-exception','scalar-cancel','async-reader','alias-mapping','live-lifetime','nested-owner','partial-map','cancelled','retiring-reader','retiring-advice','live-reader-advice','alias','cancel','no-progress','mincore-failure','advice-failure'}
   requires_map=e['operation'] in mapped or (e['operation']=='seccomp' and pid==run['pid'])
   if requires_map:need(e['owner_present'] and bool(e.get('owned_smaps')),'mapping-required')
   if e['owner_present']:
    v=inp['version'];
    if e['operation']=='verified':
     a=e['verified_owner'];need(a['sha256']==inp['sha256'] and a['inode']==v['inode'] and a['bytes']==v['size'],'verified-identity')
     need(a['pid']==pid and int(a['startticks'])==ticks and a['namespaces']==ns,'verified-owner')
    need(e['inode']==v['inode'] and e['device']==v['device'],'owner-inode');need(e['size']==v['size'] and e['mtime_ns']==v['mtime_ns'],'owner-version')
    need(int(re.search(r'^flags:\s+(\d+)',e['fdinfo'],re.M)[1],8)&3==0,'owner-readonly')
    need(int(re.search(r'^ino:\s+(\d+)',e['fdinfo'],re.M)[1])==e['inode'],'fd-inode')
    mid=re.search(r'^mnt_id:\s+(\d+)',e['fdinfo'],re.M)[1];mount=next((l for l in e['mountinfo'].splitlines() if l.split()[0]==mid),None);need(mount is not None,'owner-mount')
    dev=tuple(map(int,mount.split()[2].split(':')))
    headers=0
    for line in e['owned_smaps'].splitlines():
     m=re.match(r'^([0-9a-f]+)-([0-9a-f]+) (\S+) ([0-9a-f]+) ([0-9a-f]+):([0-9a-f]+) (\d+)',line)
     if m:
      headers+=1
      need(m[3]=='r--s','mapping-readonly');need(int(m[7])==e['inode'],'mapping-inode')
      need((int(m[5],16),int(m[6],16))==dev,'mapping-mount');need(int(m[4],16)==0 and int(m[2],16)-int(m[1],16)==v['size'],'mapping-range')
    need(headers==1 if requires_map else headers<=1,'mapping-header')
    need(not e['owned_smaps'] or headers==1,'mapping-header')
   else:need('owned_smaps' not in e and 'fdinfo' not in e,'no-fabricated-owner')
 need(run['pid'] in groups,'parent-trace')
 return groups

def validate_aux(r):
 f=r['frozen'];summary={}
 for name,expected in [('lifecycle',LIFECYCLE),('fault_controls',FAULT),('hung',None),('read-error',None)]:
  packet=r[name];run=packet['run'];pre,post=packet['pre'],packet['post']
  need(set(pre['source'])==set(SOURCES) and pre['source']==post['source']==f['source'],'aux-source')
  need(pre['executable']==post['executable']==run['executable_before'],'aux-executable')
  need(pre['derivation']==post['derivation']==f['derivation'] and pre['configuration']==post['configuration']==f['configuration'],'aux-configuration')
  error={'hung':'Owned child deadline','read-error':'Engineered observation read failure'}.get(name)
  process(run,error)
  need(run['kernel_before']['group_identity']==f['kernel']['group_identity'],'events-cgroup')
  if expected is None:
   need(packet['input'] is None and post['input'] is None and not run['observations'],'process-only');summary[name]={'mapping':'not expected','exit':run['exit'],'cleanup':run['cleanup']};continue
  inp=packet['input'];need(inp==pre['input'],'input-binding');need(post['input']['sha256']==inp['sha256'],'input-hash')
  for key in ['device','inode','size','mtime_ns']:need(post['input']['version'][key]==inp['version'][key],'input-version')
  key=BINARIES[0] if name=='lifecycle' else BINARIES[-2];need(pre['executable']==f['binary'][key],'linked-executable')
  groups=trace(run,inp);events=groups[run['pid']];pairs=[];pending=None
  need(all(e['operation'] in set(expected)|{'process','verified','teardown'} for e in events),'known-operation')
  need(events[0]['operation']=='process' and events[0]['outcome']=='begin','process-begin')
  ownership=False
  for e in events:
   if e['operation']=='verified':ownership=True
   need(e['owner_present']==ownership,'owner-lifetime')
   if name=='fault_controls' and e['operation']=='teardown':ownership=False
   if e['operation'] not in expected:continue
   if e['outcome']=='begin':need(pending is None,'operation-overlap');pending=e
   else:
    need(pending is not None and pending['operation']==e['operation'],'operation-pair')
    need(e['outcome']=='refused','refusal-outcome');need(e['reason']==expected[e['operation']],'refusal-reason');pairs.append(e['operation']);pending=None
  need(pending is None and set(pairs)==set(expected),'refusal-denominator')
  need(pairs==[k for k in expected for _ in range(33 if k=='scalar-live-reader' else 1)],'refusal-order')
  for key in expected:need(pairs.count(key)==(33 if key=='scalar-live-reader' else 1),'refusal-count')
  positives={x.get('control'):x for x in (json.loads(l) for l in run['stdout'].splitlines() if l.startswith('{')) if x.get('pass')}
  if name=='lifecycle':
   need(set(positives)=={'scalar-order-byte-oracle','mapped-pread-after-advice','deferred-destructor-observation','inherited-fd'},'positive-denominator')
   need(positives['scalar-order-byte-oracle']['tokens']==positives['scalar-order-byte-oracle']['synchronizations']==33,'scalar-count')
   need(positives['mapped-pread-after-advice']['payload_read_bytes']==12582912,'byte-oracle-count')
  else:need(set(positives)=={'dedicated-reuse-offset'},'positive-denominator')
  endings=[e for e in events if e['operation']=='teardown'];need(len(endings)==1 and endings[0]['outcome']=='complete' and endings[0]['owned_smaps']=='','teardown')
  if name=='fault_controls':
   children=[g for p,g in groups.items() if p!=run['pid']];need(len(children)==2,'child-count')
   for g,op,reason in zip(sorted(children,key=lambda x:x[0]['monotonic_ns']),['fadvise-kernel-failure','madvise-kernel-failure'],['Dedicated POSIX_FADV_RANDOM failed','Owned MADV_RANDOM failed']):
    need([e['operation'] for e in g]==['child','seccomp',op],'syscall-phase');need(g[1]['outcome']=='installed' and g[2]['outcome']=='refused' and g[2]['reason']==reason,'syscall-refusal')
    need(re.search(r'^Seccomp:\s+2$',g[2]['status'],re.M) is not None,'seccomp-kernel')
    lines=[json.loads(l) for l in run['stdout'].splitlines() if l.startswith('{')];need(any(x.get('child')==g[0]['pid'] and x.get('exit')==0 and x.get('refusal')==op for x in lines),'child-wait')
  summary[name]={'refusals':len(pairs),'operations':pairs,'children':len(groups)-1}
 # Reuse auxiliary cases use the same supervised identity contract and actual traces.
 for name in ['no-progress','mincore-failure','advice-failure','tail','remap']:
  run=r['runs'][name];process(run);groups=trace(run,r['inputs']['retain']);events=groups[run['pid']]
  need(events[-1]['operation']=='teardown' and events[-1]['owned_smaps']=='','reuse-teardown')
  if name.endswith('failure') or name=='no-progress':
   reason={'no-progress':'Cache budget unresolved after bounded passes','mincore-failure':'Cache residency unavailable','advice-failure':'Targeted mapping advice failed'}[name]
   e=next(x for x in events if x['operation']==name);need(e['outcome']=='refused' and e['reason']==reason,'cache-refusal')
   lines=[json.loads(l) for l in run['stdout'].splitlines() if l.startswith('{')];failure=next(x for x in lines if x.get('expected_refusal')==name);c=failure['cache']
   need(c['failed'] and c['error']==reason==failure['reason'],'cache-error')
   need(run['start_ns']<=c['start_ns']<c['end_ns']<=run['end_ns'],'cache-failure-time')

  from semantic import reuse_snapshots
  reuse_snapshots(run,r['inputs']['retain'],name,events)
  summary[name]={'trace_records':len(events),'exit':run['exit']}
 return summary

def mutation_packet(original, changed):
 """Lossless structural delta; reconstructed bytes must equal the mutant."""
 edits=[]
 def walk(a,b,path):
  if type(a)!=type(b):edits.append({'path':path,'value':b});return
  if isinstance(a,dict):
   for k in sorted(set(a)-set(b)):edits.append({'path':path+[k],'delete':True})
   for k in sorted(b):
    if k not in a:edits.append({'path':path+[k],'value':b[k]})
    else:walk(a[k],b[k],path+[k])
  elif isinstance(a,list) and len(a)==len(b):
   for i,(x,y) in enumerate(zip(a,b)):walk(x,y,path+[i])
  elif a!=b:edits.append({'path':path,'value':b})
 walk(original,changed,[]);rebuilt=copy.deepcopy(original)
 for edit in edits:
  parent=rebuilt
  for key in edit['path'][:-1]:parent=parent[key]
  key=edit['path'][-1]
  if edit.get('delete'):del parent[key]
  else:parent[key]=edit['value']
 need(rebuilt==changed,'delta-roundtrip')
 raw=json.dumps(edits,sort_keys=True).encode()
 return {'format':'structural-delta-v1','base_sha256':hashlib.sha256(json.dumps(original,sort_keys=True).encode()).hexdigest(),'patch_gzip_base64':base64.b64encode(gzip.compress(raw,compresslevel=1,mtime=0)).decode(),'reconstructed_sha256':hashlib.sha256(json.dumps(rebuilt,sort_keys=True).encode()).hexdigest()}

def mutations(r):
 """Rebind envelopes for semantic tests; never alter original actual receipts."""
 outcomes=[]
 cases=['pid','startticks','namespace','source','executable','hash','inode','readonly','mount','refusal','reason','phase','teardown','aggregate','swap','reap','exit','deadline','syscall','missing','missing-mapping','false-owner','junk-mapping','short-mapping','shifted-mapping','positive-count','missing-envelope','envelope']
 for case in cases:
  validate_aux(r)
  b=copy.deepcopy(r);p=b['lifecycle'];run=p['run'];target=next(k for k in run['observations'] if '-trace-' in k);events=[json.loads(l) for l in run['observations'][target].splitlines()]
  owned=next(e for e in events if e['owner_present']);refusal=next(e for e in events if e['outcome']=='refused')
  guard=None
  if case=='pid':run['samples'][0]['pid']+=1;guard='sample-pid'
  elif case=='startticks':run['startticks']+=1;guard='sample-startticks'
  elif case=='namespace':events[0]['namespaces']='pid:[0]';guard='trace-namespace'
  elif case=='source':p['pre']['source']={};guard='aux-source'
  elif case=='executable':p['pre']['executable']={};guard='aux-executable'
  elif case=='hash':p['post']['input']['sha256']='0'*64;guard='input-hash'
  elif case=='inode':owned['inode']+=1;guard='owner-inode'
  elif case=='readonly':owned['fdinfo']=re.sub(r'flags:\s+\d+','flags:\t0100002',owned['fdinfo']);guard='owner-readonly'
  elif case=='mount':owned['mountinfo']='';guard='owner-mount'
  elif case=='refusal':refusal['outcome']='unexpected-success';guard='refusal-outcome'
  elif case=='reason':refusal['reason']='Unrelated failure';guard='refusal-reason'
  elif case=='phase':events[2]['sequence']=999;guard='operation-sequence'
  elif case=='teardown':events[-1]['outcome']='missing';guard='teardown'
  elif case=='aggregate':run['samples'][0]['memory.current']='8053063680';guard='aggregate'
  elif case=='swap':run['samples'][0]['memory.swap.current']='4096';guard='swap'
  elif case=='reap':run['cleanup'][-1]['action']='UNREAPED';guard='reaped'
  elif case=='exit':run['exit']=1;guard='exit'
  elif case=='deadline':run['limits']['wall_seconds']=-10;guard='wall'
  elif case=='syscall':
   q=b['fault_controls']['run'];key=next(k for k,v in q['observations'].items() if '"operation":"seccomp"' in v)
   es=[json.loads(l) for l in q['observations'][key].splitlines()];es[-1]['reason']='Wrong exception';q['observations'][key]='\n'.join(json.dumps(e) for e in es)+'\n';guard='syscall-refusal'
  elif case=='missing':run['samples']=[];guard='live-required'
  elif case=='missing-mapping':
   next(e for e in events if e['operation']=='scalar-live-reader')['owned_smaps']='';guard='mapping-required'
  elif case=='false-owner':
   next(e for e in events if e['operation']=='scalar-live-reader')['owner_present']=False;guard='mapping-required'
  elif case=='junk-mapping':
   next(e for e in events if e['operation']=='scalar-live-reader')['owned_smaps']='junk';guard='mapping-header'
  elif case in ['short-mapping','shifted-mapping']:
   e=next(e for e in events if e['operation']=='scalar-live-reader');lines=e['owned_smaps'].splitlines();h=lines[0].split();a,z=h[0].split('-')
   if case=='short-mapping':h[0]=a+'-'+format(int(z,16)-4096,'x')
   else:h[2]='00001000'
   lines[0]=' '.join(h);e['owned_smaps']='\n'.join(lines)+'\n';guard='mapping-range'
  elif case=='positive-count':run['stdout']=run['stdout'].replace('"tokens":33','"tokens":32');guard='scalar-count'
  elif case=='missing-envelope' :run['raw_bytes'].pop(target);guard='envelope-coverage'
  elif case=='envelope':run['raw_bytes']['stdout.log']['sha256']='0'*64;guard='envelope-hash'
  if events!=[json.loads(l) for l in r['lifecycle']['run']['observations'][target].splitlines()]:
   run['observations'][target]='\n'.join(json.dumps(e) for e in events)+'\n'
  if case!='envelope':
   for name in ['lifecycle','fault_controls']:
    x=b[name]['run']
    for key in x['raw_bytes']:
     raw=(x['stdout'] if key=='stdout.log' else x['observations'][key]).encode()
     x['raw_bytes'][key]={'sha256':hashlib.sha256(raw).hexdigest(),'base64':base64.b64encode(raw).decode()}
  else:
   # Do not introduce a second accidental envelope change in the envelope test.
   run['observations'][target]=r['lifecycle']['run']['observations'][target]
  try:validate_aux(b)
  except Refused as e:
   need(str(e)==guard,'mutation-wrong-guard:'+case+':'+str(e))
   # Store exact mutations separately from actual raw packet, without duplicating
   # every untouched multi-megabyte sample for each one-field corruption.
   outcomes.append({'case':case,'expected_guard':guard,'actual_guard':str(e),'positive_revalidated':True,'kind':'envelope' if case=='envelope' else 'semantic','mutated_packet_sha256':hashlib.sha256(json.dumps(b,sort_keys=True).encode()).hexdigest(),'mutated_packet':mutation_packet(r,b)})
   continue
  raise Refused('mutation-accepted:'+case)
 return outcomes

def family_mutations(r):
 outcomes=[]
 for family in ['fault_controls','hung','read-error','no-progress','mincore-failure','advice-failure','tail','remap']:
  for case,guard in [('pid','sample-pid'),('reap','reaped'),('aggregate','aggregate')]:
   validate_aux(r)
   b=copy.deepcopy(r);x=b[family]['run'] if family in b else b['runs'][family]
   if case=='pid':x['samples'][0]['pid']+=1
   elif case=='reap':x['cleanup'][-1]['action']='MISSING'
   else:x['samples'][0]['memory.current']='8053063680'
   try:validate_aux(b)
   except Refused as e:
    need(str(e)==guard,'family-wrong-guard:'+family+':'+case+':'+str(e))
    data=json.dumps(b,sort_keys=True).encode()
    outcomes.append({'family':family,'case':case,'expected_guard':guard,'actual_guard':str(e),'positive_revalidated':True,'mutated_packet_sha256':hashlib.sha256(data).hexdigest(),'mutated_packet':mutation_packet(r,b)});continue
   raise Refused('family-mutation-accepted:'+family+':'+case)
 return outcomes
