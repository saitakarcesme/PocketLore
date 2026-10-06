"""Fixed synthetic generation and serial native probes. Never opens model assets."""
import pathlib,json,os,sys,hashlib,base64
from common import R,O,BINARIES,identity,version,sources,verify_sources,owned,preflight,atomic,freeze

def inputs():
 preflight();plan=json.loads((R/'docs/evidence/weight-fault-inputs/policy.json').read_text());manifest={}
 for name in ['default','random']:
  p=O/(name+'.bin');h=hashlib.sha256()
  with p.open('xb') as f:
   for off in range(0,plan['fixture_bytes'],plan['generation_chunk_bytes']):
    b=bytes(((i*73)^(i>>8)^(i>>16))&255 for i in range(off,off+plan['generation_chunk_bytes']));f.write(b);h.update(b)
   f.flush();os.fsync(f.fileno())
  with p.open('rb') as f:os.posix_fadvise(f.fileno(),0,0,os.POSIX_FADV_DONTNEED)
  manifest[name]={'path':str(p),'sha256':h.hexdigest(),'version':version(p),'bytes':p.stat().st_size}
 assert len({v['sha256'] for v in manifest.values()})==1
 atomic(O/'inputs.json',manifest)

def probes():
 frozen=json.loads((O/'frozen.json').read_text());verify_sources(frozen['source']);preflight()
 with (O/'attempt.json').open('x') as f:json.dump({'frozen':identity(O/'frozen.json')},f)
 report={'frozen':frozen,'runs':{},'errors':[],'model_access':False}
 try:
  for name in ['default','random','negative']:
   v=frozen['inputs']['default' if name=='negative' else name];assert version(v['path'])==v['version']
   out=O/('run-'+name);exe=R/'downloads/native-cache-build/host/fault-policy-controls';assert identity(exe)==frozen['binary'][str(exe.relative_to(R))]
   raw=owned.execute([str(exe),v['path'],v['sha256'],name,str(O/name)],out,90)
   # Retain execution first, even if subsequent observation reads fail.
   report['runs'][name]=raw;raw['collection_errors']=[];raw['observations']={};raw['raw_bytes']={};atomic(O/'runs.json',report)
   for path in [out/'stdout.log']+list(O.glob(name+'-*.json')):
    try:
     with path.open('rb') as f:data=f.read(4194305)
     raw['raw_bytes'][path.name]={'sha256':hashlib.sha256(data).hexdigest(),'base64':base64.b64encode(data).decode()}
     assert len(data)<=4194304,'Observation/log limit exceeded'
     if path.name=='stdout.log':raw['stdout']=data.decode('utf-8')
     else:raw['observations'][path.name]=data.decode('utf-8')
    except Exception as e:raw['collection_errors'].append(path.name+': '+repr(e))
   raw['post_input']=version(v['path']);raw['post_source']=sources();atomic(O/'runs.json',report)
   assert not raw['collection_errors'],raw['collection_errors']
   assert raw['exit']==0 and not raw.get('failure') and raw['post_input']==v['version'] and raw['post_source']==frozen['source'],name
 except Exception as e:report['errors'].append(type(e).__name__+': '+str(e))
 finally:atomic(O/'runs.json',report)
 print(json.dumps({'runs':list(report['runs']),'errors':report['errors']}));return int(bool(report['errors']))
if __name__=='__main__':
 mode=sys.argv[1]
 if mode=='inputs':inputs()
 elif mode=='freeze':freeze()
 elif mode=='probes':raise SystemExit(probes())
 else:raise ValueError(mode)
