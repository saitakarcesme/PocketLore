"""Bounded inert inspection of v3, with explicit legacy v2 read support."""
import hashlib,json,pathlib,sqlite3,time,zlib
class InspectionReader:
 def __init__(self,path,cancelled=lambda:False,expected_index_sha256=None):
  self.cancelled=cancelled;self.query_deadline=None;self.path=pathlib.Path(path);self.index_verified=False
  def state():
   st=self.path.stat();return (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)
  self.file_state=state;self.initial_state=state()
  if expected_index_sha256 is not None:
   if self.initial_state[2]>67108864:raise ValueError('Verified inspection requires a bounded 64MiB shard')
   digest=hashlib.sha256()
   with self.path.open('rb') as file:
    while True:
     if cancelled():raise InterruptedError('Inspection cancelled')
     chunk=file.read(262144)
     if not chunk:break
     digest.update(chunk)
   if state()!=self.initial_state or digest.hexdigest()!=expected_index_sha256:raise ValueError('Changed inspection index identity')
   if any(pathlib.Path(str(self.path)+suffix).exists() for suffix in ('-wal','-journal')):raise ValueError('Inspection index has a live journal')
   self.index_verified=True
  self.db=sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True)
  self.db.execute('PRAGMA query_only=ON');self.db.execute('PRAGMA cache_size=-2048');self.db.execute('PRAGMA mmap_size=0')
  self.db.set_progress_handler(lambda:1 if self.cancelled() or (self.query_deadline is not None and time.monotonic()>self.query_deadline) else 0,1000)
  self.v3=self.db.execute("SELECT 1 FROM sqlite_master WHERE name='format'").fetchone() is not None
  if self.v3 and self.db.execute('SELECT name FROM format').fetchall()!=[('pocketlore-selected-structure-v3-provisional',)]:self.close();raise ValueError('Unsupported selected source format')
  required={'texts','contexts','pieces','capsules','articles','search'} if self.v3 else {'contexts','pieces','capsules','articles','search'}
  if not required <= {x[0] for x in self.db.execute('SELECT name FROM sqlite_master')}:self.close();raise ValueError('Incomplete selected source schema')
  if 'fts4' not in self.db.execute("SELECT sql FROM sqlite_master WHERE name='search'").fetchone()[0].lower():self.close();raise ValueError('Unsupported search schema')
  self.query_units=self.db.execute("SELECT 1 FROM sqlite_master WHERE name='query_contract'").fetchone() is not None
  if self.query_units and self.db.execute('SELECT name FROM query_contract').fetchall()!=[('inline-units-v1',)]:self.close();raise ValueError('Unsupported query contract')
 def close(self):self.db.close()
 def check(self):
  if self.cancelled():raise InterruptedError('Inspection cancelled')
  if self.query_deadline is not None and time.monotonic()>self.query_deadline:raise TimeoutError('Bounded query deadline')
  if self.index_verified and (self.file_state()!=self.initial_state or any(pathlib.Path(str(self.path)+suffix).exists() for suffix in ('-wal','-journal'))):raise ValueError('Inspection index changed after binding')
 def inflate(self,digest,size,blob):
  self.check();z=zlib.decompressobj();raw=z.decompress(blob,262145)
  if not z.eof or z.unconsumed_tail or z.unused_data or len(raw)!=size or size>262144 or hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('Corrupt source capsule')
  return raw
 def search(self,query,limit=20):
  self.check()
  if not isinstance(query,str) or not 0<len(query)<=256 or not 1<=limit<=20:raise ValueError('Bounded query required')
  if self.query_units:
   return [(h['unit_id'],h['page'],h['revision'],h['node'],h['snippet'],h['title'],h['kind']+'; inspection only') for h in self.search_hits(query,limit)]
  if self.v3:
   rows=self.db.execute('SELECT t.id,t.page,t.revision,t.node,substr(t.text,1,240),a.metadata FROM search JOIN texts t ON t.id=search.docid JOIN articles a ON a.page=t.page AND a.revision=t.revision WHERE search MATCH ? ORDER BY search.docid LIMIT ?',(query,limit)).fetchall()
   rows=[(i,page,rev,node,snippet,json.loads(meta)['name'],'Inspection only') for i,page,rev,node,snippet,meta in rows]
  else:rows=self.db.execute('SELECT c.id,c.page,c.revision,c.node,c.start,c.end,c.title,substr(c.text,1,240),c.disposition FROM search JOIN contexts c ON c.id=search.docid WHERE search MATCH ? ORDER BY search.docid LIMIT ?',(query,limit)).fetchall()
  self.check();return rows
 def nodes(self,page,revision,start=1,limit=128):
  self.check()
  if type(start) is not int or start<1 or not 1<=limit<=128:raise ValueError('Bounded node window required')
  result=[]
  for a,b,digest,size,blob in self.db.execute("SELECT p.start,p.end,c.sha,c.bytes,c.z FROM pieces p JOIN capsules c ON c.sha=p.sha WHERE page=? AND revision=? AND p.kind='structure' AND p.end>? AND p.start<? ORDER BY part LIMIT 129",(page,revision,start,start+limit)):
   group=json.loads(self.inflate(digest,size,blob))
   if not group or group[0][0]!=a or group[-1][0]+1!=b:raise ValueError('Node capsule range mismatch')
   result.extend(n for n in group if start<=n[0]<start+limit)
  if result and [n[0] for n in result]!=list(range(start,start+len(result))):raise ValueError('Missing node window')
  return result
 def context(self,page,revision,node):
  self.check();match=node;row=None
  for depth in range(65):
   row=self.db.execute('SELECT context_root,heading,disposition FROM contexts WHERE page=? AND revision=? AND node=?',(page,revision,node)).fetchone()
   if row:break
   current=self.nodes(page,revision,node,1)
   if not current or not current[0][1]:raise ValueError('Missing exact enclosing context')
   node=current[0][1]
  if not row:raise ValueError('Context depth bound')
  root=self.nodes(page,revision,row[0],1)
  if not root:raise ValueError('Missing enclosing context')
  # The caller renders the root in bounded windows, never an isolated matching leaf.
  return {'matched_node':match,'context_node':node,'root':root[0],'heading':self.nodes(page,revision,row[1],1) if row[1] else [],'disposition':row[2],'window_units':8192}
 def html_window(self,page,revision,start,end):
  if not 0<=start<end or end-start>8192:raise ValueError('UTF16 window must be at most 8192 units')
  self.check();rows=self.db.execute("SELECT p.start,p.end,c.sha,c.bytes,c.z FROM pieces p JOIN capsules c ON c.sha=p.sha WHERE page=? AND revision=? AND p.kind='html' AND p.end>? AND p.start<? ORDER BY part LIMIT 3",(page,revision,start,end)).fetchall()
  if not rows or len(rows)>2:raise ValueError('Missing or oversized source window')
  result=bytearray();cursor=start
  for a,b,digest,size,blob in rows:
   raw=self.inflate(digest,size,blob);units=raw.decode('utf-8').encode('utf-16-le')
   if len(units)!=2*(b-a) or a>cursor:raise ValueError('Source window coordinates differ')
   stop=min(b,end);result.extend(units[2*(cursor-a):2*(stop-a)]);cursor=stop
  if cursor!=end:raise ValueError('Incomplete source window')
  self.check();return result.decode('utf-16-le')
 def source_windows(self,page,revision,start,end):
  """Yield exact inert HTML windows without splitting a UTF16 surrogate pair."""
  if type(start) is not int or type(end) is not int or not 0<=start<end<=16000000:raise ValueError('Invalid bounded source range')
  cursor=start
  while cursor<end:
   self.check();stop=min(end,cursor+8192)
   try:text=self.html_window(page,revision,cursor,stop)
   except UnicodeDecodeError:
    if stop==end:raise ValueError('Source boundary splits a Unicode scalar')
    stop-=1
    try:text=self.html_window(page,revision,cursor,stop)
    except UnicodeDecodeError:raise ValueError('Source boundary splits a Unicode scalar')
   yield {'start16':cursor,'end16':stop,'original_html':text,'sha256':hashlib.sha256(text.encode()).hexdigest()}
   cursor=stop
 def verify_source(self,page,revision,binding):
  """Verify offline byte capsules against an externally frozen source binding.

  A verified hash or metadata license is not independent rights/answer admission.
  """
  self.check()
  row=self.db.execute('SELECT original_sha,html_sha,metadata FROM articles WHERE page=? AND revision=?',(page,revision)).fetchone()
  if not row:raise ValueError('Missing bound source')
  meta=json.loads(row[2]);expected=binding['metadata']
  if expected['identifier']!=page or expected['version']['identifier']!=revision or any(meta.get(k)!=v for k,v in expected.items()):raise ValueError('Changed source metadata')
  if (row[0],row[1])!=(binding['raw_sha256'],binding['html_sha256']):raise ValueError('Changed source identity')
  observations={}
  for kind,wanted in [('original',row[0]),('html',row[1])]:
   digest=hashlib.sha256();cursor=0;parts=0;total=0
   query="SELECT p.part,p.start,p.end,c.sha,c.bytes,c.z FROM pieces p JOIN capsules c ON c.sha=p.sha WHERE page=? AND revision=? AND p.kind=? ORDER BY part"
   for part,a,b,key,size,blob in self.db.execute(query,(page,revision,kind)):
    self.check()
    if part!=parts or a!=cursor or b<=a or parts>=2048:raise ValueError('Missing/reordered source capsule')
    raw=self.inflate(key,size,blob);units=len(raw) if kind=='original' else len(raw.decode('utf-8').encode('utf-16-le'))//2
    if units!=b-a:raise ValueError('Source capsule range mismatch')
    total+=len(raw)
    if total>16000000:raise ValueError('Source byte bound exceeded')
    digest.update(raw);parts+=1;cursor=b
   if not parts or digest.hexdigest()!=wanted:raise ValueError('Incomplete or corrupt bound source')
   observations[kind]={'sha256':wanted,'bytes':total,'parts':parts,'units':cursor}
  return {'page':page,'revision':revision,'metadata':expected,'verified_capsules':observations,'source_admission_established':False}
 def verified_context(self,page,revision,node,binding):
  """Bind an exact enclosing context, never an isolated quote as factual support."""
  if not self.index_verified:raise ValueError('Verified context requires an externally pinned index')
  identity=self.verify_source(page,revision,binding);context=self.context(page,revision,node);root=context['root'];a,b=root[4:6]
  if root[7]!='element' or not 0<=a<b<=identity['verified_capsules']['html']['units']:raise ValueError('Invalid context root')
  current=self.nodes(page,revision,context['context_node'],1)[0]
  chain=[current];ancestor=current[1]
  while ancestor:
   if len(chain)>=65:raise ValueError('Context ancestor bound')
   up=self.nodes(page,revision,ancestor,1)
   if not up or up[0][0]>=chain[-1][0]:raise ValueError('Invalid context ancestry')
   chain.append(up[0]);ancestor=up[0][1]
  tags={n[2] for n in chain};expected_root=current[0]
  if tags & {'blockquote','q'}:expected_root=next((n[0] for n in chain if n[2]=='section'),chain[-1][0])
  elif 'table' in tags:expected_root=next(n[0] for n in reversed(chain) if n[2]=='table')
  elif 'math' in tags:expected_root=next((n[0] for n in chain if n[2] in {'p','dd','dt','li','section'}),chain[-1][0])
  if root[0]!=expected_root:raise ValueError('Incomplete structural context')
  if not a<=current[4]<current[5]<=b:raise ValueError('Context excludes matched element')
  row=self.db.execute('SELECT start,end,fragment_sha FROM contexts WHERE page=? AND revision=? AND node=?',(page,revision,context['context_node'])).fetchone()
  if row[:2]!=(current[4],current[5]):raise ValueError('Context/node offsets disagree')
  fragment=hashlib.sha256()
  for window in self.source_windows(page,revision,*row[:2]):fragment.update(window['original_html'].encode())
  if fragment.hexdigest()!=row[2]:raise ValueError('Context fragment identity mismatch')
  root_hash=hashlib.sha256();windows=0
  for window in self.source_windows(page,revision,a,b):root_hash.update(window['original_html'].encode());windows+=1
  self.check()
  return {'identity':identity,'context':context,'start16':a,'end16':b,'original_fragment_sha256':root_hash.hexdigest(),'window_count':windows,'display_kind':'Inert original source inspection','generation_eligible':False}

 def search_hits(self,query,limit=20):
  self.query_deadline=time.monotonic()+2
  try:return self._search_hits(query,limit)
  finally:self.query_deadline=None
 def _search_hits(self,query,limit=20):
  """Stable source-aware hits; title discovery is explicitly metadata only."""
  self.check()
  if not self.query_units:raise ValueError('Coherent queries require inline-units-v1; legacy leaf search remains separate')
  if not isinstance(query,str) or not 0<len(query)<=256 or type(limit) is not int or not 1<=limit<=20:raise ValueError('Bounded query required')
  rows=self.db.execute('SELECT q.id,q.page,q.revision,q.node,q.kind,q.projection_sha,substr(c.text,1,240),a.metadata,a.original_sha,a.html_sha FROM search JOIN query_units q ON q.id=search.docid JOIN query_content c ON c.rowid=q.id JOIN articles a ON a.page=q.page AND a.revision=q.revision WHERE search MATCH ? ORDER BY q.id LIMIT ?',(query,limit)).fetchall()
  hits=[]
  for uid,page,rev,node,kind,digest,text,metadata,original,html in rows:
   self.check()
   projected=hashlib.sha256();total=0
   if kind=='metadata-title':parts=[json.loads(metadata)['name']]
   else:
    parts=(part[0] for part in self.db.execute('SELECT t.text FROM texts t JOIN query_units q ON t.page=q.page AND t.revision=q.revision AND t.node BETWEEN q.first_node AND q.last_node WHERE q.id=? ORDER BY t.node',(uid,)))
   for part in parts:
    self.check();raw=part.encode();total+=len(raw)
    if total>16000000:raise ValueError('Query projection bound')
    projected.update(raw)
   if text is None or projected.hexdigest()!=digest:raise ValueError('Query projection mismatch')
   meta=json.loads(metadata)
   hits.append({'unit_id':uid,'page':page,'revision':rev,'node':node,'kind':kind,'title':meta['name'],'snippet':text[:240],'projection_sha256':digest,'raw_sha256':original,'html_sha256':html,'attribution_url':meta['url'],'license':meta['license'],'generation_eligible':False})
  self.check();return hits
 def open_hit(self,hit,binding):
  """Open a hash-bound exact source; this never turns a hit into answer support."""
  self.check()
  if not self.index_verified:raise ValueError('Source opening requires a pinned immutable shard')
  row=self.db.execute('SELECT page,revision,node,kind,projection_sha FROM query_units WHERE id=?',(hit['unit_id'],)).fetchone()
  if row!=(hit['page'],hit['revision'],hit['node'],hit['kind'],hit['projection_sha256']):raise ValueError('Changed source hit')
  page,rev=hit['page'],hit['revision'];identity=self.verify_source(page,rev,binding)
  if hit['raw_sha256']!=binding['raw_sha256'] or hit['html_sha256']!=binding['html_sha256'] or hit['attribution_url']!=binding['metadata']['url'] or hit['license']!=binding['metadata']['license'] or hit['title']!=binding['metadata']['name']:raise ValueError('Changed hit provenance')
  if hit['kind']=='metadata-title':
   return {'kind':'article-metadata','identity':identity,'title':hit['title'],'start16':0,'end16':identity['verified_capsules']['html']['units'],'display_kind':'Source title and attribution; not factual sentence support','generation_eligible':False}
  if hit['kind']!='source-context':raise ValueError('Unsupported source hit')
  result=self.verified_context(page,rev,hit['node'],binding);result['kind']='source-context';return result
