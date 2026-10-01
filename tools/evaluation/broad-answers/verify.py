#!/usr/bin/env python3
"""Verify exact JNI artifacts, frozen cases, retrieval behavior and explicit source review."""
from pathlib import Path
import hashlib,json,math,sqlite3,zipfile,tempfile,shutil,re
R=Path(__file__).resolve().parents[3];E=R/'docs/evidence/broad-answers';F=Path(__file__).resolve().parent
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(ok,msg):
 if not ok:raise ValueError(msg)
def artifacts(directory,current):
 receipt=json.loads((directory/'receipt.json').read_text())
 for n,h in receipt['records'].items():need(sha(directory/n)==h,'Changed/missing raw record: '+n)
 if current:
  need(sha(R/'android/app/build/outputs/apk/debug/app-debug.apk')==receipt['apk_sha256'],'Different APK')
  for n,h in receipt['sources'].items():need(sha(R/n)==h,'Changed source/protocol: '+n)
  need(sha(R/'tools/answers/model.env')==receipt['model_env_sha256'],'Changed deployed model')
 result=json.loads((directory/'results.json').read_text());need(result['status']=='PASS','JNI harness failed')
 need((directory/'catalog-before.json').read_bytes()==(directory/'catalog-after.json').read_bytes(),'Catalog mutated')
 return result

def main():
 before=artifacts(E/'before',False);after=artifacts(E/'after',True);protocol=json.loads((F/'protocol.json').read_text());old=json.loads((R/'tools/evaluation/broad-reference/protocol.json').read_text())
 need(after['model_sha256']==after['model_after']==protocol['model_sha256'],'Model not preserved')
 need(len(after['rows'])==len(protocol['cases'])==12,'Incomplete actual matrix')
 need(after['runtime']==before['runtime'],'Runtime identity changed')
 # Validate selected/retrieved bytes against the actual frozen installed assets.
 pack=R/'downloads/broad-reference/rendered-v2/broad-reference.plpack'
 need(sha(pack)==protocol['edition_sha256'],'Broad edition changed')
 with zipfile.ZipFile(pack) as z:manifest=json.loads(z.read('manifest.json'))
 dbfile=R/'downloads/broad-reference/rendered-v2/index.sqlite';need(sha(dbfile)==manifest['db_sha256'],'Broad index changed')
 db=sqlite3.connect('file:'+str(dbfile)+'?mode=ro',uri=True)
 small={}
 for path in [R/'downloads/packs/english-reference.plpack',R/'downloads/science/science-supplement-2026-10-01-v1.plpack']:
  prefix='p'+sha(path)+'_'
  with zipfile.ZipFile(path) as z:
   for line in z.read('passages.tsv').decode().splitlines():
    if not line or line.startswith('#'):continue
    row=line.split('\t');small[prefix+row[0]]=row[1:]
 for row in after['rows']:
  for h in row['retrieved']+row['selected']:
   if h['id'].startswith('p'+protocol['edition_sha256']+'_'):
    data=db.execute('SELECT d.title,d.url,d.date,d.rights,p.body FROM passages p JOIN documents d ON d.id=p.document WHERE p.citation=?',(h['id'].split('_',1)[1],)).fetchone()
   else:data=small.get(h['id'])
   need(data is not None and list(data)==[h[k] for k in ['title','url','date','rights','text']],'Source content or edition mismatch')
 byid={x['id']:x for x in after['rows']};generated=[]
 for case,row in zip(protocol['cases'],after['rows']):
  need(case['id']==row['id'] and case['question']==row['question'],'Frozen question changed')
  need(row['prompt_tokens']+256<=2048 and row['tokens']<=256,'Budget exceeded')
  need(row['native_after'][1]==0,'Retained native context')
  if case['kind']=='absent':need(row['route']=='ABSTAINED' and not row['invoked'] and not row['retrieved'],'Absent query leaked evidence/generation')
  if row['route']=='GENERATED':
   need(row['invoked'] and row['raw'] and row['tokens']>0,'Canned or fallback generation')
   citations=set(re.findall(r'\[([^\[\]]+)\]',row['text']));links=[l for l in after['links'] if l['case']==row['id']]
   need(citations and citations=={l['citation'] for l in links},'Not every generated citation span exercised')
   sources={h['id']:h for h in row['retrieved']}
   for link in links:
    h=sources[link['citation']];need(all(h[k] in link['visible'] for k in ['text','url','date','rights','provenance']),'Wrong dialog source scope')
   generated.append(row['id'])
 need(generated,'No actual generated answer')
 need(after['reload_ms']>0,'No reload behavior')
 metrics={}
 for label,data in [('before',before),('after',after)]:
  need(len(data['retrieval'])==40,'Old matrix incomplete');found=[];miss=[];absent_hits=0
  for q,x in zip(old['queries'],data['retrieval']):
   need(q['id']==x['id'] and q['question']==x['question'],'Old query changed')
   if q['kind']=='absent':absent_hits+=len(x['hits']);continue
   target='_wiki-'+q['expected_document']+'-';(found if any(target in h['id'] for h in x['hits']) else miss).append(q['id'])
  metrics[label]={'found':found,'misses':miss,'absent_hit_count':absent_hits}
 need(metrics['after']['absent_hit_count']==0,'Small-pack OR leakage remains')
 oldrows={x['id']:x for x in after['retrieval']}
 need(oldrows['q03']['hits'][0]['title']=='Acid' and oldrows['q25']['hits'][0]['title']=='Cooking','Exact title priority failed')
 need(any(h['title']=='Absolute value' for h in oldrows['q14']['hits']),'Distance paraphrase missing')
 need(len({h['url'] for h in oldrows['q13']['hits']})>1,'Four passages repeat one article')
 mixed=byid['mixed-water']['selected'];need(any('_wiki-' in h['id'] for h in mixed) and any('_wiki-' not in h['id'] for h in mixed),'Mixed small/broad context missing')
 review=json.loads((E/'builder-review.json').read_text());need(review['results_sha256']==sha(E/'after/results.json'),'Review applies to different outputs')
 need(set(review['generated'])==set(generated),'Unreviewed publication')
 for ident,a in review['generated'].items():
  need(a['support']=='supported' and a['claims'] and a['rationale'],'Unsupported publication or missing manual review')
  need(a['published_text']==byid[ident]['text'],'Review prose drift')
  for claim in a['claims']:need(claim['support']=='supported' and claim['rationale'] and claim['citations'],'Unreviewed claim')
 need(any(a['complete'] and a['useful'] for a in review['generated'].values()),'No useful complete supported generated answer')
 samples=after['samples'];need(any(s['native'][1]>0 for s in samples),'Native context not measured')
 summary={'status':'PASS','retrieval':metrics,'improved':sorted(set(metrics['after']['found'])-set(metrics['before']['found'])),'regressed':sorted(set(metrics['before']['found'])-set(metrics['after']['found'])),'routes':{k:sum(r['route']==k for r in after['rows']) for k in ['GENERATED','FALLBACK','ABSTAINED','CANCELLED']},'generated':generated,'builder_useful':sum(a['complete'] and a['useful'] for a in review['generated'].values()),'memory':{k:max(s.get(k,0) for s in samples) for k in ['pss_kib','VmRSS','VmSwap','java_used_bytes']},'limitations':'Builder source assessment is separate from independent review; emulator only; no release acceptance'}
 # Changed/missing raw JNI evidence must not pass an otherwise valid receipt.
 negatives=[]
 with tempfile.TemporaryDirectory(prefix='pocketlore-answer-artifact-') as temp:
  d=Path(temp)/'run';shutil.copytree(E/'after',d)
  with (d/'results.json').open('ab') as f:f.write(b' ')
  try:artifacts(d,False)
  except ValueError:negatives.append('changed-JNI-output')
  else:raise ValueError('Changed JNI output accepted')
  (d/'results.json').unlink()
  try:artifacts(d,False)
  except FileNotFoundError:negatives.append('missing-JNI-output')
  else:raise ValueError('Missing JNI output accepted')
 summary['negative_artifact_checks']=negatives
 summary['native_sample_maxima']=[max(s['native'][i] for s in samples) for i in range(len(samples[0]['native']))]
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
