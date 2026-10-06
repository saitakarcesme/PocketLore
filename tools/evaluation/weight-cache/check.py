"""Independent original-byte, live-kernel and budget receipt validation."""
import json,pathlib,base64,hashlib,copy,re,importlib.util,time
from common import R,O,SOURCES,BINARIES,source_check,sha,identity,sample_identity,process_stat,status_pid,atomic

def validate(r,current=True):
 f=r['frozen'];assert not r['errors'] and set(f['source'])==set(SOURCES) and set(f['binary'])==set(BINARIES)
 if current:
  source_check(f['source'])
  for p,v in f['binary'].items():assert sha(R/p)==v['sha256'],p
  manifest=pathlib.Path(f['source_path']).parent/'native-manifest.json';assert sha(manifest)==f['derivation']['sha256']
  for p,h in json.loads(manifest.read_text())['files'].items():assert sha(pathlib.Path(f['source_path'])/p)==h
 k=f['kernel'];assert 0<int(k['memory.max'])<=9663676416 and int(k['memory.swap.max'])==0 and int(k['pids.max'])<=512
 q,period=map(int,k['cpu.max'].split());assert 0<q<=period*2 and len(k['affinity_cpus'])<=4
 assert set(r['inputs'])=={'force','retain'} and r['inputs']['force']['sha256']==r['inputs']['retain']['sha256']
 assert set(r['runs'])=={'force','retain','no-progress','mincore-failure','advice-failure','tail','remap'}
 assert len(r['collection_control']['collection_errors'])==2 and r['collection_control']['raw_bytes']['stdout.log']['base64']=='/wA='
 metrics={}
 for name,run in r['runs'].items():
  inp=r['inputs']['force' if name=='force' else 'retain'];assert run['exit']==0 and not run.get('failure') and not run.get('cleanup_failure') and not run['collection_errors']
  assert run['post_source']==f['source'] and run['post_input']==inp['version'] and run['executable_before']==run['executable_after']==f['binary'][BINARIES[-1]]
  assert run['cleanup'][-1]['action']=='REAPED' and run['samples']
  assert int(re.search(r'^Pid:\s+(\d+)',run['pidfd_fdinfo'],re.M)[1])==run['pid']
  ns=run['samples'][0]['namespaces'];last=run['start_ns']
  for s in run['samples']:
   sample_identity(s,run['pid'],run['startticks'],ns);assert int(s['memory.swap.current'])==0 and last<=s['monotonic_ns']<=run['end_ns'];last=s['monotonic_ns']
  for n,v in run['raw_bytes'].items():
   b=base64.b64decode(v['base64'],validate=True);assert hashlib.sha256(b).hexdigest()==v['sha256']
   assert b.decode()==(run[n[:-4]] if n in ['stdout.log','stderr.log'] else run['observations'][n])
  lines=[json.loads(x) for x in run['stdout'].splitlines() if x.startswith('{')]
  if name=='remap':
   a=next(x for x in lines if 'before_remap' in x);b=next(x for x in lines if 'remapped' in x);assert a['before_remap']['cursor']>0 and b['cache']['cursor']==0 and b['remapped']['regions'][0]['bytes']==4194304 and not b['cache']['failed']
   continue
  if name=='tail':
   t=next(x for x in lines if 'tail_bytes' in x);assert t['tail_bytes']==33553376 and not t['cache']['failed'] and t['cache']['after_bytes']<=8388608
   a=json.loads(run['observations']['tail-tail.json']);assert len(a['cached_pages'])*4096==t['cache']['after_bytes'] and a['owner']['regions'][0]['bytes']==33553376
   continue
  if name not in ['force','retain']:
   failure=next(x for x in lines if x.get('expected_refusal')==name);assert failure['cache']['failed'] and failure['cache']['error']
   if name=='no-progress':assert failure['cache']['after_bytes']>8388608 and failure['cache']['advice_calls']<=64 and 'bounded passes' in failure['reason']
   continue
  metrics[name]=[]
  def snapshot(n):
   x=json.loads(run['observations'][n]);a=x['owner'];pages=x['cached_pages']
   assert pages==sorted(set(pages)) and all(0<=p<8192 for p in pages)
   assert a['pid']==run['pid']==status_pid(a['status'])==process_stat(x['stat'])[0] and int(a['startticks'])==run['startticks']==process_stat(x['stat'])[1]
   assert a['namespaces']==''.join(ns[n] for n in ['mnt','pid','user']) and run['start_ns']<a['monotonic_ns']<run['end_ns']
   assert a['sha256']==inp['sha256'] and a['inode']==inp['version']['inode'] and a['bytes']==33554432 and a['stat_device']==inp['version']['device']
   assert a['fault_policy']=='random' and a['dedicated_description'] and a['file_policy_result']==a['mapping_policy_result']==0
   assert len(a['regions'])==1 and a['regions'][0]['cache_present_pages']==len(pages) and a['regions'][0]['bytes']==33554432
   reg=a['regions'][0];device=tuple(map(int,a['mount'].split()[2].split(':')))
   headers=[re.match(r'^([0-9a-f]+)-([0-9a-f]+) (\S+) ([0-9a-f]+) ([0-9a-f]+):([0-9a-f]+) (\d+)',l) for l in a['smaps'].splitlines()]
   h=next(h for h in headers if h and int(h[1],16)==reg['address'])
   assert int(h[2],16)==reg['address']+33554432 and h[3]=='r--s' and int(h[4],16)==0 and (int(h[5],16),int(h[6],16))==device and int(h[7])==a['inode']
   return x
  assert not snapshot(name+'-cold.json')['cached_pages']
  for i,phase in enumerate(f['policy']['phases']):
   line=next(x for x in lines if x.get('step')==i);assert line['offset']==phase['start'] and line['bytes']==phase['bytes'] and line['sum']==phase['bytes']//256*32640
   before,touched,after=[snapshot(f'{name}-{i}-{p}.json') for p in ['before','touched','after']]
   assert before['owner']['monotonic_ns']<line['start_ns']<touched['owner']['monotonic_ns']<line['end_ns']<after['owner']['monotonic_ns']
   bstat=before['stat'][before['stat'].rfind(')')+2:].split();astat=after['stat'][after['stat'].rfind(')')+2:].split()
   assert 0<=line['major_faults']<=int(astat[9])-int(bstat[9]) and 0<=line['minor_faults']<=int(astat[7])-int(bstat[7])
   assert line['cpu_us']>=0
   c=after['cache'];assert not c['failed'] and c['before_bytes']==len(touched['cached_pages'])*4096 and c['after_bytes']==len(after['cached_pages'])*4096 and c['start_ns']>touched['owner']['monotonic_ns'] and c['end_ns']<line['end_ns']
   assert c['observed_evicted_bytes']==max(0,c['before_bytes']-c['after_bytes']) and c['chunk_bytes']==1048576 and 0<=c['cursor']<32
   if name=='retain':
    assert 0<c['end_ns']-c['start_ns']<5000000000
    assert c['policy']=='budgeted-cyclic-v1' and c['budget_bytes']==8388608 and c['after_bytes']<=8388608 and c['advice_calls']<=64
    if i in [0,1]:assert c['advice_calls']==0 and c['after_bytes']==4194304
    if i in [2,4]:assert c['advice_calls']>0 and c['before_bytes']>8388608 and c['after_bytes']<c['before_bytes']
   else:assert c['policy']=='force-drop' and c['budget_bytes']==0 and c['after_bytes']==0
   metrics[name].append({'phase':phase['name'],'cache':c,'native_access':line,'before_cached':len(before['cached_pages']),'after_cached':len(after['cached_pages'])})
  assert any(x.get('released') and x['owner']['regions']==[] for x in lines)
 assert metrics['retain'][1]['before_cached']==1024 and metrics['force'][1]['before_cached']==0
 assert metrics['retain'][4]['cache']['cursor']!=metrics['retain'][5]['cache']['cursor']
 for key in ['wrong-inode','wrong-hash','wrong-size','unaligned','partial-map','deadline','cancelled','async-reader','alias-mapping','deferred-destructor-observation','scalar-exception']:assert key in r['lifecycle']['stdout']
 for key in ['fadvise-kernel-failure','madvise-kernel-failure','double-owner','writable-inherited','dedicated-reuse-offset']:assert key in r['fault_controls']['stdout']
 for n in ['hung','read-error']:assert r[n]['cleanup'][-1]['action']=='REAPED'
 return metrics

def main():
 p={'status':'FAIL','errors':[],'files':{},'model_access':False,'android_execution':False}
 for file in [O/'runs.json',O/'frozen.json',O/'attempt.json']+sorted((O/'logs').glob('*')):
  try:
   b=file.read_bytes();p['files'][str(file.relative_to(R))]={'sha256':hashlib.sha256(b).hexdigest(),'base64':base64.b64encode(b).decode()}
  except Exception as e:p['errors'].append(repr(e))
 try:
  r=json.loads((O/'runs.json').read_text());p['execution']=r;p['measurements']=validate(r)
  spec=importlib.util.spec_from_file_location('linked_native',R/'tools/evaluation/native-cache/check.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);p['linked']=m.artifacts(r['frozen']['source_path'])
  from contract import elf_machine
  assert elf_machine(R/BINARIES[-1])==62;p['new_executable']=identity(R/BINARIES[-1])
  negatives=[]
  for n in ['source','binary','pid','startticks','budget','mincore','byte','failed','missing','policy','namespace','mount','stat']:
   b=copy.deepcopy(r);run=b['runs']['retain']
   if n=='source':b['frozen']['source']={}
   elif n=='binary':b['frozen']['binary'][BINARIES[-1]]['sha256']='0'*64
   elif n=='pid':run['pid']+=1
   elif n=='startticks':run['startticks']+=1
   elif n=='namespace':run['samples'][0]['namespaces']['pid']='pid:[0]'
   elif n=='stat':run['post_input']['inode']+=1
   elif n=='missing':run['observations'].pop('retain-1-after.json')
   elif n=='byte':run['stdout']=run['stdout'].replace('"bytes":4194304','"bytes":1')
   else:
    x=json.loads(run['observations']['retain-1-after.json'])
    if n=='budget':x['cache']['budget_bytes']=999999999
    elif n=='mincore':x['cached_pages']=[]
    elif n=='policy':x['owner']['fault_policy']='default'
    elif n=='mount':x['owner']['mount']=x['owner']['mount'].replace(x['owner']['mount'].split()[2],'0:999',1)
    else:x['cache']['failed']=True
    run['observations']['retain-1-after.json']=json.dumps(x)
   # Rebind altered raw bytes so semantic guards, not only serialization
   # mismatch, must reject these engineered corrupted observations.
   for key in list(run['raw_bytes']):
    if key in ['stdout.log','stderr.log']:text=run[key[:-4]]
    elif key in run['observations']:text=run['observations'][key]
    else:continue
    data=text.encode();run['raw_bytes'][key]={'sha256':hashlib.sha256(data).hexdigest(),'base64':base64.b64encode(data).decode()}
   try:validate(b)
   except Exception as e:negatives.append({'name':n,'refused':True,'error':repr(e)});continue
   raise AssertionError('Mutation passed '+n)
  p['negative_controls']=negatives;assert not p['errors'];p['status']='PASS_BOUNDED_SYNTHETIC_REUSE_ONLY'
 except Exception as e:p['errors'].append(type(e).__name__+': '+str(e))
 finally:p['exit']=int(bool(p['errors']));p['stdout']=p['status']+'\n';atomic(O/'check.json',p);atomic(R/'docs/evidence/weight-cache-reuse-review.json',p);print(p['stdout'],end='')
 return p['exit']
if __name__=='__main__':raise SystemExit(main())
