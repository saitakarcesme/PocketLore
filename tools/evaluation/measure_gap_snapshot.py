#!/usr/bin/env python3
"""One read-only emulator snapshot, never a peak/phone or installed-device-budget claim."""
from pathlib import Path
import datetime,json,os,subprocess,time
ROOT=Path(__file__).resolve().parents[2]
adb=Path(os.environ.get('POCKETLORE_TOOLCHAIN','/home/isa/Android/atlas-toolchain'))/'sdk/platform-tools/adb'
start=time.monotonic();commands={}
for name,args in {'boot':['getprop','sys.boot_completed'],'fingerprint':['getprop','ro.build.fingerprint'],'memory':['dumpsys','meminfo','org.pocketlore.app'],'owned_disk':['run-as','org.pocketlore.app','du','-sk','files','cache','code_cache'],'apk_path':['pm','path','org.pocketlore.app']}.items():
 p=subprocess.run([str(adb),'-s','emulator-5560','shell',*args],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 commands[name]={'argv':args,'exit_code':p.returncode,'output':p.stdout.decode(errors='replace')}
path=commands['apk_path']['output'].strip()
if commands['apk_path']['exit_code']==0 and path.startswith('package:/') and '\n' not in path:
 args=['sha256sum',path.removeprefix('package:')];p=subprocess.run([str(adb),'-s','emulator-5560','shell',*args],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 commands['installed_apk_hash']={'argv':args,'exit_code':p.returncode,'output':p.stdout.decode(errors='replace')}
report={'measured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Single instantaneous existing emulator snapshot; no physical device, no peak memory, no sustained workload, no model invocation','collection_wall_seconds':time.monotonic()-start,'commands':commands}
(ROOT/'docs/evidence/release-gap-review/emulator-snapshot.json').write_text(json.dumps(report,indent=2)+'\n')
assert all(c['exit_code']==0 for c in commands.values()) and commands['boot']['output'].strip()=='1'
print('Recorded existing emulator snapshot; memory is one instant, disk excludes provider originals and installed APK')
