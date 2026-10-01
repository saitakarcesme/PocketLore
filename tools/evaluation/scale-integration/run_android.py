#!/usr/bin/env python3
"""Run named on-device behaviors serially; archive inputs separately before project-fixture removal."""
import argparse,json,pathlib,subprocess,time
p=argparse.ArgumentParser();p.add_argument('modes',nargs='+',choices=['inspect','negative','native','ui']);p.add_argument('--output',required=True);a=p.parse_args()
out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=True)
adb=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5560']
for mode in a.modes:
 dest=out/(mode+'.json')
 if dest.exists():raise SystemExit('Refusing to replace evidence: '+str(dest))
 proc=subprocess.run(adb+['shell','am','instrument','-w','-e','mode',mode,'org.pocketlore.app.test/org.pocketlore.app.ScaleIntegrationInstrumentation'],capture_output=True,text=True,timeout=900)
 (out/(mode+'.txt')).write_text(proc.stdout+proc.stderr)
 raw=subprocess.check_output(adb+['exec-out','run-as','org.pocketlore.app','cat','files/scale-observation-'+mode+'.json'])
 dest.write_bytes(raw);report=json.loads(raw)
 if proc.returncode or report.get('status')!='PASS' or 'INSTRUMENTATION_CODE: -1' not in proc.stdout:raise SystemExit('Behavior failed; evidence preserved: '+mode)
 print(mode,'PASS',flush=True)
