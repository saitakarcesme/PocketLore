#!/usr/bin/env python3
"""Isolated systemd crash-after-receipt smoke test; never invokes Codex."""
import json, os, pathlib, subprocess, tempfile, time

def main():
    target = pathlib.Path(__file__).with_name('runner.py').resolve()
    fixture = pathlib.Path(tempfile.mkdtemp(prefix='pocketlore-recovery-'))
    (fixture/'work').mkdir()
    subprocess.run(['git','init','-q',str(fixture/'work')],check=True)
    worker = fixture/'worker.py'
    worker.write_text('''import importlib.util, pathlib, os, sys
root=pathlib.Path(sys.argv[1])
spec=importlib.util.spec_from_file_location('runner',sys.argv[2]);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
r=m.Runner(root,root/'work')
t={'id':'fixture','attempt':0}
command=['python3','-c', 'from pathlib import Path; p=Path('+repr(str(root/'executions'))+'); p.write_text(p.read_text()+"x" if p.exists() else "x")']
result=r.run_process(t,'check',command,root/'work')
crash=root/'crashed-once'
if not crash.exists():
 crash.write_text('Crash after command receipt, before completion event.'); os._exit(42)
r.event('fixture:completion',status='accepted')
(root/'recovered').write_text('ok')
''')
    env=dict(os.environ,XDG_RUNTIME_DIR='/run/user/'+str(os.getuid()),DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/'+str(os.getuid())+'/bus')
    name='pocketlore-recovery-'+str(os.getpid())
    subprocess.run(['systemd-run','--user','--unit='+name,'--property=Restart=on-failure','--property=RestartSec=1','--property=KillMode=control-group','/usr/bin/python3',str(worker),str(fixture),str(target)],env=env,check=True,capture_output=True)
    deadline=time.monotonic()+20
    while not (fixture/'recovered').exists() and time.monotonic()<deadline: time.sleep(.2)
    state=json.loads((fixture/'state/runner.json').read_text())
    result={'fixture':str(fixture),'service':name,'crash_injected':(fixture/'crashed-once').exists(),'recovered':(fixture/'recovered').exists(),'execution_count':len((fixture/'executions').read_text()),'completion_event_count':len([e for e in state['events'] if e['id']=='fixture:completion'])}
    result['passed']=result['crash_injected'] and result['recovered'] and result['execution_count']==1 and result['completion_event_count']==1
    print(json.dumps(result,indent=2))
    subprocess.run(['systemctl','--user','reset-failed',name],env=env,capture_output=True)
    if not result['passed']: raise SystemExit(1)

if __name__=='__main__': main()
