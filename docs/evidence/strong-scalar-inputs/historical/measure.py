"""Summarize actual live samples even when generation fails; never upgrade the gate."""
import json,pathlib,re,sys
from validate import residency
p=pathlib.Path(sys.argv[1]);r=json.loads(p.read_text());result={'scope':'Live host samples; anonymous includes unattributed private allocations, not an exact transformed-buffer attribution','cases':[]}
for case in r['cases']:
 rows=[];samples=[];ticks=None
 for s in case['samples']:
  a=int(s['stat_before'].rsplit(')',1)[1].split()[19]);b=int(s['stat_after'].rsplit(')',1)[1].split()[19]);assert a==b and (ticks is None or a==ticks);ticks=a
  hwm=int(re.search(r'^VmHWM:\s+(\d+) kB$',s['status'],re.M)[1])*1024
  m=residency.parse_smaps(s['smaps'],r['model']['device'],r['model']['inode']);rows.append(dict(phase=s['phase'],monotonic_ns=s['monotonic_ns'],**m,hwm_bytes=hwm,cgroup_current=int(s['kernel']['memory.current']),cgroup_peak=int(s['kernel']['memory.peak'])))
  samples.append(dict(s,startticks=a,hwm_bytes=hwm,model_device=r['model']['device'],model_inode=r['model']['inode']))
 try:window=residency.validate_window(samples,samples[0]['monotonic_ns'],samples[-1]['monotonic_ns'],case['pid'],ticks,r['model'])
 except ValueError as e:window={'qualified':False,'error':str(e),'limitation':'Captured stat device and smaps device differ; model-page attribution is unresolved, not zero residency'}
 result['cases'].append({'pid':case['pid'],'startticks':ticks,'samples':rows,'loaded_window':window,'exit':case['exit'],'stop':case['stopped_reason'],'generated_output_bytes':len(case['stdout'].encode())})
print(json.dumps(result,indent=2))
