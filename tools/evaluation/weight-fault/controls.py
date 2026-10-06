"""Prebound synthetic and code controls; generation functions are never run."""
import importlib.util,json,pathlib,sys,uuid
from common import R,O,sources,identity,owned,atomic

def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
 before=sources();out=O/('controls-'+uuid.uuid4().hex[:8]);out.mkdir();results=[]
 # Explicit imports keep accepted cleanup code and future generation code distinct.
 sys.path.insert(0,str(R/'tools/evaluation/strong-native-host'))
 support=load('support',R/'tools/evaluation/strong-native-host/support.py');sys.modules['support']=support
 future=load('future_scalar',R/'tools/evaluation/strong-native-host/run.py')
 future.O=out;future.capture=lambda:(_ for _ in ()).throw(OSError('Engineered preflight failure'))
 class ForbiddenModel:
  def __fspath__(self):raise AssertionError('Preflight failure attempted model access')
 future.MODEL=ForbiddenModel();case=future.run_case(99,{})
 assert 'Engineered preflight failure' in case['failure'] and 'pid' not in case and (out/'case-99/receipt.json').exists() and (out/'case-99/attempt.json').exists()
 results.append({'name':'preflight-failure-receipt-no-model-access','receipt':case})
 validation=load('future_validation',R/'tools/evaluation/strong-native-host/validate.py')
 phases={name:i+1 for i,name in enumerate(['verified','loaded','prefill','generation','completed','unmapped'])};assert validation.phase_chronology(phases,0,7)
 for kind in ['missing','reordered','outside']:
  bad=dict(phases)
  if kind=='missing':bad.pop('loaded')
  elif kind=='reordered':bad['prefill']=1
  else:bad['unmapped']=8
  try:validation.phase_chronology(bad,0,7)
  except AssertionError:results.append({'name':'phase-'+kind,'refused':True});continue
  raise AssertionError('Invalid phase sequence passed')
 # Algorithm-only CPU budget controls, not generated model evidence.
 fields=['0']*24;fields[11]='16000';assert validation.cpu_sample('1 (fixture) '+' '.join(fields),100);fields[11]='16001'
 try:validation.cpu_sample('1 (fixture) '+' '.join(fields),100)
 except AssertionError:results.append({'name':'cpu-over-budget','refused':True})
 else:raise AssertionError('CPU over-budget passed')
 historical=R/'docs/evidence/strong-scalar-inputs/historical/531-receipt.json'
 # The actual retained 534 is validated below when present; never fabricate a
 # successful model receipt to exercise future validators.
 p=R/'docs/evidence/weight-fault-inputs/534-receipt.json'
 assert p.exists(),'Missing retained actual failure'
 if p.exists():
  actual=json.loads(p.read_text());candidate=actual['cases'][0] if 'cases' in actual else actual
  try:validation.validate_case(candidate,{})
  except Exception as e:results.append({'name':'real-534-remains-failed','reason':repr(e),'sha256':identity(p)['sha256']})
  else:raise AssertionError('Failed actual generation accepted')
 for name,script,seconds,inject in [('hung','import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(30)',.3,False),('read-failure','import time;time.sleep(30)',2,True)]:
  run=owned.execute([sys.executable,'-c',script],out/name,seconds,inject);assert run['cleanup'][-1]['action']=='REAPED' and not pathlib.Path(f"/proc/{run['pid']}").exists();results.append({'name':name,'run':run})
 fixture=out/'fixture.bin';fixture.write_bytes(bytes(range(256))*16384);h=identity(fixture)['sha256']
 run=owned.execute([str(R/'downloads/native-cache-build/host/native-cache-controls'),str(fixture),h,'4194304',str(out/'native'),'0'],out/'native-run',30)
 text=(out/'native-run/stdout.log').read_text();assert run['exit']==0 and not run.get('failure')
 for name in ['wrong-inode','wrong-hash','wrong-size','unaligned','partial-map','deadline','cancelled','alias-mapping','scalar-order-byte-oracle','deferred-destructor-observation']:assert name in text
 results.append({'name':'current-native-lifecycle','run':run,'stdout':text})
 assert sources()==before;atomic(O/'controls.json',{'status':'PASS','source':before,'results':results});print('PASS_CODE_AND_NATIVE_CONTROLS')
if __name__=='__main__':main()
