import sys,pathlib,json,time
sys.path.insert(0,'tools/evaluation/android-runtime-durability')
from witness import request,continuity
out=pathlib.Path(__file__).resolve().parent
req=json.loads((out/'before-witness.request.json').read_text());before=json.loads((out/'before-witness.response.json').read_text());failure=json.loads((out/'failure.json').read_text())
end=max(json.loads(p.read_text()).get('observed_epoch',0) for p in out.glob('failure-*.command.json'))
after=request(out,'after',req['source_hash'],req['check_started_epoch'],end)
result={'status':'FAILED_RUN_HOST_CONTINUITY_ONLY','native_admission_ran':False,'lifecycle_gate_pass':False,'host_bracket_valid':continuity(before,after,failure['android_start_epoch'],end),'boot_unchanged':(out/'failure-boot-after.txt').read_bytes()==(out/'boot-before.txt').read_bytes()}
(out/'failure-closeout.json').write_text(json.dumps(result,indent=2))
