"""Typed parent observations only; no commands or service mutations are requested."""
import hashlib,json,pathlib,time,uuid
UNIT='pocketlore-modern-emulator.service'
TASK='523-android-runtime-durability-and-preserved-state-material-measured-window-and-final-receipts'
REQUESTS=pathlib.Path('/home/isa/PocketLore-control/evidence/android-host-witness-requests')
def sha(data):return hashlib.sha256(data).hexdigest()
def validate(request,response,raw_request):
    assert response['schema']==1 and response['status']=='observed', 'Witness status'
    assert response['request_sha256']==sha(raw_request),'Witness request hash'
    for key in ('nonce','phase','task_id','source_hash','run_id','unit'):assert response[key]==request[key], 'Witness '+key
    props=response['props'];assert props['ActiveState']=='active' and props['SubState']=='running' and props['Restart']=='no','Inactive owned process/circuit'
    assert int(response['pid'])>0 and int(props['MainPID'])==int(response['pid']) and int(response['proc_start_ticks'])>0,'Witness PID/start'
    assert len(props['InvocationID'])==32 and int(props['ExecMainStartTimestampMonotonic'])>0,'Witness invocation/start'
    assert response['host_boot_id'] and len(response['executable_sha256'])==64 and response['executable'].endswith('/qemu-system-x86_64-headless'),'Witness executable'
    assert props['ControlGroup'] in response['proc_cgroup'] and props['ControlGroup'].endswith('/'+UNIT),'Witness cgroup'
    argv=response['argv'];assert argv[argv.index('-port')+1]=='5564' and '-wipe-data' not in argv and '-read-only' not in argv,'Witness owned argv'
    assert response['monotonic_ns']>int(props['ExecMainStartTimestampMonotonic'])*1000,'Witness monotonic'
def request(out,phase,source_hash,start,end=None):
    nonce=uuid.uuid4().hex;run=out.name;inputs=out/'source-inputs.json';now=time.time()
    data={'nonce':nonce,'phase':phase,'unit':UNIT,'task_id':TASK,'source_hash':source_hash,'source_inputs_path':str(inputs.resolve()),'run_id':run,'check_started_epoch':start}
    if end is not None:data['check_finished_epoch']=end
    raw=(json.dumps(data,sort_keys=True,indent=2)+'\n').encode();stem=f'{nonce}.{phase}'
    dest=REQUESTS/(stem+'.request.json');dest.write_bytes(raw);(out/(phase+'-witness.request.json')).write_bytes(raw)
    response=REQUESTS/(stem+'.response.json');deadline=time.monotonic()+180
    while not response.exists() and time.monotonic()<deadline:time.sleep(1)
    assert response.exists(),'Parent witness missing after 180 seconds'
    reply=response.read_bytes();(out/(phase+'-witness.response.json')).write_bytes(reply);result=json.loads(reply);validate(data,result,raw)
    assert now-2<=result['observed_epoch']<=time.time()+2 and time.time()-result['observed_epoch']<=180,'Stale witness'
    return result
def continuity(before,after,android_start,android_end):
    assert before['observed_epoch']<=android_start<=android_end<=after['observed_epoch'],'Unbracketed Android run'
    assert after['monotonic_ns']>before['monotonic_ns'],'Witness monotonic order'
    for key in ('pid','proc_start_ticks','host_boot_id','proc_cgroup','argv','executable','executable_sha256'):assert before[key]==after[key], 'Changed host '+key
    for key in ('InvocationID','ExecMainStartTimestampMonotonic','ControlGroup','NRestarts'):assert before['props'][key]==after['props'][key], 'Changed host '+key
    return True
