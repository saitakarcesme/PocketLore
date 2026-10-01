"""Mechanical paragraph pairing for independent inspection, never semantic clearance."""
import pathlib,json,hashlib,re,difflib
from html.parser import HTMLParser
ROOT=pathlib.Path(__file__).resolve().parents[3]
class Paragraphs(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.level=0;self.parts=[];self.rows=[]
 def handle_starttag(self,tag,attrs):
  if tag=='p':
   if self.level:self.rows.append(''.join(self.parts))
   self.level=1;self.parts=[]
 def handle_endtag(self,tag):
  if tag=='p' and self.level:self.rows.append(''.join(self.parts));self.level=0
 def handle_data(self,data):
  if self.level:self.parts.append(data)
normalize=lambda s:re.sub(r'\s+',' ',s).strip()
packet=json.loads((ROOT/'downloads/scale-answer/source-adjudication-packet.json').read_text())
receipts=json.loads((ROOT/'docs/evidence/scale-answer/strategy-change/revision-context.json').read_text())['receipts'];rows=[];detail=[]
for selected in packet:
 receipt=next(r for r in receipts if r['id']==selected['id'])
 if receipt['status']!='identity_verified_not_rights_cleared':rows.append({'id':selected['id'],'status':'context_acquisition_failed'});continue
 raw=(ROOT/receipt['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==receipt['sha256']
 parser=Paragraphs();parser.feed(raw.decode('utf-8'));target=normalize(selected['selected_text'])
 candidates=[normalize(p) for p in parser.rows if normalize(p)];matches=[p for p in candidates if target in p]
 # Similarity only pairs a differing paragraph for a reviewer; it cannot approve extraction.
 best=matches[0] if matches else max(candidates,key=lambda p:difflib.SequenceMatcher(None,target,p,autojunk=False).ratio())
 row={'id':selected['id'],'revision':selected['revision'],'source_html_sha256':receipt['sha256'],'selected_span_sha256':selected['span_sha256'],'paragraph_text_sha256':hashlib.sha256(best.encode()).hexdigest(),'selected_text_present_after_whitespace_normalization':bool(matches),'builder_review_status':'pending_independent_rights_and_fidelity_review','method':'HTMLParser paragraph text includes citation/math text; differences must be inspected, not silently normalized away.'}
 rows.append(row);detail.append(dict(row,selected_text=selected['selected_text'],paired_html_paragraph=best,selected_utf16=[selected['start_utf16'],selected['end_utf16']],license_links=receipt['license_links'],history_url=selected['history_url']))
path=ROOT/'downloads/scale-answer/paired-source-review.json';path.write_text(json.dumps(detail,indent=2,ensure_ascii=False)+'\n')
(ROOT/'docs/evidence/scale-answer/strategy-change/paragraph-comparison.json').write_text(json.dumps({'rows':rows,'packet_path':str(path.relative_to(ROOT)),'packet_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'disclaimer':'Matching paragraph bytes do not prove source-specific rights, question relevance, semantic entailment or complete answers.'},indent=2)+'\n')
print(json.dumps(rows,indent=2))
