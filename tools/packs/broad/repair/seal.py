#!/usr/bin/env python3
"""Bind downloaded rendered bytes and derived revision metadata to saved HTTP receipts."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'downloads/broad-reference/html-v2'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def validate():
 receipts=[json.loads(x) for x in (S/'receipts.jsonl').read_text().splitlines()];byfile={r['file']:r for r in receipts};pages={}
 for name,r in byfile.items():
  p=S/name;assert sha(p)==r['sha256'] and p.stat().st_size==r['bytes'],name
  if name.endswith('.json'):
   data=json.loads(p.read_text())
   for ident,page in data.get('query',{}).get('pages',{}).items():
    if 'revisions' in page:pages.setdefault(ident,[]).append(page)
 result=[]
 for p in sorted(S.glob('*.html')):
  ident=p.stem;assert p.name in byfile, p.name
  meta=json.loads((S/(ident+'.json')).read_text());page=next(iter(meta['query']['pages'].values()));assert page in pages.get(ident,[]),ident
  assert 'oldid='+str(page['revisions'][0]['revid']) in byfile[p.name]['url']
  result.append({'id':ident,'title':page['title'],'revision':page['revisions'][0],'html_sha256':sha(p),'html_bytes':p.stat().st_size,'metadata_sha256':sha(S/(ident+'.json')),'url':byfile[p.name]['url']})
 return {'documents':result,'receipts_sha256':sha(S/'receipts.jsonl'),'downloaded_bytes':sum(r['bytes'] for r in receipts),'http_receipts':len(receipts)}
if __name__=='__main__':
 result=validate();(S/'seal.json').write_text(json.dumps(result,indent=2)+'\n');print(len(result['documents']),'real rendered revisions sealed')
