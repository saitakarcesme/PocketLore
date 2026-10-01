#!/usr/bin/env python3
"""Build the versioned CC0 DC catalog from exact pinned Wikidata revisions."""
import argparse,hashlib,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'tools/packs/regional-sources.lock.json'
def digest(raw):return hashlib.sha256(raw).hexdigest()
def build(fetch=False):
 lock=json.loads(LOCK.read_text());rows=[];counts={}
 for src in lock['sources']:
  cache=ROOT/'downloads/regional/raw'/f"{src['id']}.json"
  if fetch and not cache.exists():
   raw=urllib.request.urlopen(urllib.request.Request(src['url'],headers={'User-Agent':'PocketLore/0.1 offline pack'}),timeout=60).read()
   cache.parent.mkdir(parents=True,exist_ok=True);cache.write_bytes(raw)
  raw=cache.read_bytes()
  if digest(raw)!=src['sha256']:raise ValueError('Raw source hash mismatch: '+str(cache))
  e=json.loads(raw)['entities'][src['id']]
  assert e['lastrevid']==src['revision'] and e['modified']==src['modified']
  assert e['labels'][src['label_language']]['value']==src['label'] and e['descriptions']['en']['value']==src['description']
  claims=[c for c in e['claims']['P625'] if c['rank']!='deprecated']
  assert len(claims)==src['coordinate_candidates']
  selected=[c for c in claims if c['id']==src['coordinate_claim']];assert len(selected)==1
  c=selected[0]['mainsnak']['datavalue']['value'];assert c['globe']=='http://www.wikidata.org/entity/Q2'
  assert c['latitude']==src['latitude'] and c['longitude']==src['longitude'] and c['precision']==src['coordinate_precision_degrees']
  south,west,north,east=lock['bounds'];assert south<=c['latitude']<=north and west<=c['longitude']<=east
  assert src['category'] in ['monument','museum','park-garden','civic'];counts[src['category']]=counts.get(src['category'],0)+1
  row=[src['id'],src['label'],src['description'],str(c['latitude']),str(c['longitude']),src['modified'],str(src['revision']),src['sha256'],src['url'],'CC0-1.0',src['retrieved'],src['category'],src['coordinate_claim'],str(c['precision']),str(len(claims))]
  assert all(v and '\t' not in v and '\n' not in v for v in row);rows.append('\t'.join(row))
 assert len(rows)==25 and len(counts)==4
 data=('\n'.join(rows)+'\n').encode();out=ROOT/'downloads/regional/dc-monuments.tsv';out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data)
 manifest={'schema':2,'edition':lock['edition'],'region':lock['region'],'bounds':lock['bounds'],'count':len(rows),'categories':counts,'sha256':digest(data),'source_lock_sha256':digest(LOCK.read_bytes()),'license':'CC0-1.0','license_url':lock['license_url'],'selection':lock['selection_note'],'hours':'Not supplied; offline hours may be stale','routing':'Unavailable; spherical distance only'}
 (out.parent/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');return out,manifest
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');p.add_argument('--install',action='store_true');args=p.parse_args();pack,manifest=build(args.fetch)
 if args.install:
  assets=ROOT/'android/app/src/main/assets'
  assert json.loads((assets/'dc-monuments-manifest.json').read_text())==manifest,'Bundled manifest differs from pinned build'
  (assets/'dc-monuments.tsv').write_bytes(pack.read_bytes())
 print(json.dumps(manifest,indent=2))
