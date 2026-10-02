#!/usr/bin/env python3
"""Reproduce the bounded selected-text edition from immutable reviewed inputs, offline."""
import hashlib,json,zipfile,sys
from pathlib import Path
from prepare import ROOT,CACHE,prepare,sha
LOCK=Path(__file__).with_name('sources.lock.json')
DISPOSITION=ROOT/'docs/evidence/general-research/source-review.json'
def build(output,disposition=DISPOSITION):
 lock=json.loads(LOCK.read_text());packet=prepare();f=CACHE.parent/'review-packet.json'
 if sha(f.read_bytes())!=lock['review_packet_sha256'] or json.loads(f.read_text())!=packet:raise ValueError('Changed review packet or acquisition/extraction inputs')
 review=json.loads(Path(disposition).read_text())
 if review['packet_sha256']!=lock['review_packet_sha256']:raise ValueError('Review applies to another packet')
 license=(CACHE/'CC-BY-SA-4.0.txt').read_bytes();terms=(CACHE/'wikimedia-terms.html.text.txt').read_bytes()
 if sha(license)!=lock['license_sha256'] or sha(terms)!=lock['terms_sha256']:raise ValueError('Missing or changed license evidence')
 rows=[];docs=[]
 for d in packet['documents']:
  decision=review['documents'][d['id']]
  if decision['decision']!='admit-selected-spans':continue
  if decision['span_sha256']!=[s['sha256'] for s in d['spans']]:raise ValueError('Changed reviewed spans')
  for suffix in ['footer','history']:
   raw=CACHE/(str(d['revision'])+'-'+suffix+'.html')
   if sha(raw.read_bytes())!=decision[suffix+'_sha256']:raise ValueError('Changed rights context')
  rights='CC BY-SA 4.0; selected modified text also CC BY-SA 4.0; no added restrictions'
  notice='; '.join(n['text'] for n in d['attribution_notices'])
  attribution='Wikipedia contributors, '+d['title']+'; article '+d['article_url']+'; contributor history '+d['contributors_url']+('; '+notice if notice else '')
  doc=dict(id=d['id'],title=d['title'],url=d['revision_url'],source_date='Revision '+str(d['revision'])+' at '+d['revision_date'],retrieved_date='2026-10-02',attribution=attribution,license=rights,license_url='https://creativecommons.org/licenses/by-sa/4.0/',license_text=license.decode(),language='en',category='Bounded cross-topic reference',raw_sha256=d['parse_sha256'],source_text_format='selected rendered paragraphs, HTML/whitespace transformation',rights_basis='Selected-span independent source review; exact revision/footer/history and publisher terms retained in review packet',rights_disposition=decision['limitations']+' '+d['transformation']+' Original article footnotes are not app citations; linked reference works are not included offline. Source article: '+d['article_url']+'; revision: '+d['revision_url']+'; contributor history: '+d['contributors_url']+('; '+notice if notice else ''),passages=[])
  for s in d['spans']:
   text=s['text'];assert '\n' not in text and '\t' not in text
   citation=d['id']+'-'+s['sha256'][:16]
   doc['passages'].append(dict(id=citation,sha256=s['sha256'],source_utf16_start=s['start_utf16'],source_utf16_end=s['end_utf16'],source_span_sha256=s['sha256']))
   rows.append('\t'.join([citation,doc['title'],doc['url'],doc['source_date']+'; retrieved '+doc['retrieved_date'],attribution+'; '+rights+'; '+doc['license_url'],text]))
  docs.append(doc)
 if not docs:raise ValueError('No independently admitted real sources')
 payload=('\n'.join(rows)+'\n').encode()
 manifest=dict(schema=1,id=lock['edition'],language='en',transformation=packet['documents'][0]['transformation'],warning='Bounded selected Wikipedia paragraphs, not corpus-wide permission or verified generated answers. Two warned articles excluded. Changes: HTML/whitespace transformation and selected paragraphs under CC BY-SA4.0. Dated reference only.',documents=docs,passages_sha256=sha(payload),passage_count=len(rows))
 output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_STORED) as z:
  for name,data in [('manifest.json',(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()),('passages.tsv',payload)]:
   info=zipfile.ZipInfo(name,(2026,10,2,0,0,0));info.external_attr=0o100644<<16;z.writestr(info,data)
 return manifest
if __name__=='__main__':
 output=ROOT/'downloads/general-research/reviewed-reference.plpack';m=build(output);print(json.dumps({'documents':len(m['documents']),'passages':m['passage_count'],'bytes':output.stat().st_size,'sha256':sha(output.read_bytes())}))
