"""Independent exact ownership and authored-original export oracles."""
import copy,re,json,ast,types,pathlib,hashlib
import core as C
R=C.R;S=C.S

def pidfd_identity(raw,expected):
 C.need(type(expected) is int and expected>0,'pidfd-expected-owner')
 C.need(isinstance(raw,str) and len(raw)<=16384,'pidfd-shape');values=[]
 for line in raw.splitlines():
  if line.split(':',1)[0].strip()=='Pid':
   C.need(re.fullmatch(r'Pid:[ \t]*[1-9][0-9]*[ \t]*',line) is not None,'pidfd-Pid-shape');values.append(int(line.split(':',1)[1]))
 C.need(len(values)==1,'pidfd-Pid-cardinality');C.need(values[0]==expected,'pidfd-owner')

def expected_export():
 # Frozen CC0 authored strings and metadata specification, independent of Reader/export.
 rows=S.F.oracle_rows(8);hit=S.F.expected(S.A,rows,'Common',1)[0];row=next(x for x in rows if x['id']==hit['id']);sid,page,rev=row['id'].split(':');page=int(page);rev=int(rev);raw=row['text'].encode('utf-8')
 lexical=row['text'].replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').encode('utf-8')
 meta={'source_id':sid,'source_format':'mediawiki-xml-wikitext','format':'pocketlore-original-wikitext-v1','page_fields':{'id':{'value':str(page),'attrs':{}},'title':{'value':row['title'],'attrs':{}}},'revision_fields':{'id':{'value':str(rev),'attrs':{}},'timestamp':{'value':'2026-10-06T00:00:00Z','attrs':{}}},'page':page,'revision':rev,'title':row['title'],'namespace':0,'redirect':None,'contributor':{},'contributor_attrs':{},'text_attributes':{},'text_available':True,'text_xml_range':[10,10+len(lexical)],'page_xml_range':[0,20+len(lexical)],'coordinate_system':'decoded-original-wikitext-utf16-preserved-line-endings','publisher_sha1_verified':False,'rights':'unknown-unreviewed','admission':False}
 cm={k:v for k,v in meta.items() if k not in ['page_xml_range','text_xml_range']};meta['binding']=R.sha(R.canonical(cm)+lexical)
 metadata={'id':row['id'],'title':row['title'],'metadata':meta,'text_sha256':R.sha(raw),'lexical_sha256':R.sha(lexical),'disposition':'inspection-only'}
 return hit,raw,metadata

def export_identity(raw,metadata,receipt,hit):
 wanted,text,meta=expected_export();C.need(hit==wanted,'export-first-hit');C.need(type(raw) is bytes and raw==text,'export-original-bytes')
 C.need(receipt=={'bytes':len(text),'sha256':R.sha(text),'files':['original.wikitext','metadata.json']},'export-original-receipt')
 C.need(metadata.get('id')==meta['id'],'export-source-id');C.need(metadata.get('title')==meta['title'],'export-title');C.need(metadata.get('text_sha256')==meta['text_sha256'] and metadata.get('lexical_sha256')==meta['lexical_sha256'],'export-source-hash')
 C.need(metadata.get('metadata',{}).get('revision')==meta['metadata']['revision'],'export-revision');C.need(metadata==meta,'export-source-metadata')

def controls():
 # Historical genuine positive before every deep mutation; no child or new capsule.
 packet=json.loads(R.git_bytes('a20a1ffd13ef208cc2205a82d23ebb4b44445c80','docs/evidence/indexed-frozen-recovery-review.json'));d=packet['files']['downloads/indexed-frozen-546/positive/receipt.json'];w=R.consume(d,True);pid=w['pid'];raw=w['pidfd_info'];out=[]
 tests=[('prefix','Pid:\t'+str(pid)+'0\n','pidfd-owner'),('suffix','Pid:\t9'+str(pid)+'\n','pidfd-owner'),('missing','flags:\t02000002\n','pidfd-Pid-cardinality'),('duplicate',raw+'Pid:\t'+str(pid)+'\n','pidfd-Pid-cardinality'),('conflicting',raw+'Pid:\t1\n','pidfd-Pid-cardinality'),('garbage','Pid:\t'+str(pid)+'junk\n','pidfd-Pid-shape'),('negative','Pid:\t-1\n','pidfd-Pid-shape'),('zero','Pid:\t0\n','pidfd-Pid-shape'),('wrong','Pid:\t1\n','pidfd-owner')]
 for name,changed,guard in tests:
  pidfd_identity(raw,pid)
  try:pidfd_identity(changed,pid)
  except R.Refused as e:C.need(str(e)==guard,'pidfd-control-guard');out.append({'name':name,'value':changed,'guard':guard})
  else:raise R.Refused('pidfd-mutant-accepted')
 original=R.consume(packet['files']['downloads/indexed-frozen-546/export/original.wikitext']);metadata=R.consume(packet['files']['downloads/indexed-frozen-546/export/metadata.json'],True);hit,_,_=expected_export();receipt={'bytes':len(original),'sha256':R.sha(original),'files':['original.wikitext','metadata.json']};exports=[]
 for name in ['text','id','title','revision','source','rights','hash']:
  export_identity(original,metadata,receipt,hit);b=original;m=copy.deepcopy(metadata);r=copy.deepcopy(receipt)
  if name=='text':b=b'X'+original[1:];r['sha256']=R.sha(b);m['text_sha256']=R.sha(b)
  elif name=='id':m['id']='wrong-source:1:10001'
  elif name=='title':m['title']='Wrong title'
  elif name=='revision':m['metadata']['revision']+=1
  elif name=='source':m['metadata']['source_id']='0'*64
  elif name=='rights':m['metadata']['rights']='cleared'
  else:m['text_sha256']='0'*64
  guard={'text':'export-original-bytes','id':'export-source-id','title':'export-title','revision':'export-revision','source':'export-source-metadata','rights':'export-source-metadata','hash':'export-source-hash'}[name]
  try:export_identity(b,m,r,hit)
  except R.Refused as e:C.need(str(e)==guard,'export-control-guard');exports.append({'name':name,'guard':guard,'mutated_text_sha256':R.sha(b),'metadata_delta':name})
  else:raise R.Refused('export-mutant-accepted')
 # Evaluate the exact retained old predicate on a same-length, consistently rebound in-memory file.
 old=R.git_bytes('a20a1ffd13ef208cc2205a82d23ebb4b44445c80','tools/evaluation/indexed-frozen-recovery/check.py');tree=ast.parse(old);call=next(n for n in ast.walk(tree) if isinstance(n,ast.Call) and len(n.args)==2 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='export');bad=b'X'+original[1:]
 env={'C':types.SimpleNamespace(need=C.need,RUN=pathlib.Path('/owned-in-memory')),'R':types.SimpleNamespace(hash_file=lambda p:R.sha(bad)),'e':{'export':{'sha256':R.sha(bad)}}};eval(compile(ast.Expression(call),'retained546-export-predicate','eval'),env)
 return {'pidfd':out,'exports':exports,'baseline':d,'old_export_predicate':{'source_sha256':R.sha(old),'wrong_same_length_bytes_sha256':R.sha(bad),'actual_accepted':True,'scope':'Exact old export predicate only, in-memory file/hash adapter; not a new full old checker or audit run.'}}
