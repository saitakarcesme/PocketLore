"""Read only bounded GGUF metadata; no mmap, tensor read or inference."""
import hashlib,json,pathlib,struct,time
LIMIT=64*1024*1024

def inspect(path):
 start=time.monotonic();digest=hashlib.sha256()
 with path.open('rb') as f:
  def read(n):
   if n<0 or f.tell()+n>LIMIT or time.monotonic()-start>20: raise ValueError('Metadata bound exceeded')
   b=f.read(n)
   if len(b)!=n: raise ValueError('Truncated metadata')
   digest.update(b);return b
  def num(fmt):return struct.unpack('<'+fmt,read(struct.calcsize('<'+fmt)))[0]
  def string():
   n=num('Q')
   if n>1048576: raise ValueError('String bound exceeded')
   return read(n).decode('utf-8')
  formats={0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'?',10:'Q',11:'q',12:'d'}
  def value(kind):
   if kind in formats:return num(formats[kind])
   if kind==8:return string()
   if kind!=9:raise ValueError('Unknown metadata kind')
   typ=num('I');count=num('Q')
   if count>2000000 or typ==9:raise ValueError('Array bound exceeded')
   if typ in formats:read(struct.calcsize('<'+formats[typ])*count)
   elif typ==8:
    for _ in range(count):string()
   else:raise ValueError('Unknown array kind')
   return {'array_type':typ,'count':count}
  if read(4)!=b'GGUF':raise ValueError('Wrong magic')
  version=num('I');nt=num('Q');nm=num('Q')
  if version not in (2,3) or nt>10000 or nm>10000:raise ValueError('Header counts/version rejected')
  metadata={}
  for _ in range(nm):
   key=string();v=value(num('I'))
   if key in metadata:raise ValueError('Duplicate key')
   metadata[key]=v
  tensors=[]
  for _ in range(nt):
   name=string();nd=num('I')
   if not 1<=nd<=4:raise ValueError('Invalid dimensions')
   dims=[num('Q') for _ in range(nd)];kind=num('I');offset=num('Q')
   if not all(0<x<=1000000000 for x in dims):raise ValueError('Invalid dimension length')
   tensors.append(dict(name=name,dims=dims,ggml_type=kind,relative_data_offset=offset))
  return {'metadata':{k:v for k,v in metadata.items() if not k.startswith('tokenizer.')},'tensors':tensors,'header_bytes_read':f.tell(),'header_sha256':digest.hexdigest(),'gguf_version':version,'elapsed_seconds':time.monotonic()-start,'tensor_data_read':False}

if __name__=='__main__':
 import sys
 p=pathlib.Path(sys.argv[1]);oracle=json.loads(pathlib.Path(sys.argv[2]).read_text());before=p.stat();result=inspect(p);after=p.stat()
 assert (before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns)
 assert len(result['tensors'])==733 and result['metadata']['general.architecture']=='qwen35moe'
 expected=[{k:t[k] for k in ('name','dims','ggml_type','relative_data_offset')} for t in oracle['tensors']]
 assert result['tensors']==expected and result['metadata']==oracle['metadata'] and result['header_bytes_read']==oracle['header_end']
 result.update(model_bytes=after.st_size,oracle_sha256=hashlib.sha256(pathlib.Path(sys.argv[2]).read_bytes()).hexdigest(),full_weight_hash_recomputed=False,scope='Fresh bounded header identity against frozen tensor-layout oracle only')
 print(json.dumps(result,indent=2))
