"""Stream a complete Wikimedia pages-articles XML snapshot; preserve wikitext."""
import bz2,hashlib,json,pathlib,sqlite3,sys,time,xml.etree.ElementTree as ET,zlib
from common import atomic_json
KINDS={'see','do','buy','eat','drink','sleep','listing','go'}
def split_fields(text):
 parts=[];start=0;braces=links=0;i=0
 while i<len(text):
  pair=text[i:i+2]
  if pair=='{{':braces+=1;i+=2;continue
  if pair=='}}':braces-=1;i+=2;continue
  if pair=='[[':links+=1;i+=2;continue
  if pair==']]':links-=1;i+=2;continue
  if text[i]=='|' and braces==0 and links==0:parts.append(text[start:i]);start=i+1
  i+=1
 parts.append(text[start:]);return parts
def listings(text):
 stack=[];i=0
 while i<len(text)-1:
  pair=text[i:i+2]
  if pair=='{{':stack.append(i);i+=2;continue
  if pair=='}}' and stack:
   start=stack.pop();raw=text[start:i+2];parts=split_fields(raw[2:-2]);kind=parts[0].strip().lower()
   if kind in KINDS:
    fields={};duplicates=[]
    for p in parts[1:]:
     if '=' not in p:continue
     k,v=p.split('=',1);k=k.strip();v=v.strip()
     if k in fields:duplicates.append(k)
     fields[k]=v
    yield kind,fields,duplicates,raw
   i+=2;continue
  i+=1
def build(src,dest):
 src=pathlib.Path(src);dest=pathlib.Path(dest)
 if dest.exists():raise RuntimeError('Immutable output exists')
 start=time.time();db=sqlite3.connect(dest.with_suffix('.building.sqlite'));db.executescript('''PRAGMA journal_mode=WAL; PRAGMA cache_size=-32768;
 CREATE TABLE page(id INTEGER PRIMARY KEY,title TEXT,namespace INTEGER,revision INTEGER,timestamp TEXT,sha1 TEXT,redirect TEXT,wikitext_zlib BLOB);
 CREATE TABLE listing(page INTEGER,ordinal INTEGER,kind TEXT,name TEXT,lat REAL,lon REAL,hours TEXT,fields_json TEXT,duplicate_fields TEXT,raw TEXT,PRIMARY KEY(page,ordinal));
 CREATE INDEX listing_name ON listing(name);CREATE INDEX listing_grid ON listing(lat,lon);
 CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);''')
 counts={'pages':0,'main_namespace_pages':0,'redirects':0,'listing_occurrences':0,'located_listing_occurrences':0,'hours_filled':0,'missing_text':0};ns='{http://www.mediawiki.org/xml/export-0.11/}'
 with bz2.open(src,'rb') as f:
  events=ET.iterparse(f,events=('start','end'));_,root=next(events)
  ns=root.tag.split('}')[0]+'}'
  for event,e in events:
   if event!='end' or e.tag!=ns+'page':continue
   identity=int(e.findtext(ns+'id'));title=e.findtext(ns+'title');namespace=int(e.findtext(ns+'ns'));rev=e.find(ns+'revision');text=rev.findtext(ns+'text') or '';revision=rev.findtext(ns+'id');redirect=e.find(ns+'redirect');redirect=redirect.get('title') if redirect is not None else None
   db.execute('INSERT INTO page VALUES(?,?,?,?,?,?,?,?)',(identity,title,namespace,revision,rev.findtext(ns+'timestamp'),rev.findtext(ns+'sha1'),redirect,zlib.compress(text.encode(),6)))
   counts['pages']+=1;counts['main_namespace_pages']+=namespace==0;counts['redirects']+=redirect is not None;counts['missing_text']+=not text
   if namespace==0 and redirect is None:
    for j,(kind,fields,duplicates,raw) in enumerate(listings(text)):
     try:lat=float(fields.get('lat',''));lon=float(fields.get('long',fields.get('lon','')));assert -90<=lat<=90 and -180<=lon<=180
     except (ValueError,AssertionError):lat=lon=None
     db.execute('INSERT INTO listing VALUES(?,?,?,?,?,?,?,?,?,?)',(identity,j,kind,fields.get('name'),lat,lon,fields.get('hours'),json.dumps(fields,ensure_ascii=False),json.dumps(duplicates),raw));counts['listing_occurrences']+=1;counts['located_listing_occurrences']+=lat is not None;counts['hours_filled']+=bool(fields.get('hours'))
   if counts['pages']%1000==0:db.commit();print(counts,flush=True)
   e.clear();root.clear()
 sha=hashlib.file_digest(src.open('rb'),'sha256').hexdigest();db.execute('INSERT INTO metadata VALUES(?,?)',('source_sha256',sha));db.execute('INSERT INTO metadata VALUES(?,?)',('license','CC-BY-SA-4.0; Wikimedia contributors; retain article revision/history links'))
 db.commit();assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';db.execute('PRAGMA wal_checkpoint(TRUNCATE)');db.close();dest.with_suffix('.building.sqlite').rename(dest)
 counts.update(source=str(src),source_sha256=sha,bytes=dest.stat().st_size,sha256=hashlib.file_digest(dest.open('rb'),'sha256').hexdigest(),seconds=time.time()-start,unique_place_count=None,parser_scope='literal listing templates only; no template expansion; raw wikitext retained')
 atomic_json(dest.with_suffix('.report.json'),counts);print(counts)
if __name__=='__main__':build(*sys.argv[1:])
