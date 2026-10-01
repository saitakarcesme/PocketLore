"""Discriminating mutations of real built ELF/APK bytes; no inference."""
import importlib.util,pathlib,struct,tempfile,zipfile
from verify_16kb_artifacts import elf,inspect
ROOT=pathlib.Path(__file__).resolve().parents[2]
apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk'
assert inspect(apk)['valid']
with zipfile.ZipFile(apk) as z:
 name='lib/x86_64/libpocketlore.so';data=z.read(name);off=struct.unpack_from('<Q',data,32)[0];size,count=struct.unpack_from('<HH',data,54)
 load=next(off+i*size for i in range(count) if struct.unpack_from('<I',data,off+i*size)[0]==1)
 relro=next(off+i*size for i in range(count) if struct.unpack_from('<I',data,off+i*size)[0]==0x6474e552)
 changed=bytearray(data);struct.pack_into('<Q',changed,load+48,4096);assert not elf(changed)['valid']
 changed=bytearray(data);v=struct.unpack_from('<Q',data,relro+40)[0];struct.pack_into('<Q',changed,relro+40,v+4096);assert not elf(changed)['valid']
 with tempfile.TemporaryDirectory() as tmp:
  for mode in ['missing','zip-offset','compressed']:
   p=pathlib.Path(tmp)/(mode+'.apk')
   with zipfile.ZipFile(p,'w') as out:
    for info in z.infolist():
     if mode=='missing' and info.filename==name:continue
     out.writestr(info.filename,z.read(info),compress_type=zipfile.ZIP_DEFLATED if mode=='compressed' else zipfile.ZIP_STORED)
   assert not inspect(p)['valid'],mode
old=pathlib.Path('/home/isa/PocketLore-control/runtime/modern-android/pocketlore-ui-candidate.apk')
assert not inspect(old)['valid']
print('PASS: actual original APK rejected; LOAD, RELRO, missing-library, ZIP offset and compressed-library mutations rejected')
