from pathlib import Path
import json,hashlib,tempfile,subprocess,importlib.util,sys
import spacy
from structure import parse,match
R=Path(__file__).resolve().parents[3];F=Path(__file__).parent;E=R/'docs/evidence/source-plan-parser';D=R/'downloads/source-plan-parser'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def exact(p,h):
 if not p.is_file() or sha(p)!=h:raise AssertionError('Missing/changed artifact: '+str(p))
def reject(fn):
 try:fn()
 except (AssertionError,FileNotFoundError):return
 raise AssertionError('Mutation accepted')
def main(*, diagnostic=False, build_receipt=None):
 for line in (E/'SHA256SUMS').read_text().splitlines():h,p=line.split('  ',1);exact(R/p,h)
 spec=importlib.util.spec_from_file_location('old_source_plan',R/'tools/evaluation/source-plan/verify.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old);previous=old.main(diagnostic=True,build_receipt=build_receipt or (E/'build.json',sha(E/'build.json')));assert previous['useful']==0,'Historical negative changed'
 model=D/'en_core_web_sm-3.7.1-py3-none-any.whl';pin=json.loads((E/'acquisition.json').read_text());exact(model,pin['sha256']);assert model.stat().st_size==pin['bytes']<1024**3
 installed=json.loads((E/'installed-files.json').read_text())
 for p,h in installed['files'].items():exact(R/installed['site']/p,h)
 receipt=json.loads((E/'run/receipt.json').read_text())
 for p,h in receipt['sources'].items():exact(R/p,h)
 for p,h in receipt['artifacts'].items():exact(E/'run'/p,h)
 exact(F/'controls.json',(F/'controls.sha256').read_text().strip())
 nlp=spacy.load('en_core_web_sm',disable=['ner']);cached=json.loads((E/'run/parses.json').read_text())
 for text,want in cached.items():assert parse(nlp,text)==want,'Parser replay changed'
 controls=json.loads((F/'controls.json').read_text())['cases']
 for c in controls:assert (match(cached[c['claim']],[cached[c['source']]]) is not None)==c['supported'],'Constructed structural regression'
 values=json.loads((E/'run/results.json').read_text());assert len(values)==127
 for v in values:
  sources=json.loads((E/'run'/(v['group']+'-sources.json')).read_text())[v['id']];parses=[cached[s['span'][0]['references'][0]['text']] for s in sources]
  for c in v['claims']:assert match(cached[c['text']],parses)==c['source_indices']
 with tempfile.TemporaryDirectory(prefix='pocketlore-sentence-') as tmp:
  t=Path(tmp);classes=t/'classes';classes.mkdir();tc=Path('/home/isa/Android/atlas-toolchain/jdk/bin');sources=[R/p for p in receipt['sources'] if p.endswith('.java')]+[F/'SentenceBehavior.java',R/'tools/evaluation/fact-frames/FrameBehavior.java'];subprocess.run([tc/'javac','-d',classes,*sources],check=True);subprocess.run([tc/'java','-cp',classes,'org.pocketlore.app.SentenceBehavior'],check=True)
  for group,inputdir,rowfile in [('new','docs/evidence/source-plan/run/inputs','cases.tsv'),('prior','docs/evidence/independent-linking/scoring/inputs','drafts.tsv')]:
   p=R/inputdir;out=t/(group+'.json');subprocess.run([tc/'java','-cp',classes,'org.pocketlore.app.Export',p,p/rowfile,out],check=True);exact(out,sha(E/'run'/(group+'-sources.json')))
  changed=t/'model.whl';changed.write_bytes(model.read_bytes()+b'changed');reject(lambda:exact(changed,pin['sha256']));reject(lambda:exact(t/'missing-model',pin['sha256']))
  changed=t/'result';changed.write_bytes((E/'run/results.json').read_bytes()+b'changed');reject(lambda:exact(changed,sha(E/'run/results.json')));reject(lambda:exact(t/'missing-result',sha(E/'run/results.json')))
 counts={'records':len(values),'structural_candidates':sum(v['route']=='STRUCTURAL_CANDIDATE' for v in values),'new_useful':0,'new_absent_withheld':sum(v['group']=='new' and v['id'] in ['q04','q08','q16','q24'] and v['route']=='WITHHELD' for v in values)}
 # No candidate means no positive precision or manual support approval can be inferred.
 assert counts['structural_candidates']==0,'New candidate requires source assessment before result can be frozen'
 assert counts==json.loads((E/'metrics.json').read_text())['counts']
 print(json.dumps({'behavior':'PASS','counts':counts,'independent_review':'pending','classification':'Source retention improved; actual prose compatibility still failed'},indent=2),flush=True)
 if diagnostic:return counts
 if counts['new_useful']==0:raise AssertionError('QUALITY FAIL: no complete useful non-extractive answer')
if __name__=='__main__':main()
