#!/usr/bin/env python3
"""Capture actual installed APK/code directories separately from app-data samples."""
import json,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[3];ADB=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5562']
def shell(*args):return subprocess.check_output(ADB+['shell',*args],text=True)
rows=[]
for pkg in ['org.pocketlore.app','org.pocketlore.app.test']:
 paths=[x.removeprefix('package:') for x in shell('pm','path',pkg).splitlines()];assert len(paths)==1
 directory=str(pathlib.PurePosixPath(paths[0]).parent)
 raw=shell('du','-k',directory);allocated=int(raw.splitlines()[-1].split()[0])*1024
 rows.append({'package':pkg,'apk_path':paths[0],'apk_sha256':shell('sha256sum',paths[0]).split()[0],'allocated_code_bytes':allocated,'du_k':raw})
out=ROOT/'docs/evidence/full-capacity'/('package-storage-'+sys.argv[1]+'.json')
with out.open('x') as f:json.dump({'serial':'emulator-5562','rows':rows,'allocated_code_bytes':sum(r['allocated_code_bytes'] for r in rows)},f,indent=2);f.write('\n')
