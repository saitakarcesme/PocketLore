#!/usr/bin/env python3
"""Prepare bounded review packets from retained exact publisher revisions, never bulk labels."""
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/packs/broad/repair'))
from extract import extract
CACHE=ROOT/'downloads/general-research/acquisition'
def sha(b):return hashlib.sha256(b).hexdigest()
def prepare():
 documents=[]
 for name in ['wiki-current.json','wiki-additional.json']:
  for p in json.loads((CACHE/name).read_text())['query']['pages'].values():
   rev=p['revisions'][0];file=CACHE/(str(rev['revid'])+'.json')
   if not file.exists():continue
   raw=file.read_bytes();parsed=json.loads(raw)['parse'];assert parsed['revid']==rev['revid']
   extracted=extract(parsed['text']['*']);blocks=[];excluded=list(extracted['excluded'])
   for item in extracted['blocks']:
    if item['section']!='Lead':continue
    text=item['text']
    if text.endswith(':') or len(text)>2200:
     excluded.append({'sha256':sha(text.encode()),'reason':'Incomplete lead-in or oversized paragraph; dependent list/context not selected'});continue
    if p['title']=='Printing press' and 'invented by the German' in text:
     excluded.append({'sha256':sha(text.encode()),'reason':'Broad invention claim omits earlier East Asian movable-type context; not selected for this introductory packet'});continue
    if len(blocks)<4:blocks.append(text)
   body='\n\n'.join(blocks);offset=0;spans=[]
   for text in blocks:
    n=len(text.encode('utf-16-le'))//2;spans.append({'text':text,'sha256':sha(text.encode()),'start_utf16':offset,'end_utf16':offset+n});offset+=n+2
   documents.append({'id':'primary-wiki-'+str(p['pageid']),'title':p['title'],'revision':rev['revid'],'parent_revision':rev['parentid'],'revision_date':rev['timestamp'],'article_url':'https://en.wikipedia.org/?curid='+str(p['pageid']),'revision_url':'https://en.wikipedia.org/w/index.php?oldid='+str(rev['revid']),'contributors_url':'https://en.wikipedia.org/w/index.php?curid='+str(p['pageid'])+'&action=history','parse_file':file.name,'parse_sha256':sha(raw),'wikitext_sha256':sha(rev['slots']['main']['*'].encode()),'extracted_sha256':sha(body.encode()),'body':body,'spans':spans,'attribution_notices':extracted['attribution_notices'],'excluded':excluded,'rights_status':'pending independent selected-span review','transformation':'Selected complete lead paragraphs; HTML removed, whitespace normalized; source TeX/subscripts/superscripts retained explicitly. References remain article footnotes, not app citations. No media, externally quoted text or linked works.'})
 return {'edition':'reviewed-reference-2026-10-02-v1','acquisition':'Direct publisher API revision metadata and rendered oldid, not a bulk dataset; nine articles before HTTP429 stopped acquisition. Wikipedia is collaborative secondary reference, not primary scientific research.','documents':documents}
if __name__=='__main__':
 p=CACHE.parent/'review-packet.json';p.write_text(json.dumps(prepare(),indent=2,ensure_ascii=False)+'\n');print(p)
