"""Run historical native audits only after a successful complete main-process exit."""
from pathlib import Path
import base64,datetime,hashlib,json,os,shutil,subprocess,sys,time
R=Path(__file__).resolve().parents[3];F=Path(__file__).parent;TC=Path('/home/isa/Android/atlas-toolchain')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
main=Path(sys.argv[1]);receipt=json.loads((main/'receipt.json').read_text());assert receipt['exit_code']==0 and not receipt['killed'];assert len(list((main/'results').glob('[sn][0-9][0-9].json')))==60
assert all(sha(main/p)==h for p,h in receipt['artifacts'].items());model=R/'downloads/model-capability/models/Qwen3-4B-Q4_K_M.gguf';assert sha(model)==json.loads((F/'execution.json').read_text())['model_sha256']
assert int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024>=8*1024**3
out=R/'downloads/obligation-binding'/datetime.datetime.now(datetime.timezone.utc).strftime('history-%Y%m%dT%H%M%SZ');out.mkdir();print(out,flush=True);inputs=out/'inputs';shutil.copytree(main/'inputs',inputs);classes=out/'classes';classes.mkdir();enc=lambda s:base64.b64encode(s.encode()).decode();fixtures=json.loads((F/'history.json').read_text())
(inputs/'history.tsv').write_text(''.join(x['id']+'\t'+x['case_id']+'\t'+enc(x['question'])+'\n' for x in fixtures))
for x in fixtures:
 assert sha(R/x['original_path'])==x['original_sha256']
 (inputs/(x['id']+'.claims.tsv')).write_text(''.join(str(c['obligation'])+'\t'+','.join(map(str,c['paragraphs']))+'\t'+enc(c['subject'])+'\t'+enc(c['qualifier'])+'\t'+enc(c['claim'])+'\n' for c in x['claims']))
sources=[R/'android/app/src/main/java/org/pocketlore/app'/(n+'.java') for n in ['BoundAnswer','ObligationAnswer','ResearchEngine','EvidencePrompt','AnswerEngine','NativeRuntime']]+[R/'tools/evaluation/scale-model-quality/ScaleHarness.java',F/'BindingHarness.java',F/'HistoryHarness.java'];subprocess.run([TC/'jdk/bin/javac','-d',classes,*sources],check=True)
lib=R/'downloads/scale-model-quality/host-build/libpocketlore.so';cmd=[str(TC/'jdk/bin/java'),'-Xmx512m','-Djava.library.path='+str(lib.parent),'-cp',str(classes),'org.pocketlore.app.HistoryHarness',str(inputs),str(model),str(out/'results')];manifest={'fixture_sha256':sha(F/'history.json'),'model_sha256':sha(model),'library_sha256':sha(lib),'source_hashes':{str(p.relative_to(R)):sha(p) for p in sources+[F/'run_history.py']},'stage':'Historical typed-wrapper native audit, no fresh generation credit','command':cmd};(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
start=time.monotonic();samples=[];killed=''
with (out/'stdout.txt').open('w') as stdout,(out/'stderr.txt').open('w') as stderr:
 p=subprocess.Popen(cmd,stdout=stdout,stderr=stderr,env=dict(os.environ,POCKETLORE_HOST_THREADS='6'))
 while p.poll() is None:
  try:
   status=Path(f'/proc/{p.pid}/status').read_text();s={'elapsed_s':time.monotonic()-start,**{x.split(':')[0]:x.split(':',1)[1].strip() for x in status.splitlines() if x.startswith(('VmRSS:','VmSwap:','VmHWM:'))}};samples.append(s)
   if int(s.get('VmRSS','0').split()[0])*1024>8*1024**3:killed='RSS limit';p.kill()
  except FileNotFoundError:pass
  if time.monotonic()-start>3600:killed='Time limit';p.kill()
  time.sleep(1)
 code=p.wait()
(out/'memory.json').write_text(json.dumps(samples,indent=2)+'\n');(out/'receipt.json').write_text(json.dumps({'exit_code':code,'killed':killed,'elapsed_s':time.monotonic()-start,'artifacts':{str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and 'classes' not in p.parts}},indent=2)+'\n');print('DONE',code,out,flush=True);raise SystemExit(code)
