#!/usr/bin/env python3
"""One serial host run, preserving per-case output and failed process receipts."""
from pathlib import Path
import base64,datetime,hashlib,json,os,platform,subprocess,sys
R=Path(__file__).resolve().parents[2];F=R/'tools/evaluation/model-capability'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'downloads/model-capability'/datetime.datetime.now(datetime.timezone.utc).strftime('run-%Y%m%dT%H%M%SZ');out.mkdir(parents=True)
 tc=Path(os.environ.get('POCKETLORE_TOOLCHAIN','/home/isa/Android/atlas-toolchain'))
 spec=json.loads((F/'protocol.json').read_text());inputs=out/'inputs';inputs.mkdir();classes=out/'classes';classes.mkdir()
 enc=lambda s:base64.b64encode(s.encode()).decode()
 (inputs/'cases.tsv').write_text(''.join(c['id']+'\t'+enc(c['question'])+'\n' for c in spec['cases']))
 for c in spec['cases']:(inputs/(c['id']+'.tsv')).write_text(''.join('\t'.join(enc(s[k]) for k in ['id','title','url','date','license','text'])+'\n' for s in c['sources']))
 source=R/'android/app/src/main/java/org/pocketlore/app'
 sources=[source/(n+'.java') for n in ['ResearchEngine','EvidencePrompt','AnswerEngine','NativeRuntime']]+[F/'CapabilityHarness.java']
 subprocess.run([str(tc/'jdk/bin/javac'),'-d',str(classes),*map(str,sources)],check=True)
 models=[('baseline','baseline.json','downloads/answers/model','qwen2.5-Apache-2.0.txt'),('qwen25-1.5b','qwen25.json','downloads/synthesis/model','synthesis-model-Apache-2.0.txt'),('qwen3-1.7b','qwen3.json','downloads/synthesis/model','synthesis-qwen3-Apache-2.0.txt')]
 lib=R/'downloads/model-capability/host-build/production/libpocketlore.so'
 receipts=[];manifest={'measurement':'LLMRig Linux CPU host JNI; no Android or phone execution','platform':platform.platform(),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'protocol_sha256':sha(F/'protocol.json'),'library_path':str(lib.relative_to(R)),'library_sha256':sha(lib),'source_hashes':{str(p.relative_to(R)):sha(p) for p in sources+[R/'android/app/src/main/cpp/runtime.cpp',R/'android/app/src/main/cpp/resource_budget.h',R/'tools/runtime/build-host.sh',R/'tools/runtime/host/CMakeLists.txt',R/'tools/evaluation/run_model_capability.py']},'receipts':receipts}
 (out/'host-meminfo-before.txt').write_text(Path('/proc/meminfo').read_text())
 (out/'cpuinfo.txt').write_text(Path('/proc/cpuinfo').read_text())
 for name,pinfile,folder,notice in models:
  pin=json.loads((F/pinfile).read_text());model=R/folder/pin['filename'];license=R/'android/app/src/main/assets/licenses'/notice
  assert model.stat().st_size==pin['bytes']<=4*1024**3 and sha(model)==pin['sha256']
  assert b'Apache License' in license.read_bytes()
  d=out/name;d.mkdir();cmd=[str(tc/'jdk/bin/java'),'-Xmx512m','-Djava.library.path='+str(lib.parent),'-cp',str(classes),'org.pocketlore.app.CapabilityHarness',str(inputs),str(model),str(d)]
  receipt={'model':name,'pin':pin,'path':str(model.relative_to(R)),'license_path':str(license.relative_to(R)),'license_sha256':sha(license),'command':cmd,'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
  print('START',name,out,flush=True)
  with (d/'stdout.txt').open('wb') as stdout,(d/'stderr.txt').open('wb') as stderr:
   try:receipt['exit_code']=subprocess.run(cmd,stdout=stdout,stderr=stderr,timeout=spec['execution']['timeout_seconds_per_model']).returncode
   except subprocess.TimeoutExpired:receipt['exit_code']=124;receipt['failure']='model process exceeded predeclared timeout; partial outputs preserved'
  receipt['end_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();receipt['artifact_hashes']={str(p.relative_to(out)):sha(p) for p in sorted(d.glob('*'))};receipts.append(receipt)
  (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('END',name,receipt['exit_code'],flush=True)
 (out/'host-meminfo-after.txt').write_text(Path('/proc/meminfo').read_text())
 print(out,flush=True)
 return int(any(r['exit_code'] for r in receipts))
if __name__=='__main__':sys.exit(main())
