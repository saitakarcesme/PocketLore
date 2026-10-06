"""Discriminating actual host evidence validation; no semantic or device acceptance."""
import pathlib,hashlib,importlib.util,re,json
R=pathlib.Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('residency',R/'tools/runtime/sparse/residency.py');residency=importlib.util.module_from_spec(spec);spec.loader.exec_module(residency)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def validate(r):
 assert not r['errors'],'Execution failed'
 assert r['model']['bytes']==12290628576 and r['model']['sha256']=='96b9c0af5c77a4ecaabe3983175112b5ece763261c1ece12b2494b692a70dad7'
 assert r['binary_sha256']==sha(R/'downloads/strong-native-host/host-build/sparse-host'),'Changed executable'
 assert r['freeze_sha256']==sha(R/'docs/evidence/strong-native-host-fixtures/freeze.json'),'Changed freeze'
 for p,h in r['source_manifest'].items():assert sha(R/p)==h,'Changed executed source'
 assert len(r['cases'])==2,'Incomplete two-probe execution'
 results=[]
 for case in r['cases']:
  assert case['exit']==0 and not case['stopped_reason'] and case['stdout'].strip(),'Missing generation'
  n=re.search(r'POCKETLORE_TOKENS (\d+) EOG ([01])',case['stderr']);assert n and int(n[1])>0,'No actual tokens'
  assert 'POCKETLORE_PHASE generation' in case['stderr'] and 'POCKETLORE_PHASE released' in case['stderr']
  samples=[];ticks=None
  for s in case['samples']:
   a=int(s['stat_before'].rsplit(')',1)[1].split()[19]);b=int(s['stat_after'].rsplit(')',1)[1].split()[19]);assert a==b and (ticks is None or ticks==a);ticks=a
   hwm=int(re.search(r'^VmHWM:\s+(\d+) kB$',s['status'],re.M)[1])*1024
   assert int(s['kernel']['memory.current'])<=8053063680 and int(s['kernel']['memory.swap.current'])==0
   assert str(s['pid'])==str(case['pid']) and s['cgroup'].strip().endswith(r['preflight']['cgroup'].removeprefix('/sys/fs/cgroup'))
   samples.append(dict(s,pid=case['pid'],startticks=a,hwm_bytes=hwm,model_device=r['model']['device'],model_inode=r['model']['inode']))
  assert samples
  v=residency.validate_window(samples,samples[0]['monotonic_ns'],samples[-1]['monotonic_ns'],case['pid'],ticks,r['model']);v.update(tokens=int(n[1]),eog=bool(int(n[2])),elapsed_seconds=case['ended']-case['started']);results.append(v)
 k=r['preflight']['kernel'];assert 0<int(k['memory.max'])<=9663676416 and int(k['memory.swap.max'])==0
 quota,period=map(int,k['cpu.max'].split());assert quota<=4*period
 return results
