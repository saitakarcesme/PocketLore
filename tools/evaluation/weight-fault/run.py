"""Fixed synthetic generation and serial native probes. Never opens model assets."""
import pathlib,json,os,sys,hashlib
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
   raw['stdout']=(out/'stdout.log').read_text();raw['observations']={p.name:p.read_text() for p in O.glob(name+'-*.json') if p.is_file()};raw['post_input']=version(v['path']);raw['post_source']=sources()
   report['runs'][name]=raw;atomic(O/'runs.json',report)
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
