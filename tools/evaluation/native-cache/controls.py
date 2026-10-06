"""Engineered owned-process and identity controls, before model sampling."""
import json,pathlib,sys,subprocess,time,uuid,copy
from contract import ROOT,identity,source_manifest,source_contract,elf_machine
from run import BASE,execute
from check import validate_policy
sys.path.insert(0,str(ROOT/'tools/runtime/sparse'))
from binding import canonical_key,derivation_inputs,validate_cache

def main():
 out=BASE/('controls-'+uuid.uuid4().hex[:8]);out.mkdir();results=[]
 for name,script,seconds,inject in [
  ('hung','import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(30)',.3,False),
  ('read-error','import time;time.sleep(30)',10,True),
  ('failed','import sys;sys.exit(7)',2,False)]:
  r=execute([sys.executable,'-c',script],out/name,seconds,inject)
  assert r['cleanup'][-1]['action']=='REAPED' and 'cleanup_failure' not in r
  assert not pathlib.Path(f"/proc/{r['pid']}").exists(),'Owned child remained'
  if name=='hung':assert [x['action'] for x in r['cleanup']]==['TERM','KILL','REAPED']
  if name=='read-error':assert 'OSError' in r['failure']
  if name=='failed':assert r['exit']==7
  results.append({'name':name,'receipt':r})
 for name,kwargs in [('initial-stat',{'inject_start_error':True}),('post-identity',{'inject_after_error':True})]:
  r=execute([sys.executable,'-c','import time;time.sleep(.2)'],out/name,2,**kwargs)
  assert r['cleanup'][-1]['action']=='REAPED' and not pathlib.Path(f"/proc/{r['pid']}").exists()
  assert r.get('failure') and (out/name/'execution.json').exists()
  results.append({'name':name,'receipt':r})
 for label,code in [('cancel',12),('expiry',13)]:
  r=execute([str(ROOT/'downloads/native-cache-build/host/sparse-host'),'--cleanup-'+label+'-control'],out/('host-'+label),10)
  raw=(out/('host-'+label)/'stdout.log').read_text()
  assert r['exit']==code and 'backend_released' in raw and 'released_after_scope' in raw and 'POCKETLORE_PHASE loading' not in raw
  results.append({'name':'host-'+label+'-exception','execution':r,'stdout':raw})
 s=source_manifest();assert source_contract(s)
 for name,mutate in [('empty',lambda d:d.clear()),('missing',lambda d:d.pop(next(iter(d)))),('source-text',lambda d:d[next(iter(d))].update(text='changed'))]:
  bad=copy.deepcopy(s);mutate(bad)
  try:source_contract(bad)
  except AssertionError:results.append({'name':name,'refused':True});continue
  raise AssertionError('Source control passed '+name)
 # Owned files exercise changed inode, same-size mutation, and post-spawn compare.
 file=out/'binding.txt';file.write_text('original');a=identity(file);file.write_text('modified');assert a!=identity(file)
 twin=out/'same-bytes.txt';twin.write_text('modified');assert identity(file)['version']['inode']!=identity(twin)['version']['inode']
 results.append({'name':'version-hash-inode-mutations','refused':True,'before':a,'after':identity(file),'twin':identity(twin)})
 inputs=derivation_inputs(ROOT);key=canonical_key(inputs)
 for name in inputs:
  bad=copy.deepcopy(inputs);bad[name]['engineered-change']=1;assert canonical_key(bad)!=key
 assert canonical_key({'a':{'x':'bc'}})!=canonical_key({'ab':{'x':'c'}})
 results.append({'name':'all-derivation-input-mutations','count':len(inputs),'refused':True,'inputs':inputs,'key':key})
 # Exercise the actual cached-derivation validator only on owned tiny files.
 cache=out/'cache';(cache/'source').mkdir(parents=True);(cache/'source/file.txt').write_text('exact')
 manifest={'inputs':inputs,'input_sha256':key,'files':{'file.txt':identity(cache/'source/file.txt')['sha256']}}
 (cache/'native-manifest.json').write_text(json.dumps(manifest));validate_cache(cache,inputs)
 for name in ['stale-input','changed-file','missing-file-set']:
  m=copy.deepcopy(manifest)
  if name=='stale-input':m['input_sha256']='0'*64
  if name=='changed-file':m['files']['file.txt']='0'*64
  if name=='missing-file-set':m['files']={}
  (cache/'native-manifest.json').write_text(json.dumps(m))
  try:validate_cache(cache,inputs)
  except AssertionError:results.append({'name':name,'refused':True});continue
  raise AssertionError('Stale cache passed')
 # ELF class/machine controls use owned headers, never mutate shipped binaries.
 elf=out/'machine.elf';header=bytearray(64);header[:6]=b'\x7fELF\x02\x01';header[18:20]=(62).to_bytes(2,'little');elf.write_bytes(header);assert elf_machine(elf)==62
 header[18:20]=(183).to_bytes(2,'little');elf.write_bytes(header);assert elf_machine(elf)!=62
 header[4]=1;elf.write_bytes(header)
 try:elf_machine(elf)
 except AssertionError:results.append({'name':'wrong-elf-machine-and-class','refused':True})
 else:raise AssertionError('Wrong ELF class accepted')
 policy=json.loads((ROOT/'docs/evidence/native-cache-inputs/repair-2/policy.json').read_text());layout=json.loads((ROOT/'docs/evidence/native-cache-inputs/repair-2/tensor-layout.json').read_text());assert validate_policy(policy,layout)
 bad=copy.deepcopy(policy);bad['offset']=0
 try:validate_policy(bad,layout)
 except AssertionError:results.append({'name':'metadata-window-refused','refused':True})
 else:raise AssertionError('Metadata window accepted as tensor')
 # Native fixture uses real mmap implementation and all native exception guards.
 fixture=out/'fixture.bin';fixture.write_bytes(bytes(range(256))*16384);digest=identity(fixture)['sha256']
 exe=ROOT/'downloads/native-cache-build/host/native-cache-controls'
 before=source_manifest();r=execute([str(exe),str(fixture),digest,'4194304',str(out/'native'),'0'],out/'native-process',30)
 assert before==source_manifest();assert r['exit']==0 and not r.get('failure')
 raw=(out/'native-process/stdout.log').read_text()
 assert 'deferred-destructor-observation' in raw and 'exception-unmapped' in raw
 results.append({'name':'native-fixture','execution':r,'stdout':raw,'source':before})
 packet={'status':'PRE_SAMPLE_CONTROLS_PASS','results':results};(out/'receipt.json').write_text(json.dumps(packet,indent=2));(BASE/'controls-path.txt').write_text(str(out/'receipt.json'));print(out)
if __name__=='__main__':main()
