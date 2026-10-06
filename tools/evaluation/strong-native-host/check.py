"""Actual scalar generation gate; failed/incomplete execution cannot pass."""
import base64,copy,hashlib,importlib.util,json,pathlib,sys,time
from support import R,O,BINARIES,SOURCES,sha,identity,source_check,atomic
from validate import validate

def pack(p):
 b=p.read_bytes();return {'sha256':hashlib.sha256(b).hexdigest(),'base64':base64.b64encode(b).decode(),'bytes':len(b)}
def links(source):
 spec=importlib.util.spec_from_file_location('parent_native_checker',R/'tools/evaluation/native-cache/check.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m.artifacts(source)
def main():
 result={'status':'HOST_ENGINEERING_INCOMPLETE','errors':[],'android_execution':False,'product_qualified':False,'files':{},'started_ns':time.monotonic_ns()}
 # Freeze ALL attempted cases and the explicit unexecuted denominator first.
 for p in [O/'screen.json',O/'frozen.json',O/'controls-path.txt']+sorted(O.glob('case-*/receipt.json'))+sorted((O/'logs').glob('*'))+sorted(O.glob('controls-*/*.json'))+sorted(O.glob('controls-*/*/*.log')):
  try:
   if p.is_file():result['files'][str(p.relative_to(R))]=pack(p)
  except Exception as e:result['errors'].append('Collection '+str(p)+': '+repr(e))
 try:
  frozen=json.loads((O/'frozen.json').read_text());source_check(frozen['source']);result['linked_artifacts']=links(frozen['source_path'])
  controls=pathlib.Path((O/'controls-path.txt').read_text());result['controls']=json.loads(controls.read_text());assert result['controls']['status']=='CURRENT_NATIVE_CONTROLS_PASS' and result['controls']['source']==frozen['source']
  actual=json.loads((O/'screen.json').read_text());result['execution']=actual;result['measurements']=validate(actual)
  negatives=[]
  for name in ['duplicate-case','missing-case','wrong-pid','wrong-start','wrong-source','wrong-binary','missing-generation','wrong-mount','batch32','missing-release','aggregate-cap','missing-resource','swap','policy','cpu','wall']:
   bad=copy.deepcopy(actual);c=bad['cases'][0]
   if name=='duplicate-case':bad['cases'][1]=copy.deepcopy(c)
   elif name=='missing-case':bad['cases'].pop()
   elif name=='wrong-pid':c['samples'][0]['pid']+=1
   elif name=='wrong-start':c['startticks']+=1
   elif name=='wrong-source':bad['frozen']['source']={}
   elif name=='wrong-binary':bad['frozen']['binary'][BINARIES[1]]['sha256']='0'*64
   elif name=='missing-generation':c['stdout']=''
   elif name=='wrong-mount':
    a=json.loads(c['raw']['loaded.json']);a['mount']=a['mount'].replace(a['mount'].split()[2],'0:9999',1);c['raw']['loaded.json']=json.dumps(a)
   elif name=='batch32':c['stderr']=c['stderr'].replace('SCALAR_BEGIN 0 1','SCALAR_BEGIN 0 32')
   elif name=='aggregate-cap':c['samples'][0]['memory.current']='8053063680'
   elif name=='missing-resource':c['samples'][0].pop('memory.current')
   elif name=='swap':c['samples'][0]['memory.swap.current']='1'
   elif name=='wall':c['end_ns']=c['start_ns']+181_000_000_000
   elif name=='cpu':c['clock_ticks']=1
   elif name=='policy':
    a=json.loads(c['raw']['loaded.json']);a['fault_policy']='default';c['raw']['loaded.json']=json.dumps(a)
   else:c['raw'].pop('unmapped.json')
   try:validate(bad)
   except Exception as e:negatives.append({'mutation':name,'refused':True,'error':repr(e)});continue
   raise AssertionError('Corrupt actual receipt accepted: '+name)
  result['negative_controls']=negatives;assert not result['errors'];result['status']='PASS_BOUNDED_HOST_GENERATION_ONLY'
 except Exception as e:result['errors'].append(type(e).__name__+': '+str(e))
 finally:
  result['checker']={'sha256':sha(pathlib.Path(__file__)),'text':pathlib.Path(__file__).read_text()};result['finished_ns']=time.monotonic_ns();result['exit']=int(bool(result['errors']));result['stdout']=result['status']+'\n';atomic(O/'current-check.json',result)
  target=R/'docs/evidence/strong-native-host-review.json';atomic(target,result);print(result['stdout'],end='')
 return result['exit']
if __name__=='__main__':raise SystemExit(main())
