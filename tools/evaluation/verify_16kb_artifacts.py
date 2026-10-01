#!/usr/bin/env python3
"""Inspect actual ELF64 program headers and APK entry offsets, not filenames or flags."""
import hashlib,json,struct,sys,zipfile
PAGE=16384

def elf(data):
 if data[:6]!=b'\x7fELF\x02\x01':raise ValueError('Expected little-endian ELF64')
 offset=struct.unpack_from('<Q',data,32)[0];size,count=struct.unpack_from('<HH',data,54);loads=[];relro=[]
 for i in range(count):
  kind,flags,off,va,pa,filesz,memsz,align=struct.unpack_from('<IIQQQQQQ',data,offset+i*size)
  if kind==1:loads.append({'offset':off,'vaddr':va,'align':align,'valid':align>=PAGE and (va-off)%PAGE==0})
  if kind==0x6474e552:relro.append({'vaddr':va,'memsz':memsz,'valid':(va+memsz)%PAGE==0})
 return {'machine':struct.unpack_from('<H',data,18)[0],'loads':loads,'relro':relro,'valid':bool(loads) and all(x['valid'] for x in loads+relro)}

def inspect(path):
 raw=open(path,'rb').read();rows=[]
 with zipfile.ZipFile(path) as apk:
  for info in apk.infolist():
   if not info.filename.startswith('lib/') or not info.filename.endswith('.so'):continue
   body=apk.read(info);name,extra=struct.unpack_from('<HH',raw,info.header_offset+26);start=info.header_offset+30+name+extra
   r=elf(body);r.update(name=info.filename,sha256=hashlib.sha256(body).hexdigest(),bytes=len(body),zip_offset=start,uncompressed=info.compress_type==0)
   r['zip_valid']=r['uncompressed'] and start%PAGE==0;rows.append(r)
 expected={f'lib/{a}/{n}.so' for a in ['arm64-v8a','x86_64'] for n in ['libpocketlore','libpocketlore_index','libpocketlore_attachments']}
 valid={r['name'] for r in rows}==expected and all(r['valid'] and r['zip_valid'] and r['machine']==(183 if '/arm64-v8a/' in r['name'] else 62) for r in rows)
 return {'apk_sha256':hashlib.sha256(raw).hexdigest(),'apk_bytes':len(raw),'libraries':rows,'valid':valid}
if __name__=='__main__':
 result=inspect(sys.argv[1]);print(json.dumps(result,indent=2));sys.exit(0 if result['valid'] else 1)
