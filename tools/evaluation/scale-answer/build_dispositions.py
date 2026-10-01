"""Record builder pending dispositions; this does not issue independent clearance."""
import json,hashlib,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[3]
def sha(b):return hashlib.sha256(b).hexdigest()
def units(s):return len(s.encode('utf-16-le'))//2
def fingerprint(fields):return sha(''.join(str(units(f))+':'+f for f in fields).encode())
rows=json.loads((ROOT/'docs/evidence/scale-answer/bulk-records.json').read_text())
wiki=pathlib.Path('/home/isa/PocketLore-control/scale-workers/wiki/edition-v7')
edition=sha((wiki/'installed-inventory.json').read_bytes())
reasons={4456695:'Retained archive templates reference external aviation material; original attribution scope not independently cleared.',1910:'Temperature conversion templates survive only in supplementary ranges; rendered unit fidelity needs review; excluded from supplementary stress for225 genetics overlap.',1419:'Math/templates survive in ranges; formula-to-rendered-offset correspondence and external references require review.',1909:'Dataset-only rights; expansion notice indicates source incompleteness and no contributor-level independent review.',1566:'Ancient names and approximate chronological templates retained separately; chronology/attribution review pending.',586:'Citation/standard templates and technical tables require source-specific redistribution and extraction review.',991:'Rendered TeX and retained raw math/image ranges require fidelity/exceptions review; math brackets are not citation IDs.',656:'Multiple chemical definitions and math/templates require exact condition/formula review; notice-candidate marker is not approval.'}
dispositions=[];inputs=[]
for entry in rows:
 r=entry['row'];d=json.loads((ROOT/entry['record_path']).read_text());text=d['text'];end=text.find('\n',text.find('\n')+1);end=len(text) if end<0 else end
 # Select whole opening paragraph for a prospective review; refuse >1200 rather than truncate.
 start=0;span=text[:end];rights='Wikipedia contributors; CC BY-SA 4.0 dataset terms; source status: '+r['rights']
 fields=[edition,entry['shard'],str(r['id']),str(r['revision']),r['sha256'],r['text_sha256'],r['title'],r['url'],'https://en.wikipedia.org/w/index.php?curid='+str(r['id'])+'&action=history',r['modified'],rights,'Unresolved source-specific exceptions; see retained source ranges',r['sha256'],d['wikitext_scope']]
 key=':'.join([fields[0],fields[1],fields[2],fields[3],fields[5]])
 dispositions.append(dict(key=key,snapshot_sha256=fingerprint(fields),start_utf16=0,end_utf16=units(span),span_sha256=sha(span.encode()),rights_status='pending_independent_review',fidelity_status='pending_independent_review',rights_receipt_sha256='',fidelity_receipt_sha256='',builder_reason=reasons[r['id']],source_fields=fields,source_revision=r['revision'],source_wikitext_sha256=d['source_wikitext_sha256'],retained_wikitext_sha256=sha(d['wikitext'].encode()),retained_range_map=d['wikitext_ranges'],range_coordinate_convention='producer source-wikitext offsets; not relabeled as document UTF-16',record_path=entry['record_path']))
 inputs.append(dict(fields=fields,record_path=entry['record_path'],start_utf16=0,end_utf16=units(span)))
ledger=dict(schema=1,authority='Builder pending dispositions, no independent approval; application-bundled trust boundary',dispositions=dispositions)
(ROOT/'android/app/src/main/assets/bulk-source-reviews.json').write_text(json.dumps(ledger,indent=2,ensure_ascii=False)+'\n')
(ROOT/'docs/evidence/scale-answer/snapshot-inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
print('Recorded8 pending dispositions; independently cleared0')
