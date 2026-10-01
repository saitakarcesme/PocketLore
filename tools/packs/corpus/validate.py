#!/usr/bin/env python3
"""Independently recompute corpus integrity, coverage, attribution and deduplication."""
import argparse, collections, json, pathlib, re, urllib.parse, time, resource
from acquire import PRIMARY, LICENSE, chunks, classify, digest, filehash, limits, normalized, rights, save, topic_exclusion

def records(path):
 with path.open() as f:
  for line in f: yield json.loads(line)

def validate(stage, check_upstream=True):
 rules=json.loads((stage/'selection-v1.json').read_text()); frozen=json.loads((stage/'freeze.json').read_text())
 if filehash(stage/'selection-v1.json')!=frozen['selection_sha256']: raise ValueError('Selection freeze mismatch')
 shards=rules.get('shards',[{'path':rules.get('shard'),'sha256':rules.get('shard_sha256')}]); pins={r['path']:r['sha256'] for r in shards}
 if rules['dataset']!='wikimedia/wikipedia' or rules['config']!='20231101.en': raise ValueError('Unsupported dataset rights basis')
 docs={}; urls=set(); hashes=set(); areas=collections.Counter(); per_doc=collections.Counter(); chunk_areas=collections.Counter()
 for d in records(stage/'sources.jsonl'):
  rights(d)
  if d['id'] in rules.get('curation',{}).get('exclude_document_ids',{}): raise ValueError('Curated topic exclusion')
  expected_history='https://en.wikipedia.org/w/index.php?title='+urllib.parse.quote(d['title'].replace(' ','_'),safe='')+'&action=history'
  if d['history_url']!=expected_history or d['attribution']!=d['title']+' — Wikipedia contributors': raise ValueError('Attribution identity mismatch')
  if d['id'] in docs or d['url'] in urls or normalized(d['text']) in hashes: raise ValueError('Duplicate document')
  if d['normalized_text_sha256'] != digest(normalized(d['text'])): raise ValueError('Document normalized hash mismatch')
  area,scores=classify(d['title'],d['text'],rules)
  if topic_exclusion(d['title'],d['text'],area,rules): raise ValueError('Excluded topic')
  if d['area'] != area or d['topic_scores'] != scores: raise ValueError('Incorrect area')
  if any(marker in d['text'].lower() for marker in rules['rights_markers']): raise ValueError('Rights marker bypass')
  if d['dataset_revision']!=rules['revision'] or d['snapshot']!=rules['config'] or d['upstream_shard_sha256']!=pins.get(d['upstream_shard']): raise ValueError('Source pin mismatch')
  if d['revision_id'] is not None or d['revision_timestamp'] is not None: raise ValueError('Invented revision metadata')
  docs[d['id']]=d; urls.add(d['url']); hashes.add(normalized(d['text'])); areas[area]+=1
 seen=set(); ids=set(); ends={}
 for c in records(stage/'chunks.jsonl'):
  d=docs[c['document_id']]; text=c['text']; start,end=c['start_char'],c['end_char']
  if rules.get('curation'):
   boundary=re.search(rules['curation']['stop_heading_pattern'],d['text'])
   if boundary and end>boundary.start(): raise ValueError('Back matter counted as passage')
  if start<0 or end<=start or d['text'][start:end]!=text or digest(text)!=c['text_sha256']: raise ValueError('Corrupt chunk')
  if start<ends.get(d['id'],0): raise ValueError('Overlapping chunks')
  ends[d['id']]=end
  n=digest(normalized(text))
  if n in seen or c['id'] in ids: raise ValueError('Duplicate chunk')
  if n!=c['normalized_text_sha256']: raise ValueError('Chunk normalized hash mismatch')
  if not rules['minimum_chunk_words']<=len(text.split())<=rules['chunk_words']: raise ValueError('Chunk length invalid')
  for field in ('area','license','license_url','url','history_url','attribution','source_text_sha256'):
   if c.get(field)!=d[field]: raise ValueError('Chunk provenance mismatch: '+field)
  seen.add(n); ids.add(c['id']); per_doc[d['id']]+=1; chunk_areas[c['area']]+=1
 if any(per_doc[i]<rules['minimum_chunks'] for i in docs): raise ValueError('Insufficient document passages')
 if check_upstream:
  import pyarrow.parquet as pq
  found=set()
  for shard in shards:
   raw=stage/'raw'/pathlib.Path(shard['path']).name
   if not raw.exists() and len(shards)==1: raw=stage/'raw/source.parquet'
   if filehash(raw)!=shard['sha256']: raise ValueError('Corrupt upstream shard')
   for batch in pq.ParquetFile(raw).iter_batches(batch_size=64,use_threads=False):
    for row in batch.to_pylist():
     ident=str(row['id'])
     if ident not in docs: continue
     d=docs[ident]
     if any(row[k]!=d[k] for k in ('title','url','text')) or d['upstream_shard']!=shard['path']: raise ValueError('Upstream content mismatch')
     found.add(ident)
  if found!=docs.keys(): raise ValueError('Source missing upstream')
 receipts=list(records(stage/'receipts.jsonl'))
 if check_upstream:
  received={r['path'] for r in receipts if r['status']=='ok'}
  required=set(PRIMARY)|{'dataset-card.md'}
  required.update(pathlib.Path(sh['path']).name for sh in shards)
  if len(shards)==1 and (stage/'raw/source.parquet').exists(): required.discard(pathlib.Path(shards[0]['path']).name); required.add('source.parquet')
  if not required<=received: raise ValueError('Missing acquisition receipts')
 for r in receipts:
  if r['status']=='ok' and filehash(stage/'raw'/r['path'])!=r['sha256']: raise ValueError('Receipt hash mismatch')
 result={'documents':len(docs),'chunks':len(seen),'area_documents':dict(areas),'area_chunks':dict(chunk_areas),'all_source_texts_match_pinned_upstream':check_upstream,'minimum_passages_per_document':min(per_doc.values()),'duplicate_documents':0,'duplicate_chunks':0,'corrupt_chunks':0,'missing_rights':0}
 result['target_met']=len(docs)>=1000 and len(seen)>=10000 and all(areas[a]>=50 for a in rules['areas'])
 counts=json.loads((stage/'counts.json').read_text())
 if counts['documents']!=result['documents'] or counts['chunks']!=result['chunks'] or counts['area_documents']!=dict(areas): raise ValueError('Reported counts mismatch')
 return result

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__); p.add_argument('stage',type=pathlib.Path); args=p.parse_args(); limits()
 started=time.monotonic(); result=validate(args.stage); result['elapsed_seconds']=time.monotonic()-started; result['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss; save(args.stage/'validation.json',result); print(json.dumps(result,indent=2))
