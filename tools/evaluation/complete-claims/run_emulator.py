#!/usr/bin/env python3
"""Run only the three frozen JNI cases in isolated app storage; no service changes."""
from pathlib import Path
import subprocess,json,hashlib,datetime,sys
R=Path(__file__).resolve().parents[3]
A=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5560']
O=R/'downloads/complete-claims'/('emulator-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'));O.mkdir()
def run(args,**kw):return subprocess.run(A+args,check=True,capture_output=True,**kw).stdout
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert run(['shell','getprop','sys.boot_completed']).strip()==b'1'
ids=['cap-02','cap-05','new-01'];m={'environment':'Existing emulator-5560, x86_64 CPU JNI; not physical hardware','case_ids':ids,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
for kind,apk in [('app','android/app/build/outputs/apk/debug/app-debug.apk'),('test','android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk')]:
 p=R/apk;m[kind+'_sha256']=sha(p);(O/(kind+'-install.txt')).write_bytes(run(['install','-r',str(p)]))
base='files/complete-claims';run(['shell','run-as','org.pocketlore.app','mkdir','-p',base+'/inputs',base+'/results'])
# Refuse to overwrite prior results; recovery must inspect and preserve them.
assert not run(['shell','run-as','org.pocketlore.app','ls',base+'/results']).strip()
def put(data,dest):return run(['exec-in','run-as','org.pocketlore.app','sh','-c','cat > '+dest],input=data)
inp=R/'downloads/complete-claims/after-20261001T054408Z/inputs'
put(('\n'.join(l for l in (inp/'cases.tsv').read_text().splitlines() if l.split('\t')[0] in ids)+'\n').encode(),base+'/inputs/cases.tsv')
for i in ids:put((inp/(i+'.tsv')).read_bytes(),base+'/inputs/'+i+'.tsv')
model=R/'downloads/synthesis/model/Qwen3-1.7B-Q8_0.gguf';m['model_sha256']=sha(model)
with model.open('rb') as f:subprocess.run(A+['exec-in','run-as','org.pocketlore.app','sh','-c','cat > '+base+'/model.gguf'],stdin=f,check=True)
assert run(['shell','run-as','org.pocketlore.app','sha256sum',base+'/model.gguf']).decode().split()[0]==m['model_sha256']
(O/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(O,flush=True)
p=subprocess.run(A+['shell','am','instrument','-w','org.pocketlore.app.test/org.pocketlore.app.CompleteClaimInstrumentation'],capture_output=True,timeout=900)
(O/'instrumentation.txt').write_bytes(p.stdout+p.stderr)
for name in ['load.json']+[i+'.json' for i in ids]: (O/name).write_bytes(run(['exec-out','run-as','org.pocketlore.app','cat',base+'/results/'+name]))
m['exit_code']=p.returncode;m['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();m['artifacts']={p.name:sha(p) for p in O.iterdir() if p.name!='manifest.json'};(O/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
assert p.returncode==0 and b'INSTRUMENTATION_CODE: -1' in p.stdout
print('PASS real JNI subset',flush=True)
