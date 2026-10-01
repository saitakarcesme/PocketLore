#!/usr/bin/env python3
"""Bounded, pinned Wikimedia bulk acquisition; bulk artifacts stay outside Git."""
import argparse, fcntl, collections, datetime, hashlib, json, os, pathlib, re, resource, sys, time, unicodedata, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).parent
LICENSE = 'https://creativecommons.org/licenses/by-sa/4.0/'
PRIMARY = {
 'wikimedia-terms.html': 'https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use',
 'wikimedia-dumps-legal.html': 'https://dumps.wikimedia.org/legal.html',
 'cc-by-sa-4.0.html': LICENSE + 'legalcode.en',
}

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
def normalized(s): return ' '.join(unicodedata.normalize('NFKC', s).casefold().split())
def filehash(p):
 h = hashlib.sha256()
 with open(p, 'rb') as f:
  for block in iter(lambda: f.read(1024*1024), b''): h.update(block)
 return h.hexdigest()
def save(p, obj):
 tmp = p.with_suffix(p.suffix + '.tmp')
 tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=True) + '\n')
 tmp.replace(p)
def emit(f, obj): f.write(json.dumps(obj, ensure_ascii=True) + '\n')

def limits():
 cpus = sorted(os.sched_getaffinity(0))[:2]
 os.sched_setaffinity(0, cpus)
 resource.setrlimit(resource.RLIMIT_AS, (2*1024**3, 2*1024**3))
 return {'cpu_affinity': cpus, 'address_space_limit_bytes': 2*1024**3, 'http_concurrency': 1, 'attempts_per_url': 2, 'timeout_seconds': 45}

def fetch(url, target, receipts, expected=None):
 if target.exists():
  if expected and filehash(target) != expected: raise ValueError('Existing download hash mismatch')
  return
 for attempt in range(1, 3):
  started = now(); size = 0
  try:
   req = urllib.request.Request(url, headers={'User-Agent':'PocketLore-Corpus/1.0 (bounded research snapshot)'})
   with urllib.request.urlopen(req, timeout=45) as response, open(str(target)+'.part', 'wb') as out:
    headers = {k:v for k,v in response.headers.items() if k.lower() in ('etag','last-modified','content-length','content-type')}
    for block in iter(lambda: response.read(1024*1024), b''):
     size += len(block)
     if size > 600*1024**2: raise ValueError('Download byte budget exceeded')
     out.write(block)
   sha = filehash(str(target)+'.part')
   if expected and sha != expected: raise ValueError('Upstream SHA256 mismatch')
   os.replace(str(target)+'.part', target)
   with receipts.open('a') as f: emit(f, {'url':url,'path':target.name,'started':started,'finished':now(),'attempt':attempt,'bytes':size,'sha256':sha,'headers':headers,'status':'ok'})
   return
  except Exception as e:
   with receipts.open('a') as f: emit(f, {'url':url,'started':started,'finished':now(),'attempt':attempt,'bytes':size,'status':'failed','error':str(e)})
   if attempt == 2: raise
   time.sleep(2)

def classify(title, text, rules):
 scores = {}
 for area, pattern in rules['areas'].items():
  rx = r'\b(?:' + pattern + r')\b'
  scores[area] = 3*len(set(re.findall(rx, title.lower()))) + len(set(re.findall(rx, text[:600].lower())))
 area = max(scores, key=scores.get)
 return (area if scores[area] >= 2 else None), scores

def topic_exclusion(title, text, area, rules):
 if rules.get('content_exclusion_pattern') and re.search(rules['content_exclusion_pattern'], title+' '+text[:400], re.I): return 'non_reference_content'
 if rules.get('date_title_pattern') and re.search(rules['date_title_pattern'], title): return 'chronology'
 if area == 'practical reference' and rules.get('practical_title_required'):
  if not re.search(r'\b(?:'+rules['areas'][area]+r')\b',title,re.I): return 'practical_title_missing'
  if re.search(rules['practical_exclusion_pattern'], title, re.I): return 'practical_institution_or_abstract'
 return None

def chunks(text, rules):
 body=text
 if rules.get('curation'):
  match=re.search(rules['curation']['stop_heading_pattern'],text)
  if match: body=text[:match.start()]
 words = list(re.finditer(r'\S+', body))
 for i in range(0, len(words), rules['chunk_words']):
  part = words[i:i+rules['chunk_words']]
  if len(part) < rules['minimum_chunk_words']: continue
  start, end = part[0].start(), part[-1].end()
  yield start, end, text[start:end]

def rights(d):
 for field in ('id','title','url','attribution','history_url','license','license_url','snapshot','dataset_revision','source_text_sha256','text','upstream_shard_sha256','modifications'):
  if not d.get(field): raise ValueError('Missing rights/provenance field: '+field)
 if d['license'] != 'CC-BY-SA-4.0' or d['license_url'] != LICENSE: raise ValueError('Unapproved license')
 if not d['url'].startswith('https://en.wikipedia.org/wiki/') or not d['history_url'].startswith('https://en.wikipedia.org/w/index.php?'): raise ValueError('Unapproved source/attribution URL')
 if digest(d['text']) != d['source_text_sha256']: raise ValueError('Corrupt source text')

def acquire(stage, rules_path):
 started = time.monotonic(); budget = limits()
 stage.mkdir(parents=True, exist_ok=True)
 if (stage/'sources.jsonl').exists(): raise ValueError('Refusing to overwrite a built snapshot; validate it or choose a new stage')
 rules = json.loads(rules_path.read_text())
 if rules['dataset'] != 'wikimedia/wikipedia' or rules['config'] != '20231101.en': raise ValueError('Unsupported dataset rights basis')
 frozen = stage/'selection-v1.json'
 if frozen.exists() and filehash(frozen) != filehash(rules_path): raise ValueError('Frozen rules changed')
 frozen.write_bytes(rules_path.read_bytes())
 save(stage/'freeze.json', {'frozen_at':now(),'selection_sha256':filehash(frozen),'resource_limits':budget})
 raw = stage/'raw'; raw.mkdir(exist_ok=True)
 receipts = stage/'receipts.jsonl'
 for name,url in PRIMARY.items(): fetch(url,raw/name,receipts)
 base = f"https://huggingface.co/datasets/{rules['dataset']}/resolve/{rules['revision']}/"
 fetch(base+'README.md',raw/'dataset-card.md',receipts)
 shards = rules.get('shards', [{'path':rules.get('shard'),'sha256':rules.get('shard_sha256')}])
 for shard in shards: fetch(base+shard['path'],raw/pathlib.Path(shard['path']).name,receipts,shard['sha256'])
 import pyarrow as pa
 import pyarrow.parquet as pq
 pa.set_cpu_count(2); pa.set_io_thread_count(1)
 counts = collections.Counter(); rejected = collections.Counter(); seen_ids=set(); seen_urls=set(); seen_docs=set(); seen_chunks=set(); total_chunks=0; scanned=0
 with (stage/'sources.jsonl').open('w') as docs, (stage/'chunks.jsonl').open('w') as out, (stage/'decisions.jsonl').open('w') as decisions:
  for shard in shards:
   for batch in pq.ParquetFile(raw/pathlib.Path(shard['path']).name).iter_batches(batch_size=64, use_threads=False):
    for row in batch.to_pylist():
     scanned += 1
     title,text = row['title'],row['text']
     area,scores = classify(title,text,rules)
     reason=topic_exclusion(title,text,area,rules)
     if reason: pass
     elif not area: reason='unclassified'
     elif counts[area]>=rules['documents_per_area']: reason='area_quota'
     elif re.match(r'^(List|Index|Outline) of ',title) or '(disambiguation)' in title: reason='non_article'
     elif any(marker in text.lower() for marker in rules['rights_markers']): reason='rights_review_required'
     ident=str(row['id']); url=row['url']
     dh=digest(normalized(text)) if not reason else None
     if not reason and (ident in seen_ids or url in seen_urls or dh in seen_docs): reason='duplicate_document'
     parts=[]; local=set()
     if not reason:
      for start,end,part in chunks(text,rules):
       ch=digest(normalized(part))
       if ch in seen_chunks or ch in local:
        rejected['duplicate_chunk']+=1; continue
       local.add(ch); parts.append((start,end,part,ch))
      if len(parts)<rules['minimum_chunks']: reason='too_few_unique_chunks'
     if reason:
      rejected[reason]+=1
      if reason != 'area_quota': emit(decisions,{'id':ident,'title':title,'reason':reason})
      continue
     d={'id':ident,'title':title,'url':url,'area':area,'topic_scores':scores,'text':text,'source_text_sha256':digest(text),'normalized_text_sha256':dh,
        'language':'en','license':'CC-BY-SA-4.0','license_url':LICENSE,'attribution':title+' — Wikipedia contributors',
        'history_url':'https://en.wikipedia.org/w/index.php?title='+urllib.parse.quote(title.replace(' ','_'),safe='')+'&action=history',
        'snapshot':rules['config'],'revision_id':None,'revision_timestamp':None,'revision_limitation':'Upstream extracted dataset provides no per-article revision ID, timestamp, or contributor list; history URL is an attribution reference, not a frozen author list.',
        'dataset_revision':rules['revision'],'upstream_shard':shard['path'],'upstream_shard_sha256':shard['sha256'],
        'modifications':'Upstream extracted plain text; PocketLore retains full extracted text and creates nonoverlapping verbatim excerpts; chunks may begin or end within sentences.',
        'rights_basis':['wikimedia-terms.html','wikimedia-dumps-legal.html'],'upstream_card_license':'CC-BY-SA-3.0 (stale declaration retained; primary Wikimedia terms govern 4.0 reuse)'}
     rights(d); emit(docs,d)
     for number,(start,end,part,ch) in enumerate(parts):
      emit(out,{'id':ident+':'+str(number),'document_id':ident,'area':area,'text':part,'start_char':start,'end_char':end,'text_sha256':digest(part),'normalized_text_sha256':ch,'license':d['license'],'license_url':LICENSE,'url':url,'history_url':d['history_url'],'attribution':d['attribution'],'source_text_sha256':d['source_text_sha256']})
     counts[area]+=1; total_chunks+=len(parts); seen_ids.add(ident); seen_urls.add(url); seen_docs.add(dh); seen_chunks.update(local)
    if all(counts[a]>=rules['documents_per_area'] for a in rules['areas']): break
 report={'status':'complete' if sum(counts.values())>=1000 and total_chunks>=10000 and all(counts[a]>=50 for a in rules['areas']) else 'partial', 'documents':sum(counts.values()),'chunks':total_chunks,'area_documents':dict(counts),'scanned_rows':scanned,'rejected':dict(rejected),'elapsed_seconds':time.monotonic()-started,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'resource_limits':budget,'selection_sha256':filehash(frozen),'pyarrow_version':pa.__version__,'python':sys.version,'host':os.uname().nodename}
 save(stage/'counts.json',report)
 print(json.dumps(report,indent=2))

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('stage',type=pathlib.Path); parser.add_argument('--rules',type=pathlib.Path,default=ROOT/'selection-v4.json'); args=parser.parse_args()
 args.stage.parent.mkdir(parents=True,exist_ok=True)
 with (args.stage.parent/(args.stage.name+'.writer.lock')).open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  acquire(args.stage,args.rules)
