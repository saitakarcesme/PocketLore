"""Single bounded synthetic policy execution; never opens a model asset."""
import json,pathlib,sys,hashlib,os,base64
from common import R,O,BINARIES,identity,version,sources,source_check,owned,atomic,freeze

def fixture(p,size):
 h=hashlib.sha256()
 with p.open('xb') as f:
  for off in range(0,size,1048576):
   b=bytes(((i*73)^(i>>8)^(i>>16))&255 for i in range(off,off+1048576));h.update(b);f.write(b)
  f.flush();os.fsync(f.fileno())
 with p.open('rb') as f:os.posix_fadvise(f.fileno(),0,0,os.POSIX_FADV_DONTNEED)
 return {'path':str(p),'sha256':h.hexdigest(),'version':version(p)}
def collect(out,prefix,raw):
 raw['stream_contract']='stdout_and_stderr_combined_by_supervisor';raw['observations']={};raw['raw_bytes']={};raw['collection_errors']=[]
 for p in [out/'stdout.log']+sorted(prefix.parent.glob(prefix.name+'-*.json')):
  try:
   with p.open('rb') as g:b=g.read(4194305)
   raw['raw_bytes'][p.name]={'sha256':hashlib.sha256(b).hexdigest(),'base64':base64.b64encode(b).decode()};assert len(b)<=4194304
   if p.name in ['stdout.log','stderr.log']:raw[p.name[:-4]]=b.decode()
   else:raw['observations'][p.name]=b.decode()
  except Exception as e:raw['collection_errors'].append(repr(e))

def main():
 if sys.argv[1]=='freeze':freeze();return 0
 f=json.loads((O/'frozen-v2.json').read_text());r={'frozen':f,'inputs':{},'runs':{},'errors':[],'model_access':False}
 with (O/'attempt.json').open('x') as g:json.dump({'frozen':identity(O/'frozen-v2.json'),'task':f['policy']['task']},g)
 try:
  source_check(f['source']);r['preflight']=owned.preflight()
  bad=O/'collection-control';bad.mkdir();(bad/'stdout.log').write_bytes(b'\xff\x00');(bad/'none-unreadable.json').mkdir();control={};collect(bad,bad/'none',control);r['collection_control']=control;assert len(control['collection_errors'])==2 and control['raw_bytes']['stdout.log']['base64']=='/wA='
  for name in ['force','retain']:r['inputs'][name]=fixture(O/(name+'.bin'),33554432);atomic(O/'runs.json',r)
  assert r['inputs']['force']['sha256']==r['inputs']['retain']['sha256']
  for name in ['force','retain','no-progress','mincore-failure','advice-failure','tail','remap']:
   inp=r['inputs']['force' if name=='force' else 'retain'];out=O/('run-'+name);prefix=O/name
   exe=R/BINARIES[-1];assert identity(exe)==f['binary'][BINARIES[-1]]
   raw=owned.execute([str(exe),inp['path'],inp['sha256'],name,str(prefix)],out,45);r['runs'][name]=raw;atomic(O/'runs.json',r)
   collect(out,prefix,raw)
   raw['post_input']=version(inp['path']);raw['post_source']=sources();atomic(O/'runs.json',r)
   assert raw['exit']==0 and not raw.get('failure') and not raw['collection_errors'] and raw['post_input']==inp['version'] and raw['post_source']==f['source'],name
  fault=fixture(O/'fault.bin',67108864);x=owned.execute([str(R/BINARIES[-2]),fault['path'],fault['sha256'],'negative',str(O/'fault-negative')],O/'fault-run',30)
  r['fault_controls']={'run':x,'stdout':(O/'fault-run/stdout.log').read_text(),'input':fault};assert x['exit']==0 and not x.get('failure')
  # Prior actual ownership/scalar/async/teardown controls, current linked code.
  small=fixture(O/'lifecycle.bin',4194304);raw=owned.execute([str(R/BINARIES[0]),small['path'],small['sha256'],'4194304',str(O/'lifecycle'),'0'],O/'lifecycle-run',30)
  r['lifecycle']={'run':raw,'stdout':(O/'lifecycle-run/stdout.log').read_text(),'input':small};assert raw['exit']==0 and not raw.get('failure')
  for name,code,seconds,inject in [('hung','import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(30)',.3,False),('read-error','import time;time.sleep(30)',2,True)]:
   x=owned.execute([sys.executable,'-c',code],O/name,seconds,inject);r[name]=x;assert x['cleanup'][-1]['action']=='REAPED' and not pathlib.Path('/proc/'+str(x['pid'])).exists()
 except Exception as e:r['errors'].append(type(e).__name__+': '+str(e))
 finally:atomic(O/'runs.json',r)
 print(json.dumps({'errors':r['errors'],'runs':list(r['runs'])}));return int(bool(r['errors']))
if __name__=='__main__':raise SystemExit(main())
