#!/usr/bin/env python3
"""Apply frozen conservative curation to staged candidates without new acquisition."""
import argparse, collections, json, os, pathlib, resource, shutil, time
from acquire import chunks, digest, emit, filehash, limits, normalized, now, save

def curate(parent, stage, policy):
 started=time.monotonic(); budget=limits()
 if stage.exists(): raise ValueError('Refusing to overwrite curation stage')
 stage.mkdir(); (stage/'raw').mkdir()
 rules=json.loads((parent/'selection-v1.json').read_text()); rules['curation']=json.loads(policy.read_text())
 save(stage/'selection-v1.json',rules)
 save(stage/'freeze.json',{'frozen_at':now(),'selection_sha256':filehash(stage/'selection-v1.json'),'resource_limits':budget,'parent_sources_sha256':filehash(parent/'sources.jsonl'),'curation_policy_sha256':filehash(policy)})
 for f in (parent/'raw').iterdir(): os.link(f,stage/'raw'/f.name)
 for name in ('receipts.jsonl','decisions.jsonl'): shutil.copyfile(parent/name,stage/name)
 for name in ('counts.json','freeze.json','acquisition.log'): shutil.copyfile(parent/name,stage/('parent-'+name))
 counts=collections.Counter(); rejected=collections.Counter(); seen=set(); total=0
 with (parent/'sources.jsonl').open() as src, (stage/'sources.jsonl').open('w') as docs, (stage/'chunks.jsonl').open('w') as out, (stage/'curation-decisions.jsonl').open('w') as decisions:
  for line in src:
   d=json.loads(line); ident=d['id']
   reason=rules['curation']['exclude_document_ids'].get(ident)
   parts=[]; local=set()
   if not reason:
    for start,end,text in chunks(d['text'],rules):
     h=digest(normalized(text))
     if h not in seen and h not in local: parts.append((start,end,text,h)); local.add(h)
    if len(parts)<rules['minimum_chunks']: reason='Insufficient unique body passages after excluding back matter.'
   if reason:
    rejected[reason]+=1; emit(decisions,{'id':ident,'title':d['title'],'reason':reason}); continue
   emit(docs,d)
   for number,(start,end,text,h) in enumerate(parts):
    c={k:d[k] for k in ('area','license','license_url','url','history_url','attribution','source_text_sha256')}
    c.update(id=ident+':'+str(number),document_id=ident,text=text,start_char=start,end_char=end,text_sha256=digest(text),normalized_text_sha256=h)
    emit(out,c)
   counts[d['area']]+=1; total+=len(parts); seen.update(local)
 report={'status':'complete' if sum(counts.values())>=1000 and total>=10000 and all(counts[a]>=50 for a in rules['areas']) else 'partial','documents':sum(counts.values()),'chunks':total,'area_documents':dict(counts),'curation_rejected':dict(rejected),'parent_counts':json.loads((parent/'counts.json').read_text()),'elapsed_seconds':time.monotonic()-started,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'resource_limits':budget,'selection_sha256':filehash(stage/'selection-v1.json')}
 save(stage/'counts.json',report); print(json.dumps(report,indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__); p.add_argument('parent',type=pathlib.Path);p.add_argument('stage',type=pathlib.Path);p.add_argument('--policy',type=pathlib.Path,default=pathlib.Path(__file__).with_name('curation-v1.json')); a=p.parse_args();curate(a.parent,a.stage,a.policy)
