"""Serial offline source-conditioned screen; immutable run outputs and bounded host admission."""
from pathlib import Path
import json,hashlib,base64,subprocess,os,time,datetime,resource,sys
R=Path(__file__).resolve().parents[3];F=Path(__file__).parent;TC=Path('/home/isa/Android/atlas-toolchain')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=json.loads((F/'protocol.json').read_text());sources=json.loads((F.parent/'general-generation/sources.json').read_text()); original=json.loads((F.parent/'general-generation/protocol.json').read_text()); cases=original['cases']+p['probes']
assert sha(R/sources['pack_path'])==sources['pack_sha256']
out=R/'downloads/cross-model-support'/datetime.datetime.now(datetime.timezone.utc).strftime('run-%Y%m%dT%H%M%SZ');out.mkdir(parents=True);print(out,flush=True)
inputs=out/'inputs';inputs.mkdir();classes=out/'classes';classes.mkdir();enc=lambda s:base64.b64encode(s.encode()).decode()
(inputs/'cases.tsv').write_text(''.join(c['id']+'\t'+enc(c['question'])+'\n' for c in cases))
for c in cases:
 draft=c.get('draft')
 if draft is None:draft=json.loads((R/p['generator_run']/(c['id']+'.json')).read_text())['raw']
 (inputs/(c['id']+'.draft.txt')).write_text(draft)
 rows=[s for s in sources['sources'] if s['title'] in sources['pairs'][c['pair']]]
 (inputs/(c['id']+'.tsv')).write_text(''.join('\t'.join(enc(s[k]) for k in ['id','title','url','date','license','text'])+'\n' for s in rows))
files=[R/'android/app/src/main/java/org/pocketlore/app'/(n+'.java') for n in ['ResearchEngine','GeneralGroundedAnswer','CrossModelSupport','NativeRuntime']]+[F/'SupportHarness.java']
subprocess.run([TC/'jdk/bin/javac','-d',classes,*files],check=True)
lib=R/'downloads/scale-model-quality/host-buffer-v2-build/libpocketlore.so'
manifest={'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'inputs':{str(f.relative_to(R)):sha(f) for f in files+[F.parent/'general-generation/sources.json',F/'protocol.json',F/'run.py']},'runtime':{'path':str(lib),'sha256':sha(lib)},'scope':'Separate Qwen2.5 7B verifier of preserved Qwen3 4B drafts; CPU host, no production qualification','runs':[]}
manifest['verification_inputs']={f.name:sha(f) for f in inputs.iterdir()}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
for name in ['qwen25-7b']:
 pinfile=R/('tools/evaluation/model-capability/qwen3-4b.json' if name=='qwen3-4b' else 'tools/evaluation/scale-model-quality/qwen25-7b.json');pin=json.loads(pinfile.read_text());model=R/pin.get('path','downloads/model-capability/models/'+pin['filename'])
 assert model.stat().st_size==pin['bytes'] and sha(model)==pin['sha256']
 available=int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024
 if available<12_000_000_000:raise RuntimeError('Insufficient free host memory for bounded screen and active emulator margin')
 d=out/name;d.mkdir();cmd=[str(TC/'jdk/bin/java'),'-Xmx256m','-XX:MaxMetaspaceSize=128m','-XX:CompressedClassSpaceSize=64m','-XX:ReservedCodeCacheSize=64m','-Djava.library.path='+str(lib.parent),'-cp',str(classes),'org.pocketlore.app.SupportHarness',str(inputs),str(model),str(d)]
 def limits():resource.setrlimit(resource.RLIMIT_AS,(12_000_000_000,12_000_000_000));resource.setrlimit(resource.RLIMIT_CPU,(10800,10800))
 start=time.monotonic();samples=[]
 with (d/'stdout.txt').open('wb') as so,(d/'stderr.txt').open('wb') as se:
  proc=subprocess.Popen(cmd,stdout=so,stderr=se,env=dict(os.environ,POCKETLORE_HOST_THREADS='6'),preexec_fn=limits)
  print('START',name,proc.pid,flush=True)
  while proc.poll() is None:
   try:
    lines=Path(f'/proc/{proc.pid}/status').read_text().splitlines();row={'seconds':time.monotonic()-start,**{l.split(':')[0]:l.split(':')[1].strip() for l in lines if l.startswith(('VmRSS:','VmSwap:','VmHWM:'))}};samples.append(row)
    if int(row.get('VmRSS','0 kB').split()[0])*1024>p['rss_stop_bytes'] or row['seconds']>p['timeout_seconds']:proc.kill()
   except FileNotFoundError:pass
   time.sleep(1)
 (d/'memory.json').write_text(json.dumps(samples,indent=2)+'\n')
 receipt={'model':pin,'model_path':str(model),'exit_code':proc.returncode,'elapsed_s':time.monotonic()-start,'command':cmd,'files':{f.name:sha(f) for f in d.iterdir() if f.is_file()}}
 (d/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');manifest['runs'].append(receipt);(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('END',name,proc.returncode,flush=True)
print('DONE',flush=True)
