#!/usr/bin/env python3
"""Version 542 literal index. Original source records are copied without alteration."""
import argparse,hashlib,importlib.util,json,os,pathlib,sqlite3,sys,time
spec=importlib.util.spec_from_file_location('legacy_xml',pathlib.Path(__file__).with_name('adapter.py'));A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
FORMAT='pocketlore-wikitext-trigram-v1'
CONFIG={'gram_scalars':3,'normalization':'none','key':'UTF8-BLOB','candidate_budget':256,'body_priority':['text','title'],'max_unique_grams':262144,'index_max_bytes':67108864,'schema':542}
def grams(s):return {s[i:i+3].encode('utf8') for i in range(max(0,len(s)-2))}
def connect(path,readonly=False):
 db=sqlite3.connect('file:'+str(path.resolve())+'?mode=ro&immutable=1',uri=True) if readonly else sqlite3.connect(path)
 db.execute('PRAGMA cache_size=-2048');db.execute('PRAGMA mmap_size=0');db.execute('PRAGMA temp_store=FILE')
 if readonly:db.execute('PRAGMA query_only=ON')
 return db
def digest_index(db):
 h=hashlib.sha256()
 for term,gram,frequency in db.execute('SELECT term,gram,frequency FROM terms ORDER BY term'):
  h.update(A.canonical([term,gram.hex(),frequency])+b'\n')
 for term,ordinal in db.execute('SELECT term,ordinal FROM postings ORDER BY term,ordinal'):h.update(A.canonical([term,ordinal])+b'\n')
 return h.hexdigest()
def build(source,output,cancel=lambda:False,seconds=180):
 source=pathlib.Path(source);out=pathlib.Path(output);A.need(not out.exists(),'output-exists');out.mkdir(parents=True);guard=A.Guard(min(seconds,180),cancel);db=None;reader=None
 receipt={'index_format':FORMAT,'configuration':CONFIG,'status':'FAILED','errors':[],'samples':[],'started_ns':time.monotonic_ns(),'source_path':str(source),'indexed_records':0,'postings':0}
 try:
  receipt['samples'].append(A.sample('start'));before=A.version(source/'index.sqlite');receipt['input_before']=before;receipt['input_sha256']=A.filehash(source/'index.sqlite');reader=A.Reader(source);original=reader.receipt.copy();reader.guard=guard;guard.check()
  db=connect(out/'staging.sqlite');db.execute('PRAGMA max_page_count=16384');reader.db.backup(db,pages=128,progress=lambda *a:guard.check());db.executescript('CREATE TABLE terms(term INTEGER PRIMARY KEY,gram BLOB NOT NULL UNIQUE,frequency INTEGER NOT NULL DEFAULT 0); CREATE TABLE postings(term INTEGER NOT NULL,ordinal INTEGER NOT NULL,PRIMARY KEY(term,ordinal)) WITHOUT ROWID; CREATE TABLE search_order(ordinal INTEGER PRIMARY KEY,record_id INTEGER NOT NULL UNIQUE,stable_id TEXT NOT NULL UNIQUE); CREATE TABLE index_contract(key TEXT PRIMARY KEY,value TEXT NOT NULL);');db.execute('BEGIN');db.set_progress_handler(guard.sql,1000)
  for ordinal,(rid,ident) in enumerate(reader.db.execute("SELECT id,stable_id FROM records WHERE disposition='inspection-only' ORDER BY page,revision"),1):
   guard.check();r=reader.inspect(ident);keys=grams(r['text'])|grams(r['title']);A.need(len(keys)<=CONFIG['max_unique_grams'],'gram-bound');db.execute('INSERT INTO search_order VALUES(?,?,?)',(ordinal,rid,ident))
   for key in sorted(keys):
    guard.check();db.execute('INSERT OR IGNORE INTO terms(gram) VALUES(?)',(key,));term=db.execute('SELECT term FROM terms WHERE gram=?',(key,)).fetchone()[0];db.execute('INSERT INTO postings VALUES(?,?)',(term,ordinal));db.execute('UPDATE terms SET frequency=frequency+1 WHERE term=?',(term,))
   receipt['indexed_records']+=1;receipt['postings']+=len(keys)
   if ordinal%256==0:receipt['samples'].append(A.sample('records-'+str(ordinal)))
  for k,v in {'format':FORMAT,'configuration':CONFIG,'input_sha256':receipt['input_sha256'],'source_id':original['source_id'],'records':receipt['indexed_records'],'postings':receipt['postings'],'index_digest':digest_index(db)}.items():db.execute('INSERT INTO index_contract VALUES(?,?)',(k,json.dumps(v,sort_keys=True)))
  db.execute('PRAGMA user_version=542');db.commit();A.need(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','index-integrity');receipt['sqlite_version']=sqlite3.sqlite_version;receipt['compile_options']=[x[0] for x in db.execute('PRAGMA compile_options')];receipt['query_plan']=[list(x) for x in db.execute('EXPLAIN QUERY PLAN SELECT ordinal FROM postings WHERE term=? AND ordinal>? ORDER BY ordinal LIMIT 257',(1,0))];db.close();db=None
  receipt['input_after']=A.version(source/'index.sqlite');receipt['input_after_sha256']=A.filehash(source/'index.sqlite');A.need(before==receipt['input_after'] and receipt['input_sha256']==receipt['input_after_sha256'],'input-mutated');guard.check();os.rename(out/'staging.sqlite',out/'index.sqlite');receipt['output_sha256']=A.filehash(out/'index.sqlite');receipt['status']='BUILT_INSPECTION_ONLY';original.update(output_sha256=receipt['output_sha256'],index_format=FORMAT,parent_output_sha256=receipt['input_sha256']);A.atomic(out/'receipt.json',original)
 except (Exception,KeyboardInterrupt) as e:
  receipt['errors'].append(type(e).__name__+': '+str(e))
  if db is not None:db.rollback();db.close();db=None
 finally:
  if reader is not None:reader.close()
  receipt['ended_ns']=time.monotonic_ns();receipt['samples'].append(A.sample('closed'));receipt['storage']={p.name:p.stat().st_size for p in out.iterdir() if p.is_file()};A.atomic(out/'index-receipt.json',receipt)
 return receipt
class Reader(A.Reader):
 def __init__(self,path,expected_source=None,cancel=lambda:False):
  self.path=pathlib.Path(path);self.cancel=cancel;self.guard=A.Guard(10,cancel);self.receipt=json.loads((self.path/'receipt.json').read_text());ir=json.loads((self.path/'index-receipt.json').read_text());self.index_receipt=ir
  A.need(ir['status']=='BUILT_INSPECTION_ONLY' and not ir['errors'],'index-state');A.need(ir['configuration']==CONFIG and ir['index_format']==FORMAT,'tokenizer');A.need((self.path/'index.sqlite').stat().st_size<=CONFIG['index_max_bytes'],'index-size');self.output_hash=A.filehash(self.path/'index.sqlite');A.need(self.output_hash==ir['output_sha256']==self.receipt['output_sha256'],'index-hash');A.need(ir['input_before']==ir['input_after'] and ir['input_sha256']==ir['input_after_sha256']==self.receipt['parent_output_sha256'],'index-input')
  self.db=connect(self.path/'index.sqlite',True);self.db.set_progress_handler(self.guard.sql,1000)
  try:
   A.need(self.db.execute('PRAGMA user_version').fetchone()[0]==542,'index-schema');self.meta={k:json.loads(v) for k,v in self.db.execute('SELECT * FROM metadata')};contract={k:json.loads(v) for k,v in self.db.execute('SELECT * FROM index_contract')};A.need(contract['configuration']==CONFIG and contract['format']==FORMAT,'tokenizer');A.need(contract['input_sha256']==ir['input_sha256'],'index-input');A.need(contract['source_id']==self.meta['source_id']==self.receipt['source_id'] and (expected_source is None or expected_source==contract['source_id']),'index-source');A.need(self.meta['rights']=='unknown-unreviewed' and self.meta['admission'] is False,'index-admission')
   A.need(self.db.execute('SELECT count(*) FROM records').fetchone()[0]==self.receipt['records']==self.meta['records'],'record-count');n=self.db.execute('SELECT count(*) FROM search_order').fetchone()[0];A.need(n==contract['records']==ir['indexed_records'] and n==self.db.execute("SELECT count(*) FROM records WHERE disposition='inspection-only'").fetchone()[0],'index-count');A.need(self.db.execute('SELECT count(*) FROM postings').fetchone()[0]==contract['postings']==ir['postings'],'posting-count')
   A.need(digest_index(self.db)==contract['index_digest'],'index-digest')
   A.need(self.db.execute('SELECT count(*) FROM terms t WHERE frequency!=(SELECT count(*) FROM postings p WHERE p.term=t.term)').fetchone()[0]==0,'posting-frequency');A.need(self.db.execute('SELECT count(*) FROM postings p LEFT JOIN terms t USING(term) LEFT JOIN search_order s USING(ordinal) WHERE t.term IS NULL OR s.ordinal IS NULL').fetchone()[0]==0,'posting-reference')
   expected=list(self.db.execute("SELECT id,stable_id FROM records WHERE disposition='inspection-only' ORDER BY page,revision"));actual=list(self.db.execute('SELECT record_id,stable_id FROM search_order ORDER BY ordinal'));A.need(actual==expected and self.db.execute('SELECT coalesce(max(ordinal),0) FROM search_order').fetchone()[0]==n,'index-order')
  except Exception:self.db.close();raise
 def search(self,query,limit=20,cursor=None):
  A.need(isinstance(query,str) and 3<=len(query)<=256 and 0<limit<=20,'indexed-query-length');self.guard=A.Guard(10,self.cancel);self.guard.check();qhash=A.sha(query.encode());after=0
  if cursor is not None:
   A.need(set(cursor)=={'ordinal','query_sha256','output_sha256'} and cursor['query_sha256']==qhash and cursor['output_sha256']==self.output_hash and type(cursor['ordinal'])==int and cursor['ordinal']>=0,'cursor');after=cursor['ordinal']
  stats={'seed_candidates':0,'verified_candidates':0,'decompressions':0,'lexical_bytes':0,'full_scan':False};terms=[]
  for key in sorted(grams(query)):
   self.guard.check();r=self.db.execute('SELECT term,frequency FROM terms WHERE gram=?',(key,)).fetchone()
   if r is None:return {'hits':[],'complete':True,'cursor':None,'stats':stats}
   terms.append(r)
  seed=min(terms,key=lambda r:(r[1],r[0]))[0];rows=self.db.execute('SELECT ordinal FROM postings WHERE term=? AND ordinal>? ORDER BY ordinal LIMIT 257',(seed,after)).fetchall();hits=[];last=after
  for (ordinal,) in rows[:256]:
   self.guard.check();stats['seed_candidates']+=1;last=ordinal
   if not all(self.db.execute('SELECT 1 FROM postings WHERE term=? AND ordinal=?',(term,ordinal)).fetchone() for term,count in terms):continue
   ident=self.db.execute('SELECT stable_id FROM search_order WHERE ordinal=?',(ordinal,)).fetchone()[0];record=self.inspect(ident);stats['verified_candidates']+=1;stats['decompressions']+=1;stats['lexical_bytes']+=self.db.execute('SELECT bytes FROM records WHERE stable_id=?',(ident,)).fetchone()[0]
   for field in ['text','title']:
    at=record[field].find(query)
    if at<0:continue
    start=A.units(record[field][:at]);hits.append({'id':ident,'field':field,'start_utf16':start,'end_utf16':start+A.units(query),'quote':query,'quote_sha256':qhash,'source_text_sha256':record['text_sha256'],'admission':False});break
   if len(hits)>=limit:break
  more=bool(self.db.execute('SELECT 1 FROM postings WHERE term=? AND ordinal>? LIMIT 1',(seed,last)).fetchone());return {'hits':hits,'complete':not more,'cursor':{'ordinal':last,'query_sha256':qhash,'output_sha256':self.output_hash} if more else None,'stats':stats}
def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['build','search','inspect','export']);p.add_argument('source');p.add_argument('value');p.add_argument('destination',nargs='?');a=p.parse_args()
 if a.command=='build':r=build(a.source,a.value);print(json.dumps(r));return int(r['status']!='BUILT_INSPECTION_ONLY')
 r=Reader(a.source)
 try:print(json.dumps(r.search(a.value) if a.command=='search' else r.inspect(a.value) if a.command=='inspect' else r.export(a.value,a.destination),ensure_ascii=False))
 finally:r.close()
 return 0
if __name__=='__main__':sys.exit(main())
