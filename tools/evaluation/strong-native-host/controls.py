"""Current linked scalar and real native lifecycle controls; never model inference."""
import pathlib,json,sys,uuid,importlib.util
from support import R,O,BINARIES,identity,sources,owned,atomic,collect_outputs

def main():
 out=O/('controls-'+uuid.uuid4().hex[:8]);out.mkdir();results=[];before=sources()
 bad=out/'collection-fixture';bad.mkdir();(bad/'stdout').mkdir();(bad/'bad.json').write_bytes(b'\xff\x00');case={};collect_outputs(bad,case);assert len(case['collection_errors'])==2 and case['raw_bytes']['bad.json']['base64']=='/wA='
 atomic(bad/'receipt.json',case);results.append({'name':'collection-failure-retention','receipt':case})
 for name,script,deadline,inject in [('hung','import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(30)',.3,False),('read-error','import time;time.sleep(30)',2,True),('exit-error','import sys;sys.exit(7)',2,False)]:
  r=owned.execute([sys.executable,'-c',script],out/name,deadline,inject)
  assert r['cleanup'][-1]['action']=='REAPED' and not pathlib.Path(f"/proc/{r['pid']}").exists()
  if name=='hung':assert [v['action'] for v in r['cleanup']]==['TERM','KILL','REAPED']
  if name=='exit-error':assert r['exit']==7
  if name=='read-error':assert r.get('failure')
  results.append({'name':name,'execution':r})
 for name in ['cancel','expiry']:
  r=owned.execute([str(R/BINARIES[1]),'--cleanup-'+name+'-control'],out/name,10)
  raw=(out/name/'stdout.log').read_text();assert r['exit']==(12 if name=='cancel' else 13) and 'backend_released' in raw and 'released_after_scope' in raw
  results.append({'name':name,'execution':r,'stdout':raw})
 fixture=out/'fixture.bin';fixture.write_bytes(bytes(range(256))*16384)
 r=owned.execute([str(R/BINARIES[0]),str(fixture),identity(fixture)['sha256'],'4194304',str(out/'native'),'0'],out/'native-process',30)
 raw=(out/'native-process/stdout.log').read_text();assert r['exit']==0 and not r.get('failure')
 for name in ['scalar-order-byte-oracle','scalar-multitoken','scalar-live-reader','scalar-exception','scalar-cancel','deferred-destructor-observation','exception-unmapped','wrong-inode','wrong-hash','deadline','async-reader','alias-mapping']:assert name in raw,name
 assert sources()==before
 results.append({'name':'native-scalar-mmap','execution':r,'stdout':raw,'raw':{p.name:p.read_text() for p in out.glob('native*') if p.is_file()}})
 packet={'status':'CURRENT_NATIVE_CONTROLS_PASS','source':before,'results':results};atomic(out/'receipt.json',packet);(O/'controls-path.txt').write_text(str(out/'receipt.json'));print(packet['status'])
if __name__=='__main__':main()
