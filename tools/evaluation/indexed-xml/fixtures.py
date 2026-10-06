"""Frozen deterministic CC0 direct engineering capsules; not XML ingestion evidence."""
import hashlib,json,pathlib,sqlite3,zlib

def create(A,out,count):
 out=pathlib.Path(out);out.mkdir(exist_ok=False);db=sqlite3.connect(out/'index.sqlite');db.executescript(A.SCHEMA);sid=hashlib.sha256(('CC0-index-fixture-v1-'+str(count)).encode()).hexdigest();oracles=[]
 for i in range(1,count+1):
  title='Title %05d'%i;body='Common source record %05d. Literal (OR "quoted") {{table|x=2}} <math>a+b</math> 😀éZ.'%i
  if i==count:body+=' LateNeedleZXQ.'
  if count<8192:
   body+='\r\n{|\n! Header !! Value\n| unit || 2\n|}\n<ref>conditional otherwise</ref> {{T|x=1}} Repeat Repeat.';title+=' TitleOnlyNeedle'
  assert len((title+body).encode())<=512
  lexical=body.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').encode();meta={'source_id':sid,'source_format':'mediawiki-xml-wikitext','format':A.FORMAT,'page_fields':{'id':{'value':str(i),'attrs':{}},'title':{'value':title,'attrs':{}}},'revision_fields':{'id':{'value':str(i+10000),'attrs':{}},'timestamp':{'value':'2026-10-06T00:00:00Z','attrs':{}}},'page':i,'revision':i+10000,'title':title,'namespace':0,'redirect':None,'contributor':{},'contributor_attrs':{},'text_attributes':{},'text_available':True,'text_xml_range':[10,10+len(lexical)],'page_xml_range':[0,20+len(lexical)],'coordinate_system':'decoded-original-wikitext-utf16-preserved-line-endings','publisher_sha1_verified':False,'rights':'unknown-unreviewed','admission':False}
  cm={k:v for k,v in meta.items() if k not in ['page_xml_range','text_xml_range']};meta['binding']=A.sha(A.canonical(cm)+lexical);ident=sid+':'+str(i)+':'+str(i+10000)
  db.execute('INSERT INTO records VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(i,ident,i,i+10000,title,0,A.canonical(meta).decode(),zlib.compress(lexical),A.sha(body.encode()),A.sha(lexical),len(body.encode()),A.units(body),'inspection-only'));db.execute('INSERT INTO ledger VALUES(?,?,?,?,?)',(i,i,i+10000,'inspection-only',meta['binding']));oracles.append({'id':ident,'title':title,'text':body})
 for k,v in {'format':A.FORMAT,'source_id':sid,'status':'COMPLETE_ENGINEERING_INPUT','rights':'unknown-unreviewed','admission':False,'source_format':'mediawiki-xml-wikitext','search':'bounded-literal-original-scan-no-FTS','records':count}.items():db.execute('INSERT INTO metadata VALUES(?,?)',(k,json.dumps(v)))
 db.commit();db.close();A.atomic(out/'receipt.json',{'status':'COMPLETE_ENGINEERING_INPUT','errors':[],'source_id':sid,'records':count,'decoded_bytes':4096,'output_sha256':A.filehash(out/'index.sqlite'),'fixture':'CC0 direct capsule; coordinates are authored fixture geometry, not actual XML parse'})
 return oracles

def expected(A,rows,query,limit=20):
 hits=[]
 for r in rows:
  for field in ['text','title']:
   at=r[field].find(query)
   if at<0:continue
   a=A.units(r[field][:at]);hits.append({'id':r['id'],'field':field,'start_utf16':a,'end_utf16':a+A.units(query),'quote':query,'quote_sha256':A.sha(query.encode()),'source_text_sha256':A.sha(r['text'].encode()),'admission':False});break
  if len(hits)>=limit:break
 return hits
