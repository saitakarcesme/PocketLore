#!/usr/bin/env python3
"""Build a new rendered-source edition; refuse incomplete source/semantic review."""
from pathlib import Path
import argparse,json,hashlib,sqlite3,collections,zipfile,unicodedata,re
ROOT=Path(__file__).resolve().parents[4];STAGE=ROOT/'downloads/broad-reference/html-v2'
def digest(b):return hashlib.sha256(b).hexdigest()
def norm(t):return ' '.join(unicodedata.normalize('NFKC',t).casefold().split())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def notice_supported(n):
 t=n['text']
 return bool(n['links']) and (t.startswith('This article incorporates text from a publication now in the public domain:') or t.startswith('This article incorporates public domain material from ') or 'Licensed under CC BY 4.0' in t or 'available under a Creative Commons Attribution 4.0 International License' in t)
def eligible(d):
 if not d['blocks']:return 'No eligible narrative paragraphs'
 if any(not notice_supported(n) for n in d['attribution_notices']):return 'Unresolved additional attribution terms: excluded, exact notices retained in audit'
 if any(len(x['text'])>32000 for x in d['blocks']):return 'Paragraph exceeds bounded Android source-row admission'
 html=(STAGE/(d['id']+'.html')).read_text()
 if 'https://creativecommons.org/licenses/by-sa/4.0/' not in html:return 'CC BY-SA 4.0 footer unavailable'
 if not re.search(r'"wgRevisionId"\s*:\s*'+str(d['revision']['revid'])+r'\b',html):return 'Rendered revision does not match metadata'
 return None

def build(out,review):
 assert not out.exists(),'Preserve previous builds; choose a new directory'
 from seal import validate
 seal=validate();sealed={d['id']:d for d in seal['documents']}
 reviews=json.loads(review.read_text());assert reviews['status']=='builder-source-reviewed'
 approved={r['id']:r for r in reviews['documents']};areas=collections.Counter();docs=[];excluded=[]
 for p in sorted((STAGE/'extracted').glob('*.json'),key=lambda p:int(p.stem)):
  d=json.loads(p.read_text());reason=eligible(d)
  if reason:excluded.append({'id':d['id'],'title':d['title'],'reason':reason,'notices':d['attribution_notices']});continue
  assert sha(STAGE/(d['id']+'.html'))==d['html_sha256']==sealed[d['id']]['html_sha256'] and d['revision']==sealed[d['id']]['revision']
  if d['id'] in approved:
   r=approved[d['id']];assert r['html_sha256']==d['html_sha256'] and r['support_text'] in '\n'.join(x['text'] for x in d['blocks']);assert r['reason'];area=r['area'];areas[area]+=1
  else:area='Other reference (not counted toward area quotas)'
  d['area']=area;docs.append(d)
 assert len(areas)==8 and min(areas.values())>=50,dict(areas)
 assert len(docs)>=1000,len(docs)
 out.mkdir(parents=True);db=out/'index.sqlite';c=sqlite3.connect(db)
 c.executescript('''PRAGMA page_size=4096; PRAGMA journal_mode=DELETE;
 CREATE TABLE documents(id TEXT PRIMARY KEY,title TEXT NOT NULL,url TEXT NOT NULL UNIQUE,date TEXT NOT NULL,rights TEXT NOT NULL,provenance TEXT NOT NULL,body TEXT NOT NULL,sha TEXT NOT NULL UNIQUE,area TEXT NOT NULL);
 CREATE TABLE passages(pid INTEGER PRIMARY KEY,citation TEXT NOT NULL UNIQUE,document TEXT NOT NULL REFERENCES documents(id),body TEXT NOT NULL,sha TEXT NOT NULL UNIQUE,normalized_sha TEXT NOT NULL UNIQUE,start INTEGER NOT NULL,end INTEGER NOT NULL);
 CREATE INDEX passage_document ON passages(document);
 CREATE VIRTUAL TABLE search USING fts4(title,body,tokenize=porter);
 PRAGMA user_version=210;''')
 count=0;seen=set();source_seen=set();receipts=[]
 for d in docs:
  body='\n\n'.join(b['text'] for b in d['blocks']);body_sha=digest(body.encode());ns=digest(norm(body).encode());assert ns not in source_seen;source_seen.add(ns)
  rev=d['revision']['revid'];url='https://en.wikipedia.org/w/index.php?oldid='+str(rev);history='https://en.wikipedia.org/w/index.php?title='+__import__('urllib.parse',fromlist=['quote']).quote(d['title'].replace(' ','_'))+'&action=history'
  rights='CC BY-SA 4.0; https://creativecommons.org/licenses/by-sa/4.0/; '+d['title']+' — Wikipedia contributors; retain attribution/history/license, indicate changes, share adaptations alike. Media and quoted paragraphs excluded; source-specific attribution notices and terms retained below; unresolved additional terms excluded.'
  refs='\n'.join(r['text']+' '+ ' '.join(r['links']) for r in d['references'])
  provenance='\n'.join([d['title']+' — Wikipedia contributors','Article revision: '+str(rev),'Contributor history: '+history,'Rendered HTML SHA-256: '+d['html_sha256'],'Source SHA-256: '+body_sha,'Modifications: Selected narrative paragraphs; whitespace normalized; source math copied as TeX; superscript/subscript marked; media, quoted blocks, tables and navigation omitted. References retained below.','Generation disabled: reviewed source edition still requires separate model-support validation.','Source-specific attribution notices:', '\n'.join(n['text']+' '+ ' '.join(n['links']) for n in d['attribution_notices']), 'Reference list (source attribution, not a claim of source access):',refs])
  date=d['revision']['timestamp']+' (article revision; rendered snapshot 2026-10-01)'
  c.execute('INSERT INTO documents VALUES(?,?,?,?,?,?,?,?,?)',(d['id'],d['title'],url,date,rights,provenance,body,body_sha,d['area']))
  offset=0
  for b in d['blocks']:
   t=b['text'];h=digest(t.encode());nh=digest(norm(t).encode());start=len(body[:offset].encode('utf-16-le'))//2;end=start+len(t.encode('utf-16-le'))//2
   assert body[offset:offset+len(t)]==t;offset+=len(t)+2
   if nh in seen:continue
   seen.add(nh);count+=1;c.execute('INSERT INTO passages VALUES(?,?,?,?,?,?,?,?)',(count,'wiki-'+d['id']+'-'+h[:16],d['id'],t,h,nh,start,end));c.execute('INSERT INTO search(docid,title,body) VALUES(?,?,?)',(count,d['title'],t))
  receipts.append({'id':d['id'],'title':d['title'],'revision':d['revision'],'html_sha256':d['html_sha256'],'source_sha256':body_sha,'area':d['area'],'math':d['math_representations'],'references':len(d['references']),'quoted_blocks_excluded':len(d['excluded']),'attribution_notices':d['attribution_notices']})
 assert count>=10000 and count<=100000,count
 c.commit();c.execute('VACUUM');assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok';schema=c.execute('SELECT name,sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY name').fetchall();c.close()
 assert db.stat().st_size<=256*1024*1024,db.stat().st_size
 m={'format':'pocketlore-sqlite-v1','id':'broad-reference-rendered-20261001-v2','documents':len(docs),'passages':count,'areas':dict(areas),'area_count_definition':'Source-body reviewed subset only; other genuine documents do not count toward semantic quotas','db_sha256':sha(db),'db_bytes':db.stat().st_size,'schema':schema,'license':'CC-BY-SA-4.0','distribution_ready':False,'source_review':'Rendered revisions, math and units retained; quoted paragraphs excluded; source-specific notices retained; unresolved additional terms excluded; builder semantic review recorded; independent acceptance pending','warning':'Revision-pinned reference, not live travel/safety advice. Generation disabled pending model-support validation.','review_sha256':sha(review),'acquisition_receipts_sha256':seal['receipts_sha256']}
 pack=out/'broad-reference.plpack';legal=ROOT/'downloads/broad-reference/v1/broad-reference.plpack'
 with zipfile.ZipFile(legal) as old,zipfile.ZipFile(pack,'w',zipfile.ZIP_DEFLATED) as z:
  for name,data in [('manifest.json',(json.dumps(m,sort_keys=True,indent=2)+'\n').encode()),('index.sqlite',db.read_bytes()),('CC-BY-SA-4.0.html',old.read('CC-BY-SA-4.0.html'))]:
   i=zipfile.ZipInfo(name,(2026,10,1,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,data)
 assert pack.stat().st_size<=128*1024*1024
 (out/'build.json').write_text(json.dumps({**m,'pack_sha256':sha(pack),'pack_bytes':pack.stat().st_size,'sources':receipts,'excluded':excluded},indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--review',type=Path,required=True);a=p.parse_args();build(a.out,a.review)
