#!/usr/bin/env python3
"""Host execution of the same Java quote controller; no model inference."""
import base64,hashlib,json,pathlib,subprocess,tempfile,time
ROOT=pathlib.Path(__file__).resolve().parents[3]
HERE=pathlib.Path(__file__).resolve().parent
OUT=ROOT/'docs/evidence/research-brief'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run():
 sources=json.loads((HERE/'sources.json').read_text());cases=json.loads((HERE/'cases.json').read_text())
 with tempfile.TemporaryDirectory(prefix='brief225-') as td:
  td=pathlib.Path(td)
  (td/'sources.tsv').write_text(''.join('\t'.join([s['id'],s['title'],s['url'],s['date'],s['rights'],s['text'],'Edition SHA-256: '+s['edition_sha256']+'; passage SHA-256: '+s['sha256']])+'\n' for s in sources))
  (td/'cases.tsv').write_text(''.join(c['id']+'\t'+c['question']+'\n' for c in cases))
  (td/'historical.tsv').write_text(''.join(base64.b64encode(p.read_bytes()).decode()+'\n' for p in HERE.glob('historical-*.draft.partial.txt')))
  java=ROOT/'android/app/src/main/java/org/pocketlore/app'
  subprocess.run(['javac','-d',str(td),str(java/'ResearchEngine.java'),str(java/'ResearchBrief.java'),str(HERE/'BriefCheck.java')],check=True)
  completed=subprocess.run(['java','-Xmx256m','-cp',str(td),'org.pocketlore.app.BriefCheck',str(td/'sources.tsv'),str(td/'cases.tsv'),str(td/'historical.tsv')],capture_output=True,text=True,check=True)
  outputs=[]
  for line in completed.stdout.splitlines():
   id,ns,ids,text=line.split('\t');outputs.append(dict(id=id,host_total_ns=int(ns),source_ids=ids.split(',') if ids else [],rendered=base64.b64decode(text).decode(),route='source_brief',generated=False,coverage_verified=False))
  return outputs,completed.stderr
if __name__=='__main__':
 OUT.mkdir(parents=True,exist_ok=True)
 outputs,log=run();(OUT/'outputs.json').write_text(json.dumps(outputs,indent=2,ensure_ascii=False)+'\n');(OUT/'behavior.log').write_text(log)
 files=[HERE/'freeze.json',HERE/'run.py',HERE/'BriefCheck.java',ROOT/'android/app/src/main/java/org/pocketlore/app/ResearchBrief.java',ROOT/'android/app/src/main/java/org/pocketlore/app/ResearchEngine.java',OUT/'outputs.json']
 (OUT/'receipt.json').write_text(json.dumps(dict(environment='LLMRig host Java, -Xmx256m; no inference or Android execution',files={str(p.relative_to(ROOT)):sha(p) for p in files},java=subprocess.check_output(['java','-version'],stderr=subprocess.STDOUT,text=True)),indent=2)+'\n');print(log)
