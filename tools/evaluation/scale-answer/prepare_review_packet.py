"""Assemble exact existing bytes for independent review; never issue an approval."""
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[3]
sha=lambda data:hashlib.sha256(data).hexdigest()
ledger=json.loads((ROOT/'android/app/src/main/assets/bulk-source-reviews.json').read_text())
records=[]
for item in ledger['dispositions']:
 data=(ROOT/item['record_path']).read_bytes();source=json.loads(data)
 if sha(data)!=item['source_fields'][4] or sha(source['text'].encode())!=item['source_fields'][5]:raise ValueError('Sealed source changed')
 units=source['text'].encode('utf-16-le');span=units[item['start_utf16']*2:item['end_utf16']*2].decode('utf-16-le')
 if sha(span.encode())!=item['span_sha256']:raise ValueError('Review span changed')
 records.append(dict(disposition=item,proposed_span=span,within_runtime_span_bound=item['end_utf16']-item['start_utf16']<=1200,original_record_path=item['record_path'],raw_scope=source['wikitext_scope'],raw_context=source['wikitext'],review_required=['Source-specific rights and third-party exceptions for this exact revision','Contributor/history attribution and redistribution conditions','Compare decoded text to retained raw math/unit/notice ranges; full revision needed if insufficient','Select a complete bounded span if proposed opening paragraph exceeds1200 UTF-16 units','Do not certify claim entailment or relevance merely from source fidelity']))
packet={'kind':'Pending independent review input; not clearance, corpus or generated-answer evidence','questions':json.loads((ROOT/'tools/evaluation/scale-answer/cases.json').read_text()),'records':records}
path=ROOT/'downloads/scale-answer/independent-review-packet.json'
path.write_text(json.dumps(packet,indent=2,ensure_ascii=False)+'\n')
manifest={'path':str(path.relative_to(ROOT)),'sha256':sha(path.read_bytes()),'bytes':path.stat().st_size,'records':len(records),'oversized_proposals':[r['disposition']['key'] for r in records if not r['within_runtime_span_bound']],'independent_approvals':0,'policy':'Review input only; raw source context remains ignored and no approval is inferred.'}
(ROOT/'docs/evidence/scale-answer/repair-1/review-packet.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
