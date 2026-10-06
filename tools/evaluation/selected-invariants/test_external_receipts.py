"""Validate the real old tiny packet only in its own scope, then reject counterfactuals."""
import copy,json,pathlib,sys,hashlib
from external_receipts import load_packet,validate_bindings,validate_index,code_map
ROOT=pathlib.Path(__file__).resolve().parents[3]
PACKET=pathlib.Path('/home/isa/PocketLore-control/overnight-20261005/selected-source-kernel-probe-result-review-20261006T0509Z')
PIN='af8a80cfc27784eedaff780f76c602a22d5963e5413b8a1572a45db3f696e75a'
def substitute_rank(p):
 for owner in [p['owner.json'],p['status.json']['configuration']]+[e['configuration'] for e in p['events']]:owner['ranking_sha256']='0'*64
 for argv in [p['plan.json']['argv'],p['actual-child-start.json']['argv']]:argv[argv.index('--ranking-sha256')+1]='0'*64

def main(out):
 out.mkdir(parents=True);packet=load_packet(PACKET,PIN);code=code_map(packet['owner.json']['code']);positive=validate_bindings(packet,code,8,999)
 argv=packet['plan.json']['argv'];index=pathlib.Path(argv[argv.index('--out')+1])/'index.sqlite';positive['actual_index']=validate_index(packet,index)
 cases={
  'consistent-substituted-ranking':substitute_rank,
  'shared-unlimited-memory':lambda p:p['actual-kernel-start.json']['kernel'].__setitem__('memory.max','max'),
  'swap-enabled':lambda p:p['actual-kernel-final.json']['kernel'].__setitem__('memory.swap.max','1'),
  'cpu-unlimited':lambda p:p['actual-kernel-final.json']['kernel'].__setitem__('cpu.max','max 100000'),
  'tasks-unlimited':lambda p:p['actual-kernel-final.json']['kernel'].__setitem__('pids.max','max'),
  'oom-event':lambda p:p['actual-kernel-final.json']['kernel'].__setitem__('memory.events','max 0\noom 1\noom_kill 1'),
  'changed-pid':lambda p:p['actual-child-start.json'].__setitem__('host_child_pid',1),
  'changed-group':lambda p:p['actual-kernel-final.json']['kernel'].__setitem__('path','/different.service'),
  'unbracketed':lambda p:p['actual-kernel-final.json'].__setitem__('at',0),
  'wrong-plan':lambda p:p['actual-kernel-start.json'].__setitem__('plan_sha256','0'*64),
  'failed-child':lambda p:p['actual-kernel-final.json'].__setitem__('child_returncode',1),
  'missing-final-phase':lambda p:p.__setitem__('events',[e for e in p['events'] if e['phase']!='fts']),
  'false-promotion':lambda p:p['status.json'].__setitem__('source_admission_established',True),
  'wrong-count':lambda p:p['status.json']['counts'].__setitem__('receipts',7),
  'changed-code':lambda p:p['owner.json']['code'].__setitem__(next(iter(p['owner.json']['code'])),'0'*64),
 }
 results=[]
 for name,mutate in cases.items():
  bad=copy.deepcopy(packet);mutate(bad)
  try:validate_bindings(bad,code,8,999)
  except (ValueError,KeyError) as e:results.append({'control':name,'rejected':True,'reason':str(e)})
  else:raise AssertionError('Counterfactual accepted: '+name)
 current={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in code}
 for name,c,n in [('old-code-as-current',current,8),('tiny-as-6000',code,6000)]:
  try:validate_bindings(packet,c,n,999)
  except ValueError as e:results.append({'control':name,'rejected':True,'reason':str(e)})
  else:raise AssertionError('Scope inflation accepted')
 result={'status':'PASS','scope':'Offline validation of existing old eight-source packet only; no new producer execution or current-scale credit','positive':positive,'negative_controls':results,'packet_manifest_sha256':PIN,'current_source_qualified':False,'android_execution':False,'test_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'validator_sha256':hashlib.sha256(pathlib.Path(__file__).with_name('external_receipts.py').read_bytes()).hexdigest()};(out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main(pathlib.Path(sys.argv[1]))
