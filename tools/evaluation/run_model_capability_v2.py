#!/usr/bin/env python3
"""Human-revised bounded host matrix; actual production controller/grammar."""
from pathlib import Path
import base64,concurrent.futures,datetime,hashlib,json,os,platform,subprocess,sys,time
R=Path(__file__).resolve().parents[2];F=R/'tools/evaluation/model-capability'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 spec=json.loads((F/'execution-v2.json').read_text());assert sha(R/spec['frozen_cases_file'])==spec['frozen_cases_sha256']
 cases=json.loads((R/spec['frozen_cases_file']).read_text())
 out=R/'downloads/model-capability'/datetime.datetime.now(datetime.timezone.utc).strftime('v2-%Y%m%dT%H%M%SZ');out.mkdir(parents=True)
 inputs=out/'inputs';inputs.mkdir();classes=out/'classes';classes.mkdir();enc=lambda s:base64.b64encode(s.encode()).decode()
 (inputs/'cases.tsv').write_text(''.join(c['id']+'\t'+enc(c['question'])+'\n' for c in cases['cases']))
 for c in cases['cases']:(inputs/(c['id']+'.tsv')).write_text(''.join('\t'.join(enc(s[k]) for k in ['id','title','url','date','license','text'])+'\n' for s in c['sources']))
 tc=Path(os.environ.get('POCKETLORE_TOOLCHAIN','/home/isa/Android/atlas-toolchain'));source=R/'android/app/src/main/java/org/pocketlore/app'
 sources=[source/(n+'.java') for n in ['ResearchEngine','EvidencePrompt','AnswerEngine','NativeRuntime']]+[F/'CapabilityHarness.java']
 subprocess.run([str(tc/'jdk/bin/javac'),'-d',str(classes),*map(str,sources)],check=True)
 lib=R/'downloads/model-capability/host-v2-build/libpocketlore.so';mem=Path('/proc/meminfo').read_text();available=int(next(x.split()[1] for x in mem.splitlines() if x.startswith('MemAvailable:')))*1024
 workers=2 if available>=12*1024**3 else 1
 manifest={'measurement':'LLMRig Linux CPU native-ISA host screen; no Android/phone execution','platform':platform.platform(),'execution_sha256':sha(F/'execution-v2.json'),'protocol_sha256':sha(F/'protocol.json'),'library_path':str(lib.relative_to(R)),'library_sha256':sha(lib),'host_threads_per_process':6,'max_concurrency':workers,'admission_mem_available_bytes':available,'source_hashes':{str(p.relative_to(R)):sha(p) for p in sources+[R/'android/app/src/main/cpp/runtime.cpp',R/'android/app/src/main/cpp/resource_budget.h',R/'tools/runtime/build-host.sh',R/'tools/runtime/host/CMakeLists.txt',Path(__file__).resolve()]},'receipts':[]}
 (out/'host-meminfo-before.txt').write_text(mem);(out/'cpuinfo.txt').write_text(Path('/proc/cpuinfo').read_text());(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 # Verify all model identities before launching any inference.
 for entry in spec['models']:
  pin=json.loads((F/entry['pin']).read_text());model=R/entry['path'];assert model.stat().st_size==pin['bytes']<=4*1024**3 and sha(model)==pin['sha256']
 def execute(entry):
  name=entry['id'];pin=json.loads((F/entry['pin']).read_text());model=R/entry['path'];license=R/entry['license_path'];d=out/name;d.mkdir()
  cmd=[str(tc/'jdk/bin/java'),'-Xmx512m','-Djava.library.path='+str(lib.parent),'-cp',str(classes),'org.pocketlore.app.CapabilityHarness',str(inputs),str(model),str(d)]
  receipt={'model':name,'pin':pin,'capacity_billion':entry['capacity_billion'],'path':entry['path'],'license_path':entry['license_path'],'license_sha256':sha(license),'command':cmd,'environment':{'POCKETLORE_HOST_THREADS':'6'},'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};print('START',name,out,flush=True)
  env=dict(os.environ,POCKETLORE_HOST_THREADS='6');start=time.monotonic()
  with (d/'stdout.txt').open('wb') as stdout,(d/'stderr.txt').open('wb') as stderr:
   process=subprocess.Popen(cmd,stdout=stdout,stderr=stderr,env=env);receipt['pid']=process.pid
   samples=[]
   while process.poll() is None:
    try:
     status=Path(f'/proc/{process.pid}/status').read_text();samples.append({'elapsed_s':time.monotonic()-start,**{line.split(':')[0]:line.split(':',1)[1].strip() for line in status.splitlines() if line.startswith(('VmRSS:','VmSwap:','VmHWM:','Threads:'))}})
    except FileNotFoundError:pass
    if time.monotonic()-start>spec['execution']['timeout_seconds_per_model']:
     process.kill();receipt['failure']='Predeclared host deadline; partial token files and active case retained';break
    time.sleep(1)
   receipt['exit_code']=process.wait()
  (d/'memory-samples.json').write_text(json.dumps(samples,indent=2)+'\n');receipt['end_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();receipt['artifact_hashes']={str(p.relative_to(out)):sha(p) for p in sorted(d.glob('*'))}
  (d/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('END',name,receipt['exit_code'],flush=True);return receipt
 with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
  futures=[pool.submit(execute,e) for e in spec['models']]
  for f in concurrent.futures.as_completed(futures):
   manifest['receipts'].append(f.result());manifest['receipts'].sort(key=lambda r:[e['id'] for e in spec['models']].index(r['model']))
   (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 (out/'host-meminfo-after.txt').write_text(Path('/proc/meminfo').read_text());print(out,flush=True)
 return int(any(r['exit_code'] for r in manifest['receipts']))
if __name__=='__main__':sys.exit(main())
