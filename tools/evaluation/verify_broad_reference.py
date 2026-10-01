#!/usr/bin/env python3
"""Current broad-reference objective gate; historical numerical success is insufficient."""
from pathlib import Path
import collections,hashlib,importlib.util,json,math,sqlite3,tempfile,zipfile
ROOT=Path(__file__).resolve().parents[2];E=ROOT/'docs/evidence/broad-reference/repair';PACKDIR=ROOT/'downloads/broad-reference/rendered-v2';STAGE=ROOT/'downloads/broad-reference/html-v2'
def require(ok,why):
 if not ok:raise ValueError(why)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def license_check(manifest,legal):
 require(manifest.get('license')=='CC-BY-SA-4.0','Missing license')
 require(legal is not None and digest(legal)=='170b3685f24d098f590c92867787e7be3a86260aed1b96bf4a7594f72a9116be','Missing/changed legal bytes')
def rejected(fn,label):
 try:fn()
 except (ValueError,FileNotFoundError):return label
 raise ValueError('Mutation accepted: '+label)
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 require((PACKDIR/'build.json').is_file(),'FAIL: source-faithful broad edition is not built; the prior 1076/26660 counts do not satisfy the critic repair')
 build=module('broad_build',ROOT/'tools/packs/broad/repair/build.py');extract=module('broad_extract',ROOT/'tools/packs/broad/repair/extract.py')
 seal=module('broad_seal',ROOT/'tools/packs/broad/repair/seal.py').validate();sealed={d['id']:d for d in seal['documents']}
 info=json.loads((PACKDIR/'build.json').read_text());require(info['acquisition_receipts_sha256']==seal['receipts_sha256'],'Acquisition receipt drift');review=json.loads((E/'semantic-review.json').read_text());require(sha(E/'semantic-review.json')==info['review_sha256'],'Changed semantic review')
 pack=PACKDIR/'broad-reference.plpack';db=PACKDIR/'index.sqlite';require(sha(pack)==info['pack_sha256'] and sha(db)==info['db_sha256'],'Changed pack/index')
 with zipfile.ZipFile(pack) as z:
  m=json.loads(z.read('manifest.json'));legal=z.read('CC-BY-SA-4.0.html');license_check(m,legal);require(digest(z.read('index.sqlite'))==info['db_sha256'],'Archive index mismatch')
  require(digest(z.read('CC-BY-SA-4.0.html'))=='170b3685f24d098f590c92867787e7be3a86260aed1b96bf4a7594f72a9116be','Legal bytes changed')
 c=sqlite3.connect('file:'+str(db)+'?mode=ro',uri=True);c.row_factory=sqlite3.Row;reviewed={r['id']:r for r in review['documents']};areas=collections.Counter();source_norm=set();passage_norm=set();documents={};math_count=0;notices=0
 for d in c.execute('SELECT * FROM documents'):
  ident=d['id'];raw=STAGE/(ident+'.html');cached=json.loads((STAGE/'extracted'/(ident+'.json')).read_text());require(sha(raw)==cached['html_sha256'],'Changed rendered source')
  require(cached['html_sha256']==sealed[ident]['html_sha256'] and cached['revision']==sealed[ident]['revision'],'Unpinned revision metadata')
  actual=extract.extract(raw.read_text());require(all(actual[k]==cached[k] for k in ['blocks','references','attribution_notices','excluded','math_representations']),'Extractor/source drift')
  require(build.eligible(cached) is None,'Unresolved source admitted')
  body='\n\n'.join(b['text'] for b in actual['blocks']);require(body==d['body'] and digest(body.encode())==d['sha'],'Source fidelity mismatch')
  normalized=build.norm(body);require(normalized not in source_norm,'Duplicate document');source_norm.add(normalized)
  require(str(cached['revision']['revid']) in d['url'] and cached['revision']['timestamp'] in d['date'],'Revision/date not pinned')
  require('Wikipedia contributors' in d['rights'] and 'CC BY-SA 4.0' in d['rights'] and 'Contributor history:' in d['provenance'],'Attribution missing')
  for n in actual['attribution_notices']:
   require(n['text'] in d['provenance'] and all(link in d['provenance'] for link in n['links']),'Source-specific notice lost');notices+=1
  for ref in actual['references']:require(ref['text'] in d['provenance'] and all(link in d['provenance'] for link in ref['links']),'Reference attribution lost')
  if ident in reviewed:
   r=reviewed[ident];require(r['html_sha256']==sha(raw) and r['support_text'] in body and r['reason'] and r['reviewer']=='builder','Semantic review/source mismatch');areas[r['area']]+=1
  math_count+=actual['math_representations'];documents[ident]=dict(d)
 for p in c.execute('SELECT * FROM passages'):
  d=documents[p['document']];require(digest(p['body'].encode())==p['sha'],'Passage hash')
  require(d['body'].encode('utf-16-le')[p['start']*2:p['end']*2].decode('utf-16-le')==p['body'],'Synthetic/non-source passage')
  n=build.norm(p['body']);require(n not in passage_norm,'Duplicate passage');passage_norm.add(n)
 require(len(documents)>=1000 and len(passage_norm)>=10000,'Original breadth target unmet')
 require(len(areas)==8 and min(areas.values())>=50 and dict(areas)==m['areas'],'Reviewed semantic quota unmet')
 require(len(documents)==m['documents'] and len(passage_norm)==m['passages'],'Manifest count mismatch')
 require(c.execute('SELECT count(*) FROM search').fetchone()[0]==len(passage_norm),'Missing index rows')
 require(c.execute('SELECT count(*) FROM search s JOIN passages p ON p.pid=s.docid JOIN documents d ON d.id=p.document WHERE s.body!=p.body OR s.title!=d.title').fetchone()[0]==0,'Index diverges from source')
 require('[TeX:' in documents['991']['body'] and 'absolute value of 3 is 3' in documents['991']['body'] and '50 metres (160 ft)' in documents['633']['body'],'Critic fidelity regressions')
 receipt=json.loads((E/'run/receipt.json').read_text());require(receipt['pack']['sha256']==sha(pack),'Android tested different edition');require(receipt['apk']['sha256']==sha(ROOT/'android/app/build/outputs/apk/debug/app-debug.apk'),'APK changed')
 for name,h in receipt['sources'].items():require(sha(ROOT/name)==h,'Production/test source changed: '+name)
 for name,h in receipt['records'].items():require(sha(E/'run'/name)==h,'Raw behavior artifact changed: '+name)
 protocol=json.loads((ROOT/'tools/evaluation/broad-reference/protocol.json').read_text());require(sha(ROOT/'tools/evaluation/broad-reference/protocol.json')==receipt['protocol_sha256'],'Frozen query change')
 reports={};results={};prefix='p'+sha(pack)+'_'
 for mode in ['import','restart']:
  r=json.loads((E/'run'/(mode+'.json')).read_text());reports[mode]=r;require(r['status']=='PASS' and r['collections']==3 and r['documents']==len(documents)+18 and r['passages']==len(passage_norm)+210,'Installed catalog/counts')
  require(r['saved_model_before']==r['saved_model_after']=='74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db' and r['stages']==0,'Model/rollback/stages')
  require(r['after_open']['java_used']-r['before_open']['java_used']<32*1024*1024,'Opening heap bound')
  require(r['offline_license_visible'] and len(r['dialogs'])==8,'Source/license UI not exercised')
  require(len(r['queries'])==40,'Incomplete query matrix');found=0;misses=[];times=[]
  for q,a in zip(protocol['queries'],r['queries']):
   require(q['id']==a['id'] and q['question']==a['question'],'Changed question');ids=[];times.append(a['ms'])
   for hit in a['hits']:
    if not hit['id'].startswith(prefix):continue
    row=c.execute('SELECT p.document,p.body,d.title,d.url,d.rights,d.date FROM passages p JOIN documents d ON d.id=p.document WHERE p.citation=?',(hit['id'][len(prefix):],)).fetchone();require(row is not None,'Unknown citation')
    require(all(hit[k]==row[v] for k,v in [('text','body'),('title','title'),('url','url'),('rights','rights'),('date','date')]),'Wrong source inspection bytes');ids.append(row['document'])
   if q['kind']=='absent':require(not ids and a['controller_route']=='ABSTAINED','Absent evidence published')
   elif q['expected_document'] in ids:found+=1
   else:misses.append(q['id'])
   require(a['controller_route']!='GENERATED','Generation must await separate model-support review')
  times.sort();results[mode]={'expected_document_top4':found,'of':32,'misses':misses,'p50_ms':times[19],'p95_ms':times[37]}
 require(reports['import']['pid']!=reports['restart']['pid'],'No process restart')
 require(reports['import'].get('import_ms',0)>0,'No fresh new-edition import measurement')
 require('Index SHA-256 mismatch' in reports['import']['corrupt_index_failure'] and 'cancel' in reports['import']['cancel_status'].lower(),'Corruption/cancellation not verified')
 negatives=[rejected(lambda:license_check({k:v for k,v in m.items() if k!='license'},legal),'missing-license'),rejected(lambda:license_check(m,None),'missing-legal-text')]
 with tempfile.TemporaryDirectory(prefix='pocketlore-broad-regression-') as temp:
  changed=Path(temp)/'changed';changed.write_bytes((E/'run/restart.json').read_bytes()+b' ')
  negatives.append(rejected(lambda:require(sha(changed)==receipt['records']['restart.json'],'Changed raw artifact'),'changed-artifact'))
  negatives.append(rejected(lambda:sha(Path(temp)/'missing-model-or-pack'),'missing-artifact'))
 # Mutation tests exercise the source admission policy itself, not a producer success flag.
 base=json.loads((STAGE/'extracted/991.json').read_text());bad=json.loads(json.dumps(base));bad['attribution_notices']=[{'text':'Unspecified additional third-party permission','links':['https://example.invalid']}];require(build.eligible(bad) is not None,'Unresolved attribution mutation accepted')
 try:extract.extract('<div class="mw-parser-output"><p>'+('x'*100)+'<span class="mwe-math-element"></span></p></div>')
 except ValueError:pass
 else:raise ValueError('Missing math mutation accepted')
 require(sha(ROOT/'downloads/broad-reference/rendered-v2-repro/broad-reference.plpack')==sha(pack),'Reproducible build differs')
 print(json.dumps({'status':'PASS','documents':len(documents),'genuine_unique_passages':len(passage_norm),'builder_source_reviewed_areas':dict(areas),'preserved_math_representations':math_count,'preserved_source_notices':notices,'retrieval':results,'negative_regressions':negatives,'limitations':'Builder semantic judgments require independent review; retrieval is not generated support; emulator is not phone acceptance'},indent=2))
if __name__=='__main__':main()
