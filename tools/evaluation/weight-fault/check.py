"""Discriminating cold native policy receipts; no model/device qualification."""
import base64,copy,hashlib,importlib.util,json,pathlib,re,time
from common import R,O,SOURCES,BINARIES,identity,sha,verify_sources,process_stat,status_pid,sample_identity,atomic

def validate(r,current=True):
 f=r['frozen'];assert not r['errors'] and set(r['runs'])=={'default','random','negative'}
 if current:verify_sources(f['source'])
 assert set(f['source'])==set(SOURCES) and set(f['binary'])==set(BINARIES)
 for p,v in f['binary'].items():
  if current:assert sha(R/p)==v['sha256']
 assert len(f['inputs'])==2 and sum(v['bytes'] for v in f['inputs'].values())<=268435456
 assert f['inputs']['default']['sha256']==f['inputs']['random']['sha256']
 touched=set(f['policy']['access_pages']);assert len(touched)==16
 results={}
 for name,run in r['runs'].items():
  assert run['exit']==0 and not run.get('failure') and not run.get('cleanup_failure') and run['post_source']==f['source']
  assert run['executable_before']==run['executable_after']==f['binary']['downloads/native-cache-build/host/fault-policy-controls']
  assert run['cleanup'][-1]['action']=='REAPED' and run['cleanup'][-1]['exit']==0 and run['samples']
  assert int(re.search(r'^Pid:\s+(\d+)',run['pidfd_fdinfo'],re.M)[1])==run['pid']
  ns=run['samples'][0]['namespaces'];last=run['start_ns']
  for s in run['samples']:
   sample_identity(s,run['pid'],run['startticks'],ns);assert last<=s['monotonic_ns']<=run['end_ns'];last=s['monotonic_ns']
  if name=='negative':
   for expected in ['fadvise-kernel-failure','madvise-kernel-failure','double-owner','writable-inherited','live-reader-advice','alias','cancel','exception-release','hash','deadline','dedicated-reuse-offset']:assert expected in run['stdout'],expected
   continue
  results[name]=[]
  lines=[json.loads(l) for l in run['stdout'].splitlines() if l.startswith('{')]
  for rnd in range(2):
   outcome=next(x for x in lines if x.get('round')==rnd);assert outcome['bytes_compared']==65536 and outcome['post_advice_matches']==16
   expected_sum=sum(((i*73)^(i>>8)^(i>>16))&255 for page in touched for i in range(page*4096,(page+1)*4096));assert outcome['sum']==expected_sum
   observations=[];previous=run['start_ns']
   for phase in ['cold','touched','released']:
    o=json.loads(run['observations'][f'{name}-{rnd}-{phase}.json']);a=o['owner'];assert a['pid']==run['pid']==status_pid(a['status']) and int(a['startticks'])==run['startticks']
    assert previous<a['monotonic_ns']<run['end_ns'];previous=a['monotonic_ns']
    assert a['sha256']==f['inputs'][name]['sha256'] and a['inode']==f['inputs'][name]['version']['inode'] and a['bytes']==67108864
    assert a['namespaces']==''.join(ns[n] for n in ['mnt','pid','user']) and a['fault_policy']==name
    assert a['dedicated_description']==(name=='random') and a['file_policy_result']==(0 if name=='random' else -1) and a['mapping_policy_result']==(0 if name=='random' else -1)
    region=a['regions'][0];assert len(a['regions'])==1 and region['bytes']==67108864 and region['offset']==0
    cached=o['cached_pages'];assert cached==sorted(set(cached)) and all(0<=x<16384 for x in cached) and len(cached)==region['cache_present_pages']
    # Independently bind readonly exact VMA to the namespace-local mount device.
    device=tuple(map(int,a['mount'].split()[2].split(':')));lo=region['address'];hi=lo+region['bytes'];bound=False
    for line in a['smaps'].splitlines():
     m=re.match(r'^([0-9a-f]+)-([0-9a-f]+) (\S+) ([0-9a-f]+) ([0-9a-f]+):([0-9a-f]+) (\d+)',line)
     if m and int(m[1],16)==lo:
      assert int(m[2],16)==hi and m[3]=='r--s' and int(m[4],16)==0 and (int(m[5],16),int(m[6],16))==device and int(m[7])==a['inode'];bound=True
    assert bound
    if phase=='cold':assert cached==[],'Comparison did not start cold'
    if phase=='touched':assert touched<=set(cached)
    observations.append(o)
   cached=set(observations[1]['cached_pages']);results[name].append({'cached_pages':len(cached),'touched_pages':16,'untouched_pages':len(cached-touched),'adjacent_untouched':sum(p+d in cached-touched for p in touched for d in [-1,1]),'released_pages':len(observations[2]['cached_pages'])})
 for i in range(2):assert results['random'][i]['untouched_pages']<results['default'][i]['untouched_pages'],'No measured random-policy effect'
 return results

def main():
 packet={'status':'FAIL','errors':[],'model_access':False,'android_execution':False,'files':{},'start_ns':time.monotonic_ns()}
 for p in [O/'runs.json',O/'frozen.json',O/'controls.json']+sorted((O/'logs').glob('*')):
  try:
   if p.is_file():b=p.read_bytes();packet['files'][str(p.relative_to(R))]={'sha256':hashlib.sha256(b).hexdigest(),'base64':base64.b64encode(b).decode()}
  except Exception as e:packet['errors'].append(repr(e))
 try:
  actual=json.loads((O/'runs.json').read_text());packet['execution']=actual;packet['measurements']=validate(actual)
  control=json.loads((O/'controls.json').read_text());packet['controls']=control;assert control['status']=='PASS' and control['source']==actual['frozen']['source']
  spec=importlib.util.spec_from_file_location('native_artifacts',R/'tools/evaluation/native-cache/check.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);packet['linked']=m.artifacts(actual['frozen']['source_path'])
  assert sha(R/'downloads/native-cache-build/host/fault-policy-controls')==actual['frozen']['binary']['downloads/native-cache-build/host/fault-policy-controls']['sha256']
  mutations=[]
  for name in ['empty-source','binary','pid','startticks','cold','byte-oracle','policy-result','mount','missing-round','no-effect']:
   bad=copy.deepcopy(actual);run=bad['runs']['random']
   if name=='empty-source':bad['frozen']['source']={}
   elif name=='binary':bad['frozen']['binary'][BINARIES[0]]['sha256']='0'*64
   elif name=='pid':run['samples'][0]['pid']+=1
   elif name=='startticks':run['startticks']+=1
   elif name=='byte-oracle':run['stdout']=run['stdout'].replace('"bytes_compared":65536','"bytes_compared":1')
   elif name=='missing-round':run['observations'].pop('random-1-touched.json')
   else:
    key='random-0-'+('cold' if name=='cold' else 'touched')+'.json';o=json.loads(run['observations'][key])
    if name=='cold':o['cached_pages']=[17];o['owner']['regions'][0]['cache_present_pages']=1
    elif name=='policy-result':o['owner']['mapping_policy_result']=-1
    elif name=='mount':o['owner']['mount']=o['owner']['mount'].replace(o['owner']['mount'].split()[2],'0:999',1)
    else:o['cached_pages']=list(range(16384));o['owner']['regions'][0]['cache_present_pages']=16384
    run['observations'][key]=json.dumps(o)
   try:validate(bad)
   except Exception as e:mutations.append({'case':name,'refused':True,'error':repr(e)});continue
   raise AssertionError('Corrupt receipt passed '+name)
  packet['mutations']=mutations;assert not packet['errors'];packet['status']='PASS_SYNTHETIC_NATIVE_POLICY_ONLY'
 except Exception as e:packet['errors'].append(type(e).__name__+': '+str(e))
 finally:
  packet['finished_ns']=time.monotonic_ns();packet['exit']=int(bool(packet['errors']));packet['stdout']=packet['status']+'\n';atomic(O/'check.json',packet);atomic(R/'docs/evidence/weight-fault-policy-review.json',packet);print(packet['stdout'],end='')
 return packet['exit']
if __name__=='__main__':raise SystemExit(main())
