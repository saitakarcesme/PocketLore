"""Prepare source-specific review evidence from sealed bytes, never issue approval."""
import json,hashlib,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[3]
sha=lambda b:hashlib.sha256(b).hexdigest()
# Builder-selected review spans, not runtime rules or expected-answer allowlists.
selections={
586:('Also, ASCII specifies 33 non-printing','The control characters that are still commonly used include carriage return, line feed, and tab.','Decoded control-code explanation is relevant to bulk01; retained raw supplement has references/templates but not this complete prose. Needs exact original revision context and standard quotation/attribution review.'),
4456695:('An airport surveillance radar (ASR)','the airspace around airports.','Complete introductory sentence fits admission; unlike the preserved1224-unit proposal it covers presence/position only, not all secondary-radar fields. Raw supplement contains archive templates only; no matching factual sentence. This is not a complete answer approval.'),
991:('In mathematics, the absolute value','The absolute value of a number may be thought of as its distance from zero.','Retained raw opening prose includes sign cases, zero, examples and distance interpretation with math markup. Builder visual comparison finds those clauses represented in decoded text; image notices are separate and no media is selected. Independent formula-fidelity and source-specific rights review still needed.'),
1419:('A process without transfer of heat','such a system is said to be adiabatically isolated.','The decoded definition preserves Q=0. Raw supplement retains Q=0 math template but not the full explanatory sentence; a matching formula token does not certify the heat-transfer condition.'),
656:('An acid is a molecule or ion','known as a Lewis acid.','Decoded opening distinguishes proton donation from electron-pair covalent bonding. Retained raw supplement does not include this sentence; later reaction templates cannot establish its exact extraction fidelity.'),
1566:('The Akkadian Empire reached its political peak','following the conquests by its founder Sargon.','Decoded chronology includes a literal &nbsp artifact. Retained raw context has circa/cx templates and an attributed Blockquote; cannot certify this sentence, date uncertainty or quotation rights from those fragments. Full immutable revision review required.'),
1909:('Adaptive radiations are thought to be triggered','dispersal to a new environment.','The selected conditions retain thought-to-be and can-be uncertainty. Retained raw context is navigation/expansion templates, not the condition prose; exact revision context required.')}
ledger=json.loads((ROOT/'android/app/src/main/assets/bulk-source-reviews.json').read_text())['dispositions'];summaries=[];packet=[]
for item in ledger:
 fields=item['source_fields'];identifier=int(fields[2]);data=(ROOT/item['record_path']).read_bytes();source=json.loads(data)
 assert sha(data)==fields[4] and sha(source['text'].encode())==fields[5]
 if identifier not in selections:
  summaries.append({'id':identifier,'disposition':'excluded_from_supplementary_stress','reason':'Preserved225 molecular-genetics overlap exclusion; original source disposition remains pending.'});continue
 start_text,end_text,assessment=selections[identifier];text=source['text'];start=text.index(start_text);end=text.index(end_text,start)+len(end_text);selected=text[start:end]
 start16=len(text[:start].encode('utf-16-le'))//2;end16=len(text[:end].encode('utf-16-le'))//2
 assert 0<end16-start16<=1200
 assert text.encode('utf-16-le')[2*start16:2*end16].decode('utf-16-le')==selected
 row={'id':identifier,'title':fields[6],'key':item['key'],'revision':fields[3],'record_sha256':fields[4],'text_sha256':fields[5],'date':fields[9],'article_url':fields[7],'history_url':fields[8],'rights_metadata':fields[10],'source_status':'pending_independent_review','start_utf16':start16,'end_utf16':end16,'span_sha256':sha(selected.encode()),'raw_scope':source['wikitext_scope'],'retained_raw_sha256':sha(source['wikitext'].encode()),'literal_complete_span_present_in_raw':selected in source['wikitext'],'builder_assessment':assessment,'independent_clearance':False}
 summaries.append(row);packet.append(dict(row,selected_text=selected,retained_raw=source['wikitext'],producer_ranges=source['wikitext_ranges']))
path=ROOT/'downloads/scale-answer/source-adjudication-packet.json';path.write_text(json.dumps(packet,indent=2,ensure_ascii=False)+'\n')
report={'kind':'Builder source adjudication preparation, not independent review or answer success','unchanged_primary_cases_sha256':sha((ROOT/'tools/evaluation/scale-answer/cases.json').read_bytes()),'packet_path':str(path.relative_to(ROOT)),'packet_sha256':sha(path.read_bytes()),'packet_bytes':path.stat().st_size,'dispositions':summaries,'literal_test_limit':'Literal absence does not prove extraction failure; markup changes spelling. Literal presence does not prove rights, relevance, completeness or semantic support.'}
(ROOT/'docs/evidence/scale-answer/strategy-change/source-dossier.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print('Seven bounded source-review candidates, one overlap exclusion, zero independent approvals; source bytes and UTF-16 spans verified')
