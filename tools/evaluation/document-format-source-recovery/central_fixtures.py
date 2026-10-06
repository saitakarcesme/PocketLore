"""Authored ZIP byte structures and fixed counterexamples; never executes a parser."""
import struct,zlib,json,hashlib,pathlib
B=pathlib.Path(__file__).resolve().parent;F=B/'central-fixtures'
PAYLOAD='Source café 🙂\r\nOnly if safe; otherwise wait.\n'.encode()
def u16(b,p,n):b[p:p+2]=struct.pack('<H',n)
def u32(b,p,n):b[p:p+4]=struct.pack('<I',n)
def archive(method=0,descriptor=0,name=b'entry.txt',payload=PAYLOAD,comment=b'',extra=b''):
 c=zlib.compressobj(wbits=-15);data=c.compress(payload)+c.flush() if method==8 else payload;crc=zlib.crc32(payload);flags=0x800|(8 if descriptor else 0)
 local=struct.pack('<IHHHHHIIIHH',0x04034b50,20,flags,method,0,0,0 if descriptor else crc,0 if descriptor else len(data),0 if descriptor else len(payload),len(name),len(extra))+name+extra
 dd=(struct.pack('<I',0x08074b50) if descriptor==1 else b'')+struct.pack('<III',crc,len(data),len(payload)) if descriptor else b''
 central=struct.pack('<IHHHHHHIIIHHHHHII',0x02014b50,20,20,flags,method,0,0,crc,len(data),len(payload),len(name),0,0,0,0,0,0)+name
 offset=len(local)+len(data)+len(dd);end=struct.pack('<IHHHHIIH',0x06054b50,0,0,1,1,len(central),offset,len(comment))+comment
 return bytearray(local+data+dd+central+end),offset,len(local),len(data)
def freeze():
 F.mkdir(exist_ok=False);cases=[]
 def add(name,b,ok,expected=PAYLOAD,cancel=False):
  p=F/(name+'.zip');p.write_bytes(b);cases.append({'name':name,'file':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'accept':ok,'cancel':cancel,'payload_sha256':hashlib.sha256(expected).hexdigest() if ok else None})
 for name,kw in [('stored',{}),('deflated',{'method':8}),('signed-descriptor',{'method':8,'descriptor':1}),('unsigned-descriptor',{'method':8,'descriptor':2}),('comment',{'comment':b'authored comment'}),('directory',{'name':b'dir/','payload':b''}),('utf8-name',{'name':'café.txt'.encode()})]:
  b,*_=archive(**kw);add(name,b,True,b'' if name=='directory' else PAYLOAD)
 b,c,l,n=archive();e=len(b)-22
 mutations={
 'eocd-trailing':lambda x:x.extend(b'x'),'eocd-comment':lambda x:u16(x,e+20,1),'disk':lambda x:u16(x,e+4,1),'zip64-count':lambda x:u16(x,e+10,65535),'central-count':lambda x:u16(x,e+10,2),'central-size':lambda x:u32(x,e+12,1),'central-offset':lambda x:u32(x,e+16,0),'central-crc':lambda x:u32(x,c+16,1),'central-expanded':lambda x:u32(x,c+24,1),'central-compressed':lambda x:u32(x,c+20,1),'central-method':lambda x:u16(x,c+10,9),'central-flags':lambda x:u16(x,c+8,0x801),'central-name':lambda x:x.__setitem__(c+46,ord('X')),'local-offset':lambda x:u32(x,c+42,1),'local-name':lambda x:x.__setitem__(30,ord('X')),'local-method':lambda x:u16(x,8,8),'local-flags':lambda x:u16(x,6,0),'local-crc':lambda x:u32(x,14,1),'local-size':lambda x:u32(x,22,1),'local-extra-truncated':lambda x:u16(x,28,65535),'payload-corrupt':lambda x:x.__setitem__(l,0),'truncated':lambda x:x.__delitem__(slice(-5,None))}
 for name,fn in mutations.items():x=bytearray(b);fn(x);add(name,x,False)
 x,*_=archive(extra=struct.pack('<HH',1,0));add('zip64-extra',x,False)
 for name,off in [('descriptor-crc',4),('descriptor-size',12)]:
  x,c,l,n=archive(method=8,descriptor=1);u32(x,l+n+off,1);add(name,x,False)
 x,c,l,n=archive(method=8,descriptor=1);del x[l+n:l+n+1];u32(x,len(x)-6,c-1);add('descriptor-truncated',x,False)
 x,c,l,n=archive(method=8);x[c:c]=b'x';u32(x,18,n+1);u32(x,c+1+20,n+1);u32(x,len(x)-6,c+1);add('payload-trailing',x,False)
 x,c,l,n=archive();central=bytes(x[c:-22]);x[c:c]=central;u16(x,len(x)-14,2);u16(x,len(x)-12,2);u32(x,len(x)-10,len(central)*2);add('duplicate',x,False)
 x,c,l,n=archive();u32(x,c+42,l);add('overlap',x,False)
 x,c,l,n=archive();x[c:c]=b'x';u32(x,len(x)-6,c+1);add('gap',x,False)
 x,*_=archive();add('cancel',x,False,cancel=True)
 (B/'central-cases.json').write_text(json.dumps({'provenance':'CC0 independently authored fixed ZIP structures; no parser-derived expectations','payload_hex':PAYLOAD.hex(),'cases':cases},indent=2)+'\n')
 (B/'central-cases.tsv').write_text(''.join('\t'.join([c['name'],c['file'],str(c['accept']).lower(),str(c['cancel']).lower(),c['payload_sha256'] or '-'])+'\n' for c in cases))
if __name__=='__main__':freeze()
