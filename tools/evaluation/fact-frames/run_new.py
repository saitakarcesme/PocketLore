"""Single fixed CPU host run; immutable inputs, stage receipts and sampled RSS/swap."""
from pathlib import Path
import base64,datetime,hashlib,json,os,subprocess,time
R=Path(__file__).resolve().parents[3];F=Path(__file__).parent;TC=Path('/home/isa/Android/atlas-toolchain')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def available():return int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024
assert sha(F/'fixtures.json')==(F/'fixtures.sha256').read_text().strip()
new=json.loads((F/'fixtures.json').read_text());old=json.loads((R/'tools/evaluation/scale-model-quality/protocol.json').read_text())
model=R/'downloads/model-capability/models/Qwen3-4B-Q4_K_M.gguf';spec=json.loads((F/'protocol.json').read_text());assert sha(model)==spec['generator_sha256'];assert available()>=8*1024**3
out=R/'downloads/fact-frames'/datetime.datetime.now(datetime.timezone.utc).strftime('run-%Y%m%dT%H%M%SZ');out.mkdir(parents=True);print(out,flush=True);inputs=out/'inputs';inputs.mkdir();classes=out/'classes';classes.mkdir();enc=lambda s:base64.b64encode(s.encode()).decode();cases=new['cases'];edition=old['source_edition_sha256']
(inputs/'cases.tsv').write_text(''.join(c['id']+'\t'+enc(c['question'])+'\n' for c in cases))
for c in cases:(inputs/(c['id']+'.tsv')).write_text(''.join('\t'.join(enc(s[k] if k!='edition' else edition) for k in ['edition','id','source_sha256','sha256','title','date','license','text'])+'\n' for s in c['sources']))
sources=[R/'android/app/src/main/java/org/pocketlore/app'/(n+'.java') for n in ['BoundAnswer','ObligationAnswer','ResearchEngine','EvidencePrompt','AnswerEngine','NativeRuntime']]+[R/'tools/evaluation/scale-model-quality/ScaleHarness.java',R/'tools/evaluation/obligation-binding/BindingHarness.java',F/'FrameDraftHarness.java',R/'android/app/src/main/java/org/pocketlore/app/FactFrames.java']
subprocess.run([TC/'jdk/bin/javac','-d',classes,*sources],check=True)
lib=R/'downloads/scale-model-quality/host-build/libpocketlore.so';manifest={'stage':'CPU host candidate, not Android','protocol_sha256':sha(F/'fixtures.json'),'execution_sha256':sha(F/'protocol.json'),'model_sha256':sha(model),'library_sha256':sha(lib),'sources':{str(p.relative_to(R)):sha(p) for p in sources+[F/'run_new.py']},'git_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'available_start':available()}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(out/'memory-before.txt').write_text(Path('/proc/meminfo').read_text())
cmd=[str(TC/'jdk/bin/java'),'-Xmx512m','-Djava.library.path='+str(lib.parent),'-cp',str(classes),'org.pocketlore.app.FrameDraftHarness',str(inputs),str(model),str(out/'results')]
with (out/'stdout.txt').open('w') as stdout,(out/'stderr.txt').open('w') as stderr:
 p=subprocess.Popen(cmd,stdout=stdout,stderr=stderr,env=dict(os.environ,POCKETLORE_HOST_THREADS='6'));start=time.monotonic();samples=[];killed=''
 while p.poll() is None:
  try:
   status=Path(f'/proc/{p.pid}/status').read_text();s={'elapsed_s':time.monotonic()-start,**{x.split(':')[0]:x.split(':',1)[1].strip() for x in status.splitlines() if x.startswith(('VmRSS:','VmHWM:','VmSwap:','Threads:'))}};samples.append(s)
   if int(s.get('VmRSS','0').split()[0])*1024>8*1024**3:killed='RSS admission exceeded';p.kill()
  except FileNotFoundError:pass
  if time.monotonic()-start>7200:killed='Time budget exceeded';p.kill()
  time.sleep(1)
 code=p.wait()
(out/'memory.json').write_text(json.dumps(samples,indent=2)+'\n');(out/'memory-after.txt').write_text(Path('/proc/meminfo').read_text());receipt={'exit_code':code,'killed':killed,'elapsed_s':time.monotonic()-start,'command':cmd,'artifacts':{str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and 'classes' not in p.parts}}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('DONE',code,out,flush=True);raise SystemExit(code)
