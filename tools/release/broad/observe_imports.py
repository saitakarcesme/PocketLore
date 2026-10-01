#!/usr/bin/env python3
"""Observe existing project fixture import storage without controlling application state."""
import json,pathlib,subprocess,time,sys
out=pathlib.Path(sys.argv[1]);adb=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5560'];end=time.monotonic()+240
with (out/'import-storage-samples.jsonl').open('x') as log:
 while time.monotonic()<end:
  p=subprocess.run(adb+['shell','run-as','org.pocketlore.app','du','-ak','files/pack-library'],capture_output=True,text=True)
  rows=[]
  for line in p.stdout.splitlines():
   try:n,path=line.split(None,1);rows.append((int(n)*1024,path))
   except ValueError:pass
  log.write(json.dumps({'monotonic_seconds':time.monotonic(),'partial_allocated_bytes':sum(n for n,path in rows if path.endswith('.partial')),'library_allocated_bytes':next((n for n,path in rows if path=='files/pack-library'),None),'files':rows,'error':p.stderr})+'\n');log.flush()
  if (out/'summary.json').exists():break
  time.sleep(.5)
