#!/usr/bin/env python3
"""Require two real forced builds to match exactly; retain every run and failure."""
from pathlib import Path
import datetime,hashlib,json,subprocess,zipfile
ROOT=Path(__file__).resolve().parents[2]
def main():
    out=ROOT/'downloads/release-repro'/datetime.datetime.now(datetime.timezone.utc).strftime('run-%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True)
    apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk';hashes=[]
    for label in ['a','b']:
        with (out/(label+'.log')).open('wb') as log:
            result=subprocess.run(['bash',str(ROOT/'tools/android-build.sh'),'assembleDebug','--rerun-tasks'],stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:raise RuntimeError(f'Forced build {label} failed; preserved at {out}')
        data=apk.read_bytes();hashes.append(hashlib.sha256(data).hexdigest());(out/(label+'.apk')).write_bytes(data)
        with zipfile.ZipFile(apk) as z:
            dex=[z.read(n) for n in z.namelist() if n.startswith('classes') and n.endswith('.dex')]
            if not dex or any(b'~~~{' in d for d in dex):raise AssertionError('Unexpected incremental DEX class-checksum metadata')
    report={'scope':'Same rig/toolchain/key, two forced builds; not independent clean-machine reproduction','apk_sha256':hashes,'equal':hashes[0]==hashes[1]}
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    if not report['equal']:raise AssertionError(f'APK drift; failure preserved at {out}')
    print('PASS: two forced builds byte-identical:',hashes[0]);print(out)
if __name__=='__main__':main()
