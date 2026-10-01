"""Prepare a byte-pinned replay without autoregressive generation of old questions."""
from pathlib import Path
import json,base64,hashlib,subprocess,sys
R=Path(__file__).resolve().parents[3];F=Path(__file__).parent;TC=Path('/home/isa/Android/atlas-toolchain');E=R/'docs/evidence/obligation-binding'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def enc(s):return base64.b64encode(s.encode()).decode()
def compile_to(classes):
 sources=[R/'android/app/src/main/java/org/pocketlore/app'/(n+'.java') for n in ['BoundAnswer','EvidenceLinker','ObligationAnswer','ResearchEngine','EvidencePrompt','AnswerEngine','NativeRuntime']]+[R/'tools/evaluation/scale-model-quality/ScaleHarness.java',R/'tools/evaluation/obligation-binding/BindingHarness.java',F/'LinkHarness.java']
 classes.mkdir(parents=True,exist_ok=True);subprocess.run([TC/'jdk/bin/javac','-d',classes,*sources],check=True);return sources
if __name__=='__main__':
 newrun=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=False);inputs=out/'inputs';inputs.mkdir();assert json.loads((newrun/'receipt.json').read_text())['exit_code']==0
 new=json.loads((F/'fixtures.json').read_text());old=json.loads((R/'tools/evaluation/scale-model-quality/protocol.json').read_text());extension=json.loads((R/'tools/evaluation/obligation-binding/new-cases.json').read_text());cases=old['cases']+extension['cases']+new['cases'];by={c['id']:c for c in cases};rows=[];origins={}
 def sources(id,c):
  (inputs/(id+'.tsv')).write_text(''.join('\t'.join(enc(s[k] if k!='edition' else new['edition']) for k in ['edition','id','source_sha256','sha256','title','date','license','text'])+'\n' for s in c['sources']))
 for c in cases:
  id=c['id'];path=(newrun if id.startswith('l') else E/'run')/'results'/(id+'.json');v=json.loads(path.read_text());rows.append('\t'.join([id,enc(c['question']),enc(v['draft']['raw']),str(v['draft']['tokens'])]));sources(id,c);origins[id]={'path':str(path.relative_to(R)),'sha256':sha(path),'type':'actual generated draft'}
 for h in json.loads((R/'tools/evaluation/obligation-binding/history.json').read_text()):
  id=h['id'];path=E/'history/results'/(id+'.json');v=json.loads(path.read_text());lines=[]
  for c in v['claims']:lines.append(f"O{c['obligation']}|"+','.join(x['label'] for x in c['references'])+'|'+c['subject']+'|'+c['qualifier']+'|'+c['text'])
  rows.append('\t'.join([id,enc(h['question']),enc('\n'.join(lines)),'1']));sources(id,by[h['case_id']]);origins[id]={'path':str(path.relative_to(R)),'sha256':sha(path),'type':'historical generated claim wrapper, not fresh generation'}
 for c in new['cases']:
  id='p'+c['id'][1:];rows.append('\t'.join([id,enc('Is this complete statement supported by the cited excerpt?'),enc('@PROBE'),'1',enc(c['probe_source']['passage']),enc(c['constructed_probe'])]));sources(id,c);origins[id]={'path':str((F/'fixtures.json').relative_to(R)),'sha256':sha(F/'fixtures.json'),'case':c['id'],'type':'constructed counterfactual or paraphrase regression, never corpus or generated success'}
 (inputs/'drafts.tsv').write_text('\n'.join(rows)+'\n');(out/'origins.json').write_text(json.dumps(origins,indent=2)+'\n');sources_java=compile_to(out/'classes')
 cmd=[str(TC/'jdk/bin/java'),'-cp',str(out/'classes'),'org.pocketlore.app.LinkHarness',str(inputs),str(out/'prepared')];subprocess.run(cmd,check=True)
 manifest={'sources':{str(p.relative_to(R)):sha(p) for p in sources_java+[F/'prepare.py',F/'score.py',F/'protocol.json',F/'runtime-declaration.json',F/'fixtures.json']},'inputs':{str(p.relative_to(out)):sha(p) for p in inputs.glob('*')},'origins_sha256':sha(out/'origins.json'),'pairs_sha256':sha(out/'prepared/pairs.json'),'revision':subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=R).strip(),'command':cmd}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
