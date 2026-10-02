"""Stream official revision XML into an immutable, bounded, inspectable provenance index."""
import argparse,bz2,collections,hashlib,json,re,sqlite3,time,zlib,resource
from pathlib import Path
from xml.etree import ElementTree as ET
NS='{http://www.mediawiki.org/xml/export-0.11/}'
def sha(b):return hashlib.sha256(b).hexdigest()
def utf16(s):return len(s.encode('utf-16-le'))//2
def base36(n):
 out=''
 while n:n,r=divmod(n,36);out='0123456789abcdefghijklmnopqrstuvwxyz'[r]+out
 return out or '0'
def value(e,name):return e.findtext(NS+name)
def build(archive,out,pin,limit=4_000_000_000):
 started=time.monotonic();assert not out.exists(),'Preserve previous index'
 with archive.open('rb') as f:h=hashlib.file_digest(f,'sha1').hexdigest()
 assert archive.stat().st_size==pin['size'] and h==pin['sha1'],'Official source archive mismatch'
 out.mkdir();db=sqlite3.connect(out/'provenance.sqlite');db.executescript('''PRAGMA cache_size=-8192; PRAGMA journal_mode=DELETE;
 CREATE TABLE documents(id INTEGER PRIMARY KEY,revision INTEGER NOT NULL UNIQUE,title TEXT NOT NULL,date TEXT NOT NULL,url TEXT NOT NULL,history_url TEXT NOT NULL,revision_url TEXT NOT NULL,text_sha1 TEXT NOT NULL,text_sha256 TEXT NOT NULL,raw_utf8_bytes INTEGER NOT NULL,raw_zlib BLOB NOT NULL,rights TEXT NOT NULL);
 CREATE TABLE spans(doc INTEGER,start_utf16 INTEGER,end_utf16 INTEGER,text TEXT NOT NULL,sha256 TEXT NOT NULL,PRIMARY KEY(doc,start_utf16));
 CREATE TABLE dispositions(id INTEGER,reason TEXT NOT NULL);
 CREATE TABLE partitions(partition INTEGER PRIMARY KEY,documents INTEGER NOT NULL,sample_id INTEGER,sample_hash TEXT);
 CREATE VIRTUAL TABLE search USING fts4(title,text,doc,tokenize=unicode61);
 ''');counts=collections.Counter();samples={};partition_counts=collections.Counter();seen=set();expanded=0
 class Bounded:
  def __init__(self,f):self.f=f
  def read(self,n=-1):
   nonlocal expanded
   b=self.f.read(n);expanded+=len(b)
   if expanded>limit:raise ValueError('Expanded archive exceeds admission')
   return b
 with bz2.open(archive,'rb') as source:
  events=ET.iterparse(Bounded(source),events=('start','end'));_,root=next(events)
  for event,page in events:
   if event!='end' or page.tag!=NS+'page':continue
   counts['pages']+=1;identifier=int(value(page,'id'));namespace=value(page,'ns');rev=page.find(NS+'revision')
   def exclude(reason):counts[reason]+=1;db.execute('INSERT INTO dispositions VALUES(?,?)',(identifier,reason))
   if identifier in seen:raise ValueError('Duplicate page identity')
   seen.add(identifier)
   if namespace!='0':exclude('non_article_namespace')
   elif page.find(NS+'redirect') is not None:exclude('redirect')
   elif rev is None or rev.find(NS+'text') is None:exclude('missing_revision_text')
   else:
    text=value(rev,'text') or '';raw=text.encode();declared=value(rev,'sha1');actual=base36(int(hashlib.sha1(raw).hexdigest(),16)).zfill(31)
    if not declared or actual!=declared:raise ValueError('Revision text SHA1 mismatch: '+str(identifier))
    if len(raw)>4_000_000:exclude('oversized_record')
    elif value(rev,'model')!='wikitext':exclude('non_wikitext_model')
    else:
     title=value(page,'title');revision=int(value(rev,'id'));date=value(rev,'timestamp');url='https://en.wikipedia.org/?curid='+str(identifier)
     db.execute('INSERT INTO documents VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(identifier,revision,title,date,url,'https://en.wikipedia.org/w/index.php?curid='+str(identifier)+'&action=history','https://en.wikipedia.org/w/index.php?oldid='+str(revision),declared,sha(raw),len(raw),zlib.compress(raw), 'pending_source_specific_rights_and_fidelity'))
     counts['indexed_documents']+=1;partition=identifier%16;partition_counts[partition]+=1;rank=sha(str(identifier).encode())
     if partition not in samples or rank<samples[partition][0]:samples[partition]=(rank,identifier)
     for m in re.finditer(r'[^\n]+(?:\n(?!\n)[^\n]+)*',text):
      block=m.group();a=m.start();b=m.end()
      # Preserve exact text; this exclusion is extraction policy, not rights clearance.
      if len(block)<80 or len(block)>4000 or any(c in block for c in '{}[]<>|\"“”') or block.startswith(('=','*','#',':',';')):continue
      start=utf16(text[:a]);end=start+utf16(block)
      db.execute('INSERT INTO spans VALUES(?,?,?,?,?)',(identifier,start,end,block,sha(block.encode())));db.execute('INSERT INTO search VALUES(?,?,?)',(title,block,identifier));counts['candidate_plain_spans']+=1
   root.remove(page);page.clear()
   if counts['pages']%1000==0:db.commit()
 for part,n in partition_counts.items():db.execute('INSERT INTO partitions VALUES(?,?,?,?)',(part,n,samples[part][1],samples[part][0]))
 db.commit();assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';db.close()
 result={'counts':dict(counts),'admitted_research_documents':0,'expanded_bytes':expanded,'index_bytes':(out/'provenance.sqlite').stat().st_size,'elapsed_s':time.monotonic()-started,'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'scope':'Host primary-source index, not installed Android or broad rights clearance','pin':pin,'partitions':{str(k):{'count':partition_counts[k],'representative_id':v[1]} for k,v in samples.items()}}
 (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('out',type=Path);p.add_argument('pin',type=Path);a=p.parse_args();print(json.dumps(build(a.archive,a.out,json.loads(a.pin.read_text())),indent=2))
