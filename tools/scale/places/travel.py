"""Build an offline English Wikivoyage HTML and listing database from a full ZIM.
Requires libzim; never accesses the network or changes the input archive.
"""
import hashlib,html.parser,json,pathlib,re,sqlite3,sys,time,zlib
from libzim.reader import Archive
class ListingParser(html.parser.HTMLParser):
 def __init__(self):
  super().__init__();self.stack=[];self.active=None;self.listings=[];self.text=[];self.skip=0
 def handle_starttag(self,tag,attrs):
  a=dict(attrs); classes=a.get('class','').split(); fields=[]
  if 'vcard' in classes and self.active is None:self.active={'depth':len(self.stack),'fields':{},'lat':None,'lon':None}
  if self.active is not None:
   if 'data-lat' in a:self.active['lat']=a['data-lat'];self.active['lon']=a.get('data-lon')
   fields=[c for c in classes if c.startswith('listing-')]
  if tag not in ('area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'):self.stack.append((tag,fields))
 def handle_endtag(self,tag):
  for i in range(len(self.stack)-1,-1,-1):
   if self.stack[i][0]==tag:
    del self.stack[i:]
    if self.active is not None and len(self.stack)<=self.active['depth']:
     self.listings.append(self.active);self.active=None
    break
 def handle_data(self,data):
  if any(t in ('script','style') for t,_ in self.stack):return
  self.text.append(data)
  if self.active is not None:
   for field in {f for _,fs in self.stack for f in fs}:self.active['fields'].setdefault(field,[]).append(data)
def build(source,dest):
 started=time.time(); source=pathlib.Path(source); dest=pathlib.Path(dest)
 if dest.exists():raise RuntimeError('Refusing to overwrite completed output')
 staging=dest.with_suffix('.building.sqlite'); db=sqlite3.connect(staging)
 db.executescript('''PRAGMA journal_mode=WAL; PRAGMA cache_size=-32768;
 CREATE TABLE IF NOT EXISTS page(path TEXT PRIMARY KEY,title TEXT,revision TEXT,revision_date TEXT,license_url TEXT,source_url TEXT,html_sha256 TEXT,html_zlib BLOB,text TEXT);
 CREATE TABLE IF NOT EXISTS listing(page TEXT,ordinal INTEGER,name TEXT,lat REAL,lon REAL,hours TEXT,fields_json TEXT,PRIMARY KEY(page,ordinal));
 CREATE INDEX IF NOT EXISTS listing_grid ON listing(lat,lon);
 CREATE INDEX IF NOT EXISTS listing_name ON listing(name);
 CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT);''')
 z=Archive(source); counts={'entries':z.entry_count,'redirects':0,'non_html':0,'pages':0,'listings':0,'revision_missing':0}
 for i in range(z.entry_count):
  e=z._get_entry_by_id(i)
  if e.is_redirect:counts['redirects']+=1;continue
  item=e.get_item()
  if str(item.mimetype)!='text/html':counts['non_html']+=1;continue
  if db.execute('SELECT 1 FROM page WHERE path=?',(e.path,)).fetchone():continue
  raw=bytes(item.content);h=raw.decode('utf-8'); parser=ListingParser();parser.feed(h)
  rev=re.search(r'https://en\.wikivoyage\.org/wiki/\?title=[^"<>]+oldid=(\d+)',h)
  date=re.search(r'Last edited on (\d{4}-\d{2}-\d{2})',h)
  lic=re.findall(r'https://creativecommons.org/licenses/[^"<> ]+',h)
  url=rev.group(0).replace('&amp;','&') if rev else None
  db.execute('INSERT INTO page VALUES(?,?,?,?,?,?,?,?,?)',(e.path,e.title,rev.group(1) if rev else None,date.group(1) if date else None,lic[-1] if lic else None,url,hashlib.sha256(raw).hexdigest(),zlib.compress(raw,6),' '.join(' '.join(parser.text).split())))
  counts['pages']+=1;counts['revision_missing']+=rev is None
  for j,l in enumerate(parser.listings):
   fields={k:' '.join(''.join(v).split()) for k,v in l['fields'].items()}
   try:lat=float(l['lat']);lon=float(l['lon'])
   except (TypeError,ValueError):lat=lon=None
   db.execute('INSERT INTO listing VALUES(?,?,?,?,?,?,?)',(e.path,j,fields.get('listing-name'),lat,lon,fields.get('listing-hours'),json.dumps(fields,ensure_ascii=False)));counts['listings']+=1
  if i%500==0:db.commit();print(i,counts,flush=True)
 db.execute('INSERT OR REPLACE INTO metadata VALUES(?,?)',('source_sha256',hashlib.file_digest(source.open('rb'),'sha256').hexdigest()))
 db.commit();db.execute('PRAGMA wal_checkpoint(TRUNCATE)');db.close();staging.rename(dest)
 counts.update(bytes=dest.stat().st_size,seconds=time.time()-started,source=str(source),sha256=hashlib.file_digest(dest.open('rb'),'sha256').hexdigest(),source_sha256=hashlib.file_digest(source.open('rb'),'sha256').hexdigest())
 dest.with_suffix('.report.json').write_text(json.dumps(counts,indent=2));print(counts)
if __name__=='__main__':build(*sys.argv[1:])
