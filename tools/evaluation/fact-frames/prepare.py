"""Replay sealed drafts through the frozen frame controller; never regenerates old prose."""
from pathlib import Path
import base64,hashlib,json,subprocess,sys,time,shutil,os
R=Path(__file__).resolve().parents[3];F=Path(__file__).parent;TC=Path('/home/isa/Android/atlas-toolchain');PRIOR=R/'docs/evidence/independent-linking/scoring'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def enc(s):return base64.b64encode(s.encode()).decode()
def java_sources():return [R/'android/app/src/main/java/org/pocketlore/app'/(n+'.java') for n in ['FactFrames','BoundAnswer','EvidenceLinker','ObligationAnswer','ResearchEngine','EvidencePrompt','AnswerEngine','NativeRuntime']]+[R/'tools/evaluation/scale-model-quality/ScaleHarness.java',R/'tools/evaluation/obligation-binding/BindingHarness.java',F/'FrameHarness.java']
if __name__=='__main__':
 run=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=False);assert json.loads((run/'receipt.json').read_text())['exit_code']==0;inputs=out/'inputs';shutil.copytree(PRIOR/'inputs',inputs);origins=json.loads((PRIOR/'origins.json').read_text());rows=(inputs/'drafts.tsv').read_text().splitlines();fixtures=json.loads((F/'fixtures.json').read_text())
 for c in fixtures['cases']:
  id=c['id'];path=run/'results'/(id+'.json');v=json.loads(path.read_text());rows.append('\t'.join([id,enc(c['question']),enc(v['draft']['raw']),str(v['draft']['tokens'])]));origins[id]={'path':str(path.relative_to(R)),'sha256':sha(path),'type':'actual new generated draft'}
  source=''.join('\t'.join(enc(s[k] if k!='edition' else fixtures['source_edition_sha256']) for k in ['edition','id','source_sha256','sha256','title','date','license','text'])+'\n' for s in c['sources']);(inputs/(id+'.tsv')).write_text(source)
  probe='t'+id[1:];rows.append('\t'.join([probe,enc('Is this complete statement supported by the available evidence?'),enc('@PROBE'),'1',enc(c['sources'][0]['id']),enc(c['constructed_probe'])]));(inputs/(probe+'.tsv')).write_text(source);origins[probe]={'path':str((F/'fixtures.json').relative_to(R)),'sha256':sha(F/'fixtures.json'),'case':id,'type':'constructed frame regression, not generated success or corpus'}
 (inputs/'drafts.tsv').write_text('\n'.join(rows)+'\n');(out/'origins.json').write_text(json.dumps(origins,indent=2)+'\n');classes=out/'classes';classes.mkdir();sources=java_sources();subprocess.run([TC/'jdk/bin/javac','-d',classes,*sources],check=True)
 manifest={'sources':{str(p.relative_to(R)):sha(p) for p in sources+[F/'protocol.json',F/'fixtures.json',F/'prepare.py']},'inputs':{str(p.relative_to(out)):sha(p) for p in inputs.glob('*')},'origins_sha256':sha(out/'origins.json'),'revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()};(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 command=[str(TC/'jdk/bin/java'),'-Xmx256m','-cp',str(classes),'org.pocketlore.app.FrameHarness',str(inputs),str(out/'results')];start=time.monotonic()
 with (out/'stdout.txt').open('w') as stdout,(out/'stderr.txt').open('w') as stderr:
  process=subprocess.Popen(command,stdout=stdout,stderr=stderr)
  while True:
   pid,status,usage=os.wait4(process.pid,os.WNOHANG)
   if pid:break
   if time.monotonic()-start>120:process.kill()
   time.sleep(.02)
  process.returncode=os.waitstatus_to_exitcode(status)
 (out/'parser-memory.json').write_text(json.dumps({'maximum_rss_kib':usage.ru_maxrss,'user_cpu_seconds':usage.ru_utime,'system_cpu_seconds':usage.ru_stime,'measurement':'os.wait4 usage for Java replay child only; no PSS or swap snapshot, not Android'},indent=2)+'\n')
 (out/'receipt.json').write_text(json.dumps({'exit_code':process.returncode,'command':command,'elapsed_s':time.monotonic()-start,'artifacts':{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and 'classes' not in p.parts}},indent=2)+'\n');print('Frame replay',process.returncode,out);raise SystemExit(process.returncode)
