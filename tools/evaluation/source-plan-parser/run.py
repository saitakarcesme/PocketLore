from pathlib import Path
import json,hashlib,subprocess,time,resource,base64,sys
import spacy
from structure import parse,match
R=Path(__file__).resolve().parents[3];F=Path(__file__).parent;D=R/'downloads/source-plan-parser';E=R/'docs/evidence/source-plan-parser';TC=Path('/home/isa/Android/atlas-toolchain/jdk/bin')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=D/'run';out.mkdir(exist_ok=False);classes=out/'classes';classes.mkdir();old=json.loads((R/'docs/evidence/source-plan/run/manifest.json').read_text());src=[R/p for p in old['sources'] if p.endswith('.java')]+[R/'android/app/src/main/java/org/pocketlore/app/SentenceEvidence.java',F/'Export.java'];subprocess.run([TC/'javac','-d',classes,*src],check=True)
groups=[('new',R/'docs/evidence/source-plan/run/inputs','cases.tsv'),('prior',R/'docs/evidence/independent-linking/scoring/inputs','drafts.tsv')]
for name,p,rows in groups:subprocess.run([TC/'java','-cp',classes,'org.pocketlore.app.Export',p,p/rows,out/(name+'-sources.json')],check=True)
start=time.monotonic();nlp=spacy.load('en_core_web_sm',disable=['ner']);loaded=time.monotonic();cache={}
def parsed(text):
 if text not in cache:cache[text]=parse(nlp,text)
 return cache[text]
controls=json.loads((F/'controls.json').read_text());control_results=[]
for c in controls['cases']:
 source=parsed(c['source']);claim=parsed(c['claim']);control_results.append({**c,'matches':match(claim,[source]),'source_parse':source,'claim_parse':claim})
(out/'controls.json').write_text(json.dumps(control_results,indent=2)+'\n')
results=[]
for name,p,rows in groups:
 sources=json.loads((out/(name+'-sources.json')).read_text())
 for row in (p/rows).read_text().splitlines():
  f=row.split('\t');id=f[0];question=base64.b64decode(f[1]).decode();srcs=sources[id];texts=[s['span'][0]['references'][0]['text'] for s in srcs];parses=[parsed(t) for t in texts];failure='';claims=[];raw=''
  if name=='new':raw=json.loads((R/'docs/evidence/source-plan/run/results'/(id+'.json')).read_text())['draft']['raw']
  else:
   raw=base64.b64decode(f[2]).decode()
   if raw=='@PROBE':raw='O1|probe|probe|none|'+base64.b64decode(f[5]).decode()
  if not raw:failure='No preserved prose; no generation repeated'
  for line in raw.strip().splitlines():
   if not line.strip():continue
   parts=line.split('|')
   if len(parts)!=5:failure='Malformed or withheld draft';break
   text=parts[4].strip();pp=parsed(text);matches=match(pp,parses);literal=any(text==t for t in texts)
   claims.append({'text':text,'parse':pp,'source_indices':matches,'literal_copy':literal})
   if matches is None:failure='Complete structure not proved'
  eligible=bool(claims) and not failure
  results.append({'group':name,'id':id,'question':question,'raw':raw,'source_sentence_count':len(srcs),'claims':claims,'route':'STRUCTURAL_CANDIDATE' if eligible else 'WITHHELD','failure':failure})
(out/'results.json').write_text(json.dumps(results,indent=2)+'\n');(out/'parses.json').write_text(json.dumps(cache,indent=2)+'\n')
r={'load_seconds':loaded-start,'total_seconds':time.monotonic()-start,'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'model':nlp.meta['version'],'spacy':spacy.__version__,'sources':{str(p.relative_to(R)):sha(p) for p in src+[F/'run.py',F/'structure.py',F/'protocol.json',F/'controls.json']},'model_sha256':sha(D/'en_core_web_sm-3.7.1-py3-none-any.whl'),'artifacts':{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and 'classes' not in p.parts}}
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print('DONE',r['total_seconds'],len(cache),'parses');print('controls',[(v['id'],v['matches'] is not None) for v in control_results]);print('candidates',[(v['group'],v['id']) for v in results if v['route']=='STRUCTURAL_CANDIDATE'])
