#!/usr/bin/env python3
"""Acquire only the frozen replacement shortlist after the first serial job finishes."""
from acquire import ROOT,OUT,get
import json,urllib.parse
spec=json.loads((ROOT/'tools/packs/broad/repair/replacements.json').read_text());titles=spec['practical reference'];rows=[]
for offset in range(0,len(titles),25):
 q=urllib.parse.urlencode({'action':'query','prop':'revisions','rvprop':'ids|timestamp','titles':'|'.join(titles[offset:offset+25]),'format':'json'})
 batch=json.loads(get('https://en.wikipedia.org/w/api.php?'+q,OUT/('replacement-batch-'+str(offset)+'.json')))
 for ident,page in batch['query']['pages'].items():
  if 'revisions' not in page:rows.append({'requested_title':page['title'],'excluded':'No real article/revision returned'});continue
  path=OUT/(ident+'.json');data={'query':{'pages':{ident:page}}}
  if not path.exists():path.write_text(json.dumps(data))
  else:page=next(iter(json.loads(path.read_text())['query']['pages'].values()))
  rev=page['revisions'][0]['revid'];url='https://en.wikipedia.org/w/index.php?'+urllib.parse.urlencode({'title':page['title'],'oldid':rev})
  get(url,OUT/(ident+'.html'));rows.append({'id':ident,'title':page['title'],'area':'practical reference'});print(ident,page['title'],flush=True)
(OUT/'extra-index.json').write_text(json.dumps(rows,indent=2)+'\n')
