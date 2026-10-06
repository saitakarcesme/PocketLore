"""Constructed protocol mutations, never proof of a real host observation."""
import copy,json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from witness import validate,continuity,sha,UNIT,TASK
parent=json.loads(pathlib.Path('/home/isa/PocketLore-control/overnight-20261005/owned-host-witness-20261006T0157Z-before.json').read_text())
request={'nonce':'constructed','phase':'before','task_id':TASK,'source_hash':'0'*64,'run_id':'constructed','unit':UNIT}
raw=json.dumps(request).encode();before=dict(parent,**request,schema=1,status='observed',request_sha256=sha(raw),observed_epoch=100)
validate(request,before,raw);after=copy.deepcopy(before);after['observed_epoch']=200;after['monotonic_ns']+=100000000000
continuity(before,after,110,190);controls=[]
for field,value in [('nonce','wrong'),('request_sha256','wrong'),('source_hash','wrong'),('run_id','wrong'),('pid',0),('proc_start_ticks',0),('argv',['-port','5560'])]:
 bad=copy.deepcopy(before);bad[field]=value
 try:validate(request,bad,raw)
 except (AssertionError,ValueError):controls.append(field)
 else:raise AssertionError('Accepted '+field)
for field in ('pid','proc_start_ticks','host_boot_id','executable_sha256','proc_cgroup'):
 bad=copy.deepcopy(after);bad[field]='changed'
 try:continuity(before,bad,110,190)
 except AssertionError:controls.append(field+'-continuity')
 else:raise AssertionError(field)
for field in ('InvocationID','ExecMainStartTimestampMonotonic'):
 bad=copy.deepcopy(after);bad['props'][field]='changed'
 try:continuity(before,bad,110,190)
 except AssertionError:controls.append(field)
 else:raise AssertionError(field)
try:continuity(before,after,99,190)
except AssertionError:controls.append('unbracketed')
else:raise AssertionError('Unbracketed accepted')
print(json.dumps({'classification':'Constructed controls using historical identity only; no current runtime proof','rejected':controls,'exit':0},indent=2))
