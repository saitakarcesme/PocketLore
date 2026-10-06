"""Bounded read-only inspection of provisional v2; no factual admission."""
import hashlib,sqlite3,zlib
class InspectionReader:
 def __init__(self,path,cancelled=lambda:False):
  self.cancelled=cancelled;self.db=sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True)
  self.db.execute('PRAGMA query_only=ON');self.db.execute('PRAGMA cache_size=-2048');self.db.execute('PRAGMA mmap_size=0')
  self.db.set_progress_handler(lambda:1 if self.cancelled() else 0,1000)
 def close(self):self.db.close()
 def check(self):
  if self.cancelled():raise InterruptedError('Inspection cancelled')
 def search(self,query,limit=20):
  self.check()
  if not isinstance(query,str) or not 0<len(query)<=256 or not 1<=limit<=20:raise ValueError('Bounded query required')
  rows=self.db.execute('SELECT c.id,c.page,c.revision,c.node,c.start,c.end,c.title,substr(c.text,1,240),c.disposition FROM search JOIN contexts c ON c.id=search.docid WHERE search MATCH ? ORDER BY search.docid LIMIT ?',(query,limit)).fetchall();self.check();return rows
 def html_window(self,page,revision,start,end):
  if not 0<=start<end or end-start>8192:raise ValueError('UTF16 window must be at most 8192 units')
  self.check();rows=self.db.execute("SELECT p.start,p.end,c.sha,c.bytes,c.z FROM pieces p JOIN capsules c ON c.sha=p.sha WHERE page=? AND revision=? AND p.kind='html' AND p.end>? AND p.start<? ORDER BY part LIMIT 3",(page,revision,start,end)).fetchall()
  if not rows or len(rows)>2:raise ValueError('Missing or oversized source window')
  result=bytearray();cursor=start
  for a,b,digest,size,blob in rows:
   self.check();z=zlib.decompressobj();raw=z.decompress(blob,262145)
   if not z.eof or z.unconsumed_tail or z.unused_data or len(raw)!=size or size>262144 or hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('Corrupt source capsule')
   units=raw.decode('utf-8').encode('utf-16-le')
   if len(units)!=2*(b-a) or a>cursor:raise ValueError('Source window coordinates differ')
   stop=min(b,end);result.extend(units[2*(cursor-a):2*(stop-a)]);cursor=stop
  if cursor!=end:raise ValueError('Incomplete source window')
  self.check();return result.decode('utf-16-le')
