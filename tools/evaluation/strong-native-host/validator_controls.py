"""Current real native random policy and synthetic budget oracles; no model access."""
import copy,json,os,pathlib,sys
from support import R,O,BINARIES,identity,owned,atomic
from validate import resource_sample,policy_observation,phase_chronology

def execute(out):
 results=[];fixture=out/'random.bin'
 import hashlib
 h=hashlib.sha256()
 with fixture.open('xb') as f:
  for off in range(0,67108864,1048576):
   b=bytes(((i*73)^(i>>8)^(i>>16))&255 for i in range(off,off+1048576));f.write(b);h.update(b)
  f.flush();os.fsync(f.fileno())
 with fixture.open('rb') as f:os.posix_fadvise(f.fileno(),0,0,os.POSIX_FADV_DONTNEED)
 for kind in ['random','negative']:
  prefix=out/kind
  run=owned.execute([str(R/BINARIES[-1]),str(fixture),h.hexdigest(),kind,str(prefix)],out/(kind+'-run'),90)
  raw=(out/(kind+'-run')/'stdout.log').read_text();assert run['exit']==0 and not run.get('failure')
  observations={p.name:p.read_text() for p in out.glob(kind+'-*.json')}
  results.append({'name':'actual-native-'+kind,'run':run,'stdout':raw,'observations':observations,'fixture':identity(fixture)})
  if kind=='negative':
   for key in ['fadvise-kernel-failure','madvise-kernel-failure','double-owner','alias','cancel','hash','deadline','dedicated-reuse-offset']:assert key in raw
   continue
  for i in range(2):
   cold=json.loads(observations[f'random-{i}-cold.json']);touch=json.loads(observations[f'random-{i}-touched.json'])
   assert cold['cached_pages']==[] and len(touch['cached_pages'])==16
   policy_observation(touch['owner'],'loaded')
   line=next(json.loads(l) for l in raw.splitlines() if l.startswith('{') and json.loads(l).get('round')==i)
   assert line['bytes_compared']==65536 and line['post_advice_matches']==16
   expected=sum(((n*73)^(n>>8)^(n>>16))&255 for page in [17+1024*j for j in range(16)] for n in range(page*4096,(page+1)*4096));assert line['sum']==expected
  a=touch['owner']
  for name in ['default','shared','file-error','mapping-error','inode','mount']:
   bad=copy.deepcopy(a)
   if name=='default':bad['fault_policy']='default'
   elif name=='shared':bad['dedicated_description']=False
   elif name=='file-error':bad['file_policy_result']=1
   elif name=='mapping-error':bad['mapping_policy_result']=1
   elif name=='inode':bad['inode']+=1
   else:bad['mount']='0 '+bad['mount'].split(' ',1)[1]
   try:policy_observation(bad,'loaded')
   except Exception as e:results.append({'name':'policy-'+name,'refused':True,'error':repr(e)});continue
   raise AssertionError('Policy corruption passed')
  # Real same-process sample, with explicit fixture-only CPU-limit declaration.
  s=copy.deepcopy(run['samples'][0]);s['limits']='Max cpu time 150 160 seconds\n'
  assert resource_sample(s,os.sysconf('SC_CLK_TCK'))
  for name in ['cap','missing','swap','cpu','limits','missing-stat']:
   bad=copy.deepcopy(s)
   if name=='cap':bad['memory.current']='8053063680'
   elif name=='missing':bad.pop('memory.current')
   elif name=='swap':bad['memory.swap.current']='1'
   elif name=='limits':bad['limits']='Max cpu time unlimited unlimited seconds'
   elif name=='missing-stat':bad.pop('stat')
   else:
    pos=bad['stat'].rfind(')')+2;parts=bad['stat'][pos:].split();parts[11]=str(161*os.sysconf('SC_CLK_TCK'));bad['stat']=bad['stat'][:pos]+' '.join(parts)
   try:resource_sample(bad,os.sysconf('SC_CLK_TCK'))
   except Exception as e:results.append({'name':'resource-'+name,'refused':True,'error':repr(e)});continue
   raise AssertionError('Resource corruption passed')
 phases=dict(zip(['verified','loaded','prefill','generation','completed','unmapped'],range(1,7)));assert phase_chronology(phases,0,7)
 for name in ['missing','reorder','outside']:
  bad=dict(phases)
  if name=='missing':bad.pop('generation')
  elif name=='reorder':bad['generation']=2
  else:bad['unmapped']=8
  try:phase_chronology(bad,0,7)
  except AssertionError:results.append({'name':'phase-'+name,'refused':True});continue
  raise AssertionError('Chronology passed')
 # Preflight fails before any access to a real model; preserve durable receipt.
 import importlib.util
 spec=importlib.util.spec_from_file_location('current_screen_driver',R/'tools/evaluation/strong-native-host/run.py');driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
 atomic(out/'validator-controls-progress.json',{'synthetic_only':True,'results':results})
 old_o,old_capture,old_model=driver.O,driver.capture,driver.MODEL
 class Forbidden:
  def __fspath__(self):raise AssertionError('Forbidden model access')
 try:
  driver.O=out;driver.capture=lambda:(_ for _ in ()).throw(OSError('Frozen synthetic preflight failure'));driver.MODEL=Forbidden()
  case=driver.run_case(99,{})
  assert 'Frozen synthetic preflight failure' in case['failure'] and 'pid' not in case and (out/'case-99/receipt.json').exists()
  results.append({'name':'preflight-failure-no-model-access','case':case})
 finally:driver.O,driver.capture,driver.MODEL=old_o,old_capture,old_model
 return results
