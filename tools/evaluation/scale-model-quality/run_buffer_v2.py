#!/usr/bin/env python3
"""Bounded CPU matrix, immutable inputs, raw partials, actual memory and identities."""
from pathlib import Path
import base64,datetime,hashlib,json,os,platform,subprocess,time
R=Path(__file__).resolve().parents[3];F=Path(__file__).resolve().parent;TC=Path('/home/isa/Android/atlas-toolchain')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def available():return int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024
models=[('qwen25-7b',F/'qwen25-7b.json',None,'tools/evaluation/scale-model-quality/qwen25-7b-LICENSE'),('qwen15-moe',F/'qwen15-moe.json',None,'tools/evaluation/scale-model-quality/qwen15-moe-LICENSE')]
assert sha(F/'protocol.json')==(F/'protocol.sha256').read_text().strip();protocol=json.loads((F/'protocol.json').read_text());spec=json.loads((F/'execution-buffer-v2.json').read_text())
out=R/'downloads/scale-model-quality'/datetime.datetime.now(datetime.timezone.utc).strftime('buffer-v2-%Y%m%dT%H%M%SZ');out.mkdir();print(out,flush=True);inputs=out/'inputs';inputs.mkdir();classes=out/'classes';classes.mkdir();enc=lambda s:base64.b64encode(s.encode()).decode()
(inputs/'cases.tsv').write_text(''.join(c['id']+'\t'+enc(c['question'])+'\n' for c in protocol['cases']))
for c in protocol['cases']:(inputs/(c['id']+'.tsv')).write_text(''.join('\t'.join(enc(s[k]) for k in ['id','title','url','date','license','text'])+'\n' for s in c['sources']))
sources=[R/'android/app/src/main/java/org/pocketlore/app'/(n+'.java') for n in ['ResearchEngine','EvidencePrompt','AnswerEngine','ObligationAnswer','NativeRuntime']]+[F/'ScaleHarness.java']
subprocess.run([TC/'jdk/bin/javac','-d',classes,*sources],check=True)
lib=R/'downloads/scale-model-quality/host-buffer-v2-build/libpocketlore.so';startup=available();limit=startup-2*1024**3
manifest={'stage':'CPU host oracle-evidence screen, not deployed Android','platform':platform.platform(),'startup_available_bytes':startup,'protocol_sha256':sha(F/'protocol.json'),'execution_sha256':sha(F/'execution-buffer-v2.json'),'library_sha256':sha(lib),'source_hashes':{str(p.relative_to(R)):sha(p) for p in sources+[R/'android/app/src/main/cpp/runtime.cpp',R/'android/app/src/main/cpp/resource_budget.h',F/'run_buffer_v2.py']},'receipts':[]}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(out/'host-memory-before.txt').write_text(Path('/proc/meminfo').read_text())
pending=[]
for name,pinfile,path,licensepath in models:
 pin=json.loads(pinfile.read_text());path=path or pin['path'];model=R/path;assert model.stat().st_size==pin['bytes']<=6_000_000_000 and sha(model)==pin['sha256'];pending.append(dict(id=name,pin=pin,path=path,license=licensepath,license_sha256=sha(R/licensepath)))
active=[]
while pending or active:
 if pending and len(active)<1:
  entry=pending[0];reserve=10_000_000_000 if entry['id']=='qwen25-7b' else 10_500_000_000
  if available()>=reserve+2*1024**3 and sum(a['reserve'] for a in active)+reserve<=limit:
   pending.pop(0);d=out/entry['id'];d.mkdir();env=dict(os.environ,POCKETLORE_HOST_THREADS='6');cmd=[str(TC/'jdk/bin/java'),'-Xmx512m','-Djava.library.path='+str(lib.parent),'-cp',str(classes),'org.pocketlore.app.ScaleHarness',str(inputs),str(R/entry['path']),str(d)]
   stdout=(d/'stdout.txt').open('wb');stderr=(d/'stderr.txt').open('wb');p=subprocess.Popen(cmd,stdout=stdout,stderr=stderr,env=env)
   active.append({'entry':entry,'process':p,'dir':d,'start':time.monotonic(),'reserve':reserve,'samples':[],'stdout':stdout,'stderr':stderr,'command':cmd,'available_at_start':available(),'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()});print('START',entry['id'],p.pid,flush=True)
  elif not active:
   raise RuntimeError('Host resource admission cannot fit next model with declared reserve; no inference launched')
 for a in list(active):
  p=a['process'];d=a['dir'];elapsed=time.monotonic()-a['start']
  try:
   status=Path(f'/proc/{p.pid}/status').read_text();a['samples'].append({'elapsed_s':elapsed,**{line.split(':')[0]:line.split(':',1)[1].strip() for line in status.splitlines() if line.startswith(('VmRSS:','VmSwap:','VmHWM:','Threads:'))}})
  except FileNotFoundError:pass
  if a['samples'] and int(a['samples'][-1].get('VmRSS','0 kB').split()[0])*1024>10_500_000_000 and p.poll() is None:p.kill();a['timeout']=True
  if elapsed>spec['timeout_seconds_per_model'] and p.poll() is None:p.kill();a['timeout']=True
  if p.poll() is not None:
   code=p.wait();a['stdout'].close();a['stderr'].close();(d/'memory.json').write_text(json.dumps(a['samples'],indent=2)+'\n')
   receipt={**a['entry'],'exit_code':code,'timeout':a.get('timeout',False),'start_utc':a['start_utc'],'elapsed_s':elapsed,'available_at_start':a['available_at_start'],'threads':6,'command':a['command'],'artifact_hashes':{p.name:sha(p) for p in d.iterdir()}}
   (d/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');manifest['receipts'].append(receipt);(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');active.remove(a);print('END',a['entry']['id'],code,elapsed,flush=True)
 time.sleep(1)
(out/'host-memory-after.txt').write_text(Path('/proc/meminfo').read_text());print('DONE',out,flush=True)
raise SystemExit(int(any(r['exit_code']!=0 for r in manifest['receipts'])))
