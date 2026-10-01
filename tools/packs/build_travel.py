#!/usr/bin/env python3
"""Build the bounded CC0 travel pack from hash-pinned cached Wikidata entities."""
import argparse,hashlib,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def build(fetch=False):
 lock=json.loads((ROOT/'tools/packs/travel-sources.lock.json').read_text()); rows=[]
 for src in lock['sources']:
  cache=ROOT/'downloads/travel/raw'/f"{src['id']}.json"
  if fetch and not cache.exists():
   url=src['url']+'?revision='+str(src['revision'])
   raw=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'PocketLore/0.1 offline pack'}),timeout=60).read()
   cache.parent.mkdir(parents=True,exist_ok=True);cache.write_bytes(raw)
  raw=cache.read_bytes()
  if hashlib.sha256(raw).hexdigest()!=src['sha256']:raise ValueError('Raw source hash mismatch: '+str(cache))
  e=json.loads(raw)['entities'][src['id']];assert e['lastrevid']==src['revision']
  coords=[c['mainsnak']['datavalue']['value'] for c in e['claims']['P625'] if c['rank']!='deprecated']
  assert len(coords)==1 and coords[0]['globe']=='http://www.wikidata.org/entity/Q2'
  c=coords[0];assert 38.87<=c['latitude']<=38.90 and -77.06<=c['longitude']<=-77.02
  row=[src['id'],e['labels']['en']['value'],e['descriptions']['en']['value'],str(c['latitude']),str(c['longitude']),src['modified'],str(src['revision']),src['sha256'],src['url']+'?revision='+str(src['revision']),'CC0-1.0',src['retrieved']]
  assert all('\t' not in v and '\n' not in v for v in row)
  rows.append('\t'.join(row))
 data=('\n'.join(rows)+'\n').encode();out=ROOT/'downloads/travel/dc-monuments.tsv';out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data)
 manifest={'schema':1,'region':lock['region'],'bounds':lock['bounds'],'count':len(rows),'sha256':hashlib.sha256(data).hexdigest(),'source_lock_sha256':hashlib.sha256((ROOT/'tools/packs/travel-sources.lock.json').read_bytes()).hexdigest(),'license':'CC0-1.0','hours':'Not supplied; offline hours may be stale','routing':'Unavailable; spherical distance only'}
 (out.parent/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');return out,manifest
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');p.add_argument('--install',action='store_true');args=p.parse_args();pack,manifest=build(args.fetch)
 if args.install:
  assets=ROOT/'android/app/src/main/assets'
  assert json.loads((assets/'dc-monuments-manifest.json').read_text())==manifest,'Bundled manifest differs from pinned build'
  (assets/'dc-monuments.tsv').write_bytes(pack.read_bytes())
 print(json.dumps(manifest,indent=2))
