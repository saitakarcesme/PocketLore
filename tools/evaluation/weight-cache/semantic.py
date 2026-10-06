"""Three task539 contracts; no execution or model access."""
import re,json
from auxiliary import need
from common import process_stat,status_pid
EVENT_KEYS={'low','high','max','oom','oom_kill','oom_group_kill','sock_throttled'}
FAILURE_KEYS={'high','max','oom','oom_kill','oom_group_kill'}
def events(raw):
 need(isinstance(raw,str),'events-format');out={}
 for line in raw.splitlines():
  m=re.fullmatch(r'([a-z_]+) ([0-9]+)',line)
  need(m is not None,'events-format');key,value=m.groups()
  need(key in EVENT_KEYS and key not in out,'events-keys');out[key]=int(value)
 need(set(out)==EVENT_KEYS,'events-keys');return out

def resource_contract(run):
 need(run.get('event_contract')=='no-new-memory-failure-v1','events-contract')
 need('kernel_before' in run and 'kernel_after' in run,'events-boundaries')
 first,last=run['kernel_before'],run['kernel_after'];identity=first.get('group_identity')
 need(isinstance(identity,dict) and set(identity)=={'path','device','inode','raw_cgroup'} and identity['inode']>0,'events-cgroup')
 need(identity['path']=='/sys/fs/cgroup'+identity['raw_cgroup'].split('0::')[1].strip(),'events-cgroup')
 previous=events(first.get('memory.events'));baseline=previous.copy();clock=first['observed_ns']
 samples=run['samples']+[last]
 for s in samples:
  need(s.get('group_identity')==identity,'events-cgroup')
  if 'cgroup' in s:need(s['cgroup']==identity['raw_cgroup'],'events-cgroup')
  observed=s.get('kernel_observed_ns',s.get('observed_ns'));need(type(observed)==int and observed>=clock,'events-chronology');clock=observed
  current=events(s.get('memory.events'))
  # Check new failures before monotonicity so the exact one-sample oom_kill
  # contradiction reaches its own resource guard, not its later decrease.
  need(all(current[k]==baseline[k] for k in FAILURE_KEYS),'events-new-failure')
  need(all(current[k]>=previous[k] for k in EVENT_KEYS),'events-monotonic');previous=current
 need(run['start_ns']<=first['observed_ns']<=run['samples'][0]['kernel_observed_ns'],'events-chronology')
 need(last['observed_ns']>=run['end_ns'],'events-chronology')

def verified_phase(entries):
 matches=[i for i,e in enumerate(entries) if e.get('operation')=='verified']
 need(len(matches)==1,'verified-required')
 need(matches==[1] and entries[0]['operation']=='process' and entries[0]['outcome']=='begin','verified-order')
 e=entries[1];need(e.get('outcome')=='complete' and e.get('owner_present') is True and isinstance(e.get('verified_owner'),dict),'verified-state')
 need(e['verified_owner'].get('regions')==[],'verified-state')
 return e

def snapshot(x,run,inp,n,verified):
 need(isinstance(x,dict) and 'owner' in x and 'stat' in x and 'cached_pages' in x,'snapshot-required')
 a=x['owner'];pages=x['cached_pages'];count=(n+4095)//4096
 need(isinstance(pages,list) and all(type(p)==int for p in pages),'pages-type')
 need(pages==sorted(set(pages)),'pages-unique')
 need(all(0<=p<count for p in pages),'pages-range')
 need(a['pid']==run['pid']==status_pid(a['status'])==process_stat(x['stat'])[0] and int(a['startticks'])==run['startticks']==process_stat(x['stat'])[1],'snapshot-pid')
 v=inp['version'];need(a['sha256']==inp['sha256'] and a['inode']==v['inode'] and a['stat_device']==v['device'] and a['bytes']==v['size'],'snapshot-source')
 for field in ['fd','mount','fdinfo','namespaces','sha256','inode','stat_device','bytes']:
  need(a[field]==verified['verified_owner'][field],'snapshot-owner')
 need(a['fault_policy']=='random' and a['dedicated_description'] is True and a['file_policy_result']==a['mapping_policy_result']==0,'snapshot-policy')
 need(len(a['regions'])==1,'snapshot-region');reg=a['regions'][0]
 need(reg['bytes']==n and reg['offset']==0 and reg['page_size']==4096 and reg['address']>0 and reg['address']%4096==0,'snapshot-range')
 need(reg['cache_present_pages']==len(pages),'pages-cardinality')
 need(int(re.search(r'^flags:\s+(\d+)',a['fdinfo'],re.M)[1],8)&3==0,'snapshot-readonly')
 mount=a['mount'].split();mid=re.search(r'^mnt_id:\s+(\d+)',a['fdinfo'],re.M)[1];need(mid==mount[0],'snapshot-mount')
 dev=tuple(map(int,mount[2].split(':')));headers=[]
 for block in re.split(r'(?=^[0-9a-f]+-[0-9a-f]+ )',a['smaps'],flags=re.M):
  m=re.match(r'^([0-9a-f]+)-([0-9a-f]+) (\S+) ([0-9a-f]+) ([0-9a-f]+):([0-9a-f]+) (\d+)',block)
  if not m or int(m[1],16)!=reg['address']:continue
  need(int(m[2],16)==reg['address']+count*4096 and m[3]=='r--s' and int(m[4],16)==0,'snapshot-vma')
  need((int(m[5],16),int(m[6],16))==dev and int(m[7])==v['inode'],'snapshot-vma')
  fields={k:int(value)*1024 for k,value in re.findall(r'^(Rss|Pss|Private_Dirty|Anonymous|Swap):\s+(\d+) kB$',block,re.M)}
  need(set(fields)=={'Rss','Pss','Private_Dirty','Anonymous','Swap'},'snapshot-residency')
  need(0<=fields['Pss']<=fields['Rss']<=len(pages)*4096 and fields['Private_Dirty']==fields['Anonymous']==fields['Swap']==0,'snapshot-residency');headers.append(m)
 need(len(headers)==1,'snapshot-vma')
 return a['monotonic_ns']

def reuse_snapshots(run,inp,name,entries):
 verified=verified_phase(entries)
 need(all(e.get('owner_present') is True for e in entries[1:]),'reuse-owner-lifetime')
 need(entries[-1]['operation']=='teardown' and entries[-1]['outcome']=='complete' and entries[-1]['owned_smaps']=='','reuse-teardown')
 specs=[('cold',33553376 if name=='tail' else 33554432)]
 if name=='tail':specs.append(('tail',33553376))
 elif name=='remap':specs.extend([('remap-old',33554432),('remap-new',4194304)])
 else:specs.append(('before-injection',33554432))
 prior=verified['monotonic_ns'];snapshots=[]
 for suffix,n in specs:
  key=name+'-'+suffix+'.json';need(key in run['observations'],'snapshot-required');x=json.loads(run['observations'][key])
  now=snapshot(x,run,inp,n,verified);need(prior<now<entries[-1]['monotonic_ns'],'snapshot-chronology');prior=now;snapshots.append(x)
 need(not snapshots[0]['cached_pages'],'snapshot-cold')
 if name not in ['tail','remap']:
  need(set(range(4096))<=set(snapshots[1]['cached_pages']),'pressure-observed')
  injection=next(e for e in entries if e['operation']=='seccomp');need(prior<injection['monotonic_ns'],'snapshot-chronology')
 else:
  for x in snapshots[1:]:
   c=x['cache'];need(not c['failed'] and c['policy']=='budgeted-cyclic-v1' and c['budget_bytes']==8388608 and c['after_bytes']==len(x['cached_pages'])*4096<=8388608,'snapshot-budget')
   need(verified['monotonic_ns']<c['start_ns']<c['end_ns']<x['owner']['monotonic_ns'],'snapshot-cache-time')
  if name=='remap':
   old,new=snapshots[1:];need(old['cache']['cursor']>0 and new['cache']['cursor']==0,'remap-cursor')
   lines=[json.loads(l) for l in run['stdout'].splitlines() if l.startswith('{')]
   a=next(x for x in lines if 'before_remap' in x);b=next(x for x in lines if 'remapped' in x)
   need(a['before_remap']==old['cache'] and b['cache']==new['cache'],'remap-cache-binding')
   extra={'owner':b['remapped'],'stat':new['stat'],'cached_pages':new['cached_pages']};now=snapshot(extra,run,inp,4194304,verified)
   need(prior<=now<entries[-1]['monotonic_ns'],'snapshot-chronology')
