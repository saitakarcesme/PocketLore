"""Independent raw process, scalar sequence and owned mapping receipt checks."""
import re,json,hashlib,pathlib
from support import R,O,SOURCES,BINARIES,sha,identity,source_check,process_stat,status_pid,sample_identity
SHA='96b9c0af5c77a4ecaabe3983175112b5ece763261c1ece12b2494b692a70dad7'
def mapping(a):
 assert a['sha256']==SHA and a['bytes']==12290628576 and len(a['regions'])==1
 region=a['regions'][0];assert region['bytes']==12290628576 and region['offset']==0
 device=tuple(map(int,a['mount'].split()[2].split(':')));cursor=region['address'];end=cursor+(region['bytes']+4095)//4096*4096;rss=0
 for line in a['smaps'].splitlines():
  m=re.match(r'^([0-9a-f]+)-([0-9a-f]+) (\S+) ([0-9a-f]+) ([0-9a-f]+):([0-9a-f]+) (\d+)',line)
  if m:
   lo,hi=int(m[1],16),int(m[2],16)
   if hi<=region['address'] or lo>=end:continue
   assert lo==cursor and hi<=end and m[3]=='r--s' and int(m[4],16)==lo-region['address'] and (int(m[5],16),int(m[6],16))==device and int(m[7])==a['inode']
   cursor=hi
 assert cursor==end,'Incomplete authoritative owned mapping'
 return True

def preflight_valid(p):
 k=p['kernel'];assert 0<int(k['memory.max'])<=9663676416 and int(k['memory.swap.max'])==0 and int(k['pids.max'])<=512
 quota,period=map(int,k['cpu.max'].split());assert 0<quota<=2*period and len(p['affinity'])<=4
 assert int(next(l.split()[1] for l in p['meminfo'].splitlines() if l.startswith('MemAvailable:')))*1024>=11*1024**3
 assert int(k['memory.current'])<8053063680

def phase_chronology(observations,start,end):
 names=['verified','loaded','prefill','generation','completed','unmapped']
 assert set(observations)==set(names)
 previous=start
 for name in names:
  value=observations[name];assert previous<value<end;previous=value
 return True

def cpu_sample(raw,ticks):
 assert isinstance(ticks,int) and ticks>0
 fields=raw[raw.rfind(')')+2:].split();assert (int(fields[11])+int(fields[12]))/ticks<=160
 return True

def validate_case(c,f):
 preflight_valid(c['preflight'])
 assert c.get('exit')==0 and not any(c.get(k) for k in ['failure','cleanup_failure','post_identity_failure','collection_errors']),c.get('failure') or c.get('exit')
 assert c['binary_before']==c['binary_after']==f['binary'][BINARIES[1]]
 assert c['post_source']==f['source'] and c['model_before']==c['model_after']==c['parent_fd']['stat']
 assert c['model_before']['size']==12290628576
 assert c['prompt']['sha256']==f['policy']['probes'][c['number']-1]
 assert hashlib.sha256(c['prompt']['text'].encode()).hexdigest()==c['prompt']['sha256']
 assert c['cleanup'][-1]['action']=='REAPED' and c['cleanup'][-1]['exit']==0
 assert int(re.search(r'^Pid:\s+(\d+)',c['pidfd_fdinfo'],re.M)[1])==c['pid']
 assert 0<c['end_ns']-c['start_ns']<=180_000_000_000
 text=c['stderr'];n=re.search(r'PREFILL_TOKENS (\d+)',text);g=re.search(r'POCKETLORE_TOKENS (\d+) EOG ([01])',text)
 assert n and g and 0<int(n[1])<=850 and 0<int(g[1])<=128 and g[2]=='1' and c['stdout'].strip(),'Missing or incomplete generated output'
 begins=re.findall(r'^SCALAR_BEGIN (\d+) (\d+)$',text,re.M);ends=re.findall(r'^SCALAR_END (\d+) (\d+)$',text,re.M)
 count=int(n[1])+int(g[1]);assert begins==[(str(i),'1') for i in range(count)] and ends==[(str(i),'0') for i in range(count)]
 for phase in ['identity_hash','loading','loaded','prefill','generation','completed_hold','context_released','model_released','backend_released','released_after_scope']:assert 'POCKETLORE_PHASE '+phase in text,phase
 previous=0;ns=c['samples'][0]['namespaces'];group=c['samples'][0]['cgroup']
 for s in c['samples']:
  cpu_sample(s['stat'],c['clock_ticks'])
  limits=re.search(r'^Max cpu time\s+(\d+)\s+(\d+)\s+seconds',s['limits'],re.M);assert limits and limits.groups()==('150','160')
  sample_identity(s,c['pid'],c['startticks'],ns);assert s['cgroup']==group and c['start_ns']<=s['monotonic_ns']<=c['end_ns'] and s['monotonic_ns']>previous;previous=s['monotonic_ns'];assert int(s['memory.swap.current'])==0
 phase_chronology({n:json.loads(c['raw'][n+'.json'])['monotonic_ns'] for n in ['verified','loaded','prefill','generation','completed','unmapped']},c['start_ns'],c['end_ns'])
 phase_time=c['start_ns']
 for name in ['verified','loaded','prefill','generation','completed','unmapped']:
  a=json.loads(c['raw'][name+'.json']);assert a['pid']==c['pid'] and int(a['startticks'])==c['startticks'] and a['sha256']==SHA and a['inode']==c['model_before']['inode'] and a['stat_device']==c['model_before']['device']
  assert a['namespaces']==''.join(ns[x] for x in ['mnt','pid','user']) and c['start_ns']<a['monotonic_ns']<c['end_ns']
  assert a['monotonic_ns']>phase_time;phase_time=a['monotonic_ns']
  assert status_pid(a['status'])==c['pid']
  if name in ['verified','unmapped']:assert a['regions']==[]
  else:mapping(a)
 assert any(s['phase']=='loaded' for s in c['samples']) and any(s['phase']=='completed_hold' for s in c['samples'])
 return {'tokens':int(g[1]),'prefill_tokens':int(n[1]),'elapsed_seconds':(c['end_ns']-c['start_ns'])/1e9,'aggregate_sample_max':max(int(s['memory.current']) for s in c['samples'])}
def validate(r):
 source_check(r['frozen']['source']);preflight_valid(r['frozen']['kernel'])
 f=r['frozen'];assert f['policy']==json.loads(f['source']['docs/evidence/strong-scalar-inputs/route.json']['text'])
 for p,v in f['configuration'].items():assert sha(R/p)==v['sha256']
 manifest=pathlib.Path(f['source_path']).parent/'native-manifest.json';assert sha(manifest)==f['derivation']['sha256']
 for p,h in json.loads(manifest.read_text())['files'].items():assert sha(pathlib.Path(f['source_path'])/p)==h
 assert not r['errors'] and not r['not_run'] and len(r['cases'])==2,'Incomplete screen'
 for p,v in r['frozen']['binary'].items():assert sha(R/p)==v['sha256'],p
 return [validate_case(c,r['frozen']) for c in r['cases']]
