#!/usr/bin/env python3
"""Native-only development overlay for the exact coordinator UI APK, not a source merge."""
import hashlib,json,pathlib,subprocess,zipfile,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[2];TC=pathlib.Path('/home/isa/Android/atlas-toolchain')
base=pathlib.Path('/home/isa/PocketLore-control/runtime/modern-android/pocketlore-ui-candidate.apk');out=ROOT/'downloads/android-16kb/refined-ui-16kb.apk'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='3873ba23b6cda8268ec77ced1362a2e3230751d09f7ae111cfecb1795ece364e'
native={f'lib/{abi}/{name}.so':ROOT/f'android/app/build/generated/nativeLibs/{abi}/{name}.so' for abi in ['arm64-v8a','x86_64'] for name in ['libpocketlore','libpocketlore_index']}
def signature(name):return name.upper().startswith('META-INF/') and name.upper().endswith(('.RSA','.SF','.DSA','.EC','MANIFEST.MF'))
with tempfile.TemporaryDirectory(dir=ROOT/'downloads/android-16kb') as tmp:
 tmp=pathlib.Path(tmp)
 with zipfile.ZipFile(base) as src,zipfile.ZipFile(tmp/'unsigned.apk','w') as dest:
  for info in src.infolist():
   if signature(info.filename):continue
   body=native[info.filename].read_bytes() if info.filename in native else src.read(info.filename)
   info.extra=b''
   dest.writestr(info,body)
 subprocess.run([TC/'sdk/build-tools/35.0.0/zipalign','-P','16','-f','4',tmp/'unsigned.apk',tmp/'aligned.apk'],check=True)
 subprocess.run([TC/'sdk/build-tools/35.0.0/apksigner','sign','--ks',ROOT/'downloads/android-debug/debug.keystore','--ks-key-alias','androiddebugkey','--ks-pass','pass:android','--key-pass','pass:android','--out',out,tmp/'aligned.apk'],check=True)
 subprocess.run([TC/'sdk/build-tools/35.0.0/apksigner','verify',out],check=True)
with zipfile.ZipFile(base) as a,zipfile.ZipFile(out) as b:
 assert set(a.namelist())==set(b.namelist())
 changed=[n for n in sorted(a.namelist()) if a.read(n)!=b.read(n)]
 assert {n for n in changed if not signature(n)}==set(native),changed
receipt={'base_sha256':hashlib.sha256(base.read_bytes()).hexdigest(),'output':str(out.relative_to(ROOT)),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bytes':out.stat().st_size,'changed_entries':changed,'policy':'Only four native libraries and signatures differ; UI DEX/resources/manifest/assets preserved byte-for-byte. Separate development overlay, not a source integration or release.'}
(ROOT/'docs/evidence/android-16kb/refined-ui-overlay.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
