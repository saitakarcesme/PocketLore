#!/usr/bin/env python3
"""Explicit bounded fixture/prefix commands; the offline checker never ingests."""
import base64,copy,json,os,pathlib,resource,shutil,signal,sqlite3,sys,time,traceback
import check,fixtures
A=check.A;ROOT=check.ROOT;BASE=ROOT/'downloads/current-xml-541'
ARCHIVE='/home/isa/PocketLore-control/continue-20261006/current-source-20261001/enwiki-20261001-pages-articles-multistream.xml.bz2.partial'
IDENTITY='3fd026adce2a54ec7a2583c9047bcd8e632e67bad62b0b46ea4b685657d18f31'
CANCEL=False
def cancel(signum,frame):
 global CANCEL
 CANCEL=True
for sig in [signal.SIGTERM,signal.SIGINT]:signal.signal(sig,cancel)
def available():
 raw=pathlib.Path('/proc/meminfo').read_text();check.need(int(next(x.split()[1] for x in raw.splitlines() if x.startswith('MemAvailable:')))*1024>=11*1024**3,'host-available');return raw
def synthetic():
 out=BASE/'synthetic-v4';out.mkdir(exist_ok=False);before=check.freeze();A.atomic(out/'freeze.json',before);oracle=fixtures.create(out/'inputs');results=[];raw={};source=A.filehash(out/'inputs/valid.bz2')
 def run(name,fixture='valid',expected=None,**kwargs):
  p=out/'inputs'/f'{fixture}.bz2';v=A.version(p);r=A.build(p,out/name,A.filehash(p),**kwargs);check.need(v==A.version(p),'fixture-mutated');raw[name]=r
  if expected:check.need(r['status']=='FAILED' and any(expected in e for e in r['errors']),name+' expected '+expected)
  else:check.rawcheck(r,A.filehash(p))
  results.append({'name':name,'expected':expected or 'success','actual':r['errors'] or r['status']});return r
 r=run('positive');reader=A.Reader(out/'positive',source);ident=source+':1:11';record=reader.inspect(ident)
 check.need(record['text']==oracle['text'] and record['text_sha256']==oracle['text_utf8_sha256'] and record['metadata']['text_xml_range']==oracle['valid_text_xml_range'],'independent-text')
 check.need(r['records']==oracle['records'] and r['pages']==oracle['pages'] and r['ledger']==oracle['ledger'],'independent-counts')
 for query in oracle['queries']:
  hits=reader.search(query);check.need(bool(hits)==(query!='absentliteral'),'query-oracle')
  for h in hits:reader.resolve(h)
 emoji=reader.search('😀')[0];check.need([emoji['start_utf16'],emoji['end_utf16']]==oracle['emoji_utf16_range'],'independent-UTF16')
 search_query='otherwise no.';flow_hits=reader.search(search_query)
 exported=reader.export(ident,out/'prefix-export');check.need((out/'prefix-export/original.wikitext').read_bytes()==oracle['text'].encode(),'export-bytes');reader.close()
 flow={'query':search_query,'hits':flow_hits,'inspection':{k:v for k,v in record.items() if k!='text'},'export':exported};check.validate_flow(r,flow,out/'positive')
 flow_controls=[]
 for name,guard,edit in [('flow-export','export-binding',lambda m:m['export'].update(sha256='0'*64)),('flow-inspection','inspection-binding',lambda m:m['inspection'].update(title='Changed')),('flow-hit','search-binding',lambda m:m['hits'][0].update(start_utf16=0))]:
  check.validate_flow(r,flow,out/'positive');m=copy.deepcopy(flow);edit(m)
  try:check.validate_flow(r,m,out/'positive');raise AssertionError('accepted '+name)
  except ValueError as e:check.need(str(e)==guard,'flow-guard');flow_controls.append({'name':name,'expected_guard':guard,'actual_guard':str(e),'mutated':m})
 other=copy.deepcopy(r);other['output_sha256']='0'*64
 try:check.validate_flow(other,flow,out/'positive');raise AssertionError('accepted receipt substitution')
 except ValueError as e:check.need(str(e)=='capsule-receipt','capsule-guard');flow_controls.append({'name':'receipt-substitution','expected_guard':'capsule-receipt','actual_guard':str(e),'mutated_receipt':other})
 rr=A.Reader(out/'positive',source);check.need(rr.inspect(ident)['text']==oracle['text'],'reopen');rr.close();results.extend([{'name':x,'actual':'PASS'} for x in ['exact-original','UTF16','query-source','export-bytes','reopen']])
 run('split','multistream',limits={'chunk':1});run('missing-and-model')
 for name,expected in [('nested-id','unsupported-page-layout'),('duplicate-contributor','duplicate-contributor-field'),('duplicate-redirect','duplicate-redirect'),('conflict','revision-conflict'),('doctype','doctype'),('malformed','mismatched tag'),('truncated','truncated-bzip'),('trailing-truncated-member','junk after document element'),('namespace','xml-namespace'),('oversized','field-bound'),('deep','xml-depth'),('missing-id','numeric-id')]:run(name,name,expected)
 run('bomb','bomb','prefix-not-authorized',limits={'decoded':32768});run('page-bound',expected='page-bound',limits={'page':100});run('cancel',expected='cancelled',cancel=lambda:True);
 calls=[0]
 def midcancel():
  calls[0]+=1;return calls[0]>95
 run('mid-cancel',expected='cancelled',cancel=midcancel);
 run('deadline',expected='deadline',limits={'seconds':0.000001});run('partial',provisional=True,limits={'pages':1})
 check.need(not (out/'conflict/index.sqlite').exists() and A.filehash(out/'positive/index.sqlite')==r['output_sha256'],'rollback')
 try:A.Reader(out/'positive','0'*64);raise AssertionError('source collision accepted')
 except A.Refused as e:check.need(str(e)=='reader-source','source collision guard')
 results.append({'name':'source-collision-rollback','actual':'PASS'})
 mutations=[]
 def mutant(name,guard,edit):
  check.rawcheck(r,source);m=copy.deepcopy(r);edit(m)
  try:check.rawcheck(m,source);raise AssertionError('accepted '+name)
  except ValueError as e:check.need(str(e)==guard,name+' wrong guard '+str(e));actual=str(e)
  A.atomic(out/(name+'.mutation.json'),m);mutations.append({'name':name,'expected_guard':guard,'actual_guard':actual,'base_sha256':A.sha(A.canonical(r)),'mutated_sha256':A.sha(A.canonical(m))})
 mutant('wrong-input','archive-input',lambda m:m.update(source_id='0'*64));mutant('wrong-version','archive-version',lambda m:m['fd_after'].update(inode=0));mutant('wrong-pid','pid',lambda m:m['samples'][1].update(pid=0));mutant('wrong-offset','byte-offset',lambda m:m.update(xml_parsed_bytes=m['decoded_bytes']+1));mutant('wrong-format','source-format',lambda m:m.update(source_format='HTML'));mutant('promotion','license-promotion',lambda m:m.update(admission=True));mutant('wrong-count','record-count',lambda m:m.update(records=999));mutant('wrong-phase','phase',lambda m:m['samples'][1].update(phase='fake'))
 def ticks(m):
  s=m['samples'][1];a,b=s['stat'].rsplit(')',1);v=b.split();v[19]=str(int(v[19])+1);s['stat']=a+') '+' '.join(v)
 mutant('wrong-startticks','startticks',ticks)
 # Database semantic corruptions rebind the outer database hash, not the original source oracle.
 for name,sql,guard in [('schema','PRAGMA user_version=0','schema'),('rights',"UPDATE metadata SET value='true' WHERE key='admission'",'license-promotion'),('count',"UPDATE metadata SET value='99' WHERE key='records'",'record-count'),('format',"UPDATE metadata SET value='\"html\"' WHERE key='source_format'",'format')]:
  target=out/('db-'+name);shutil.copytree(out/'positive',target);db=sqlite3.connect(target/'index.sqlite');db.execute(sql);db.commit();db.close();m=copy.deepcopy(r);m['output_sha256']=A.filehash(target/'index.sqlite');A.atomic(target/'receipt.json',m)
  try:A.Reader(target,source);raise AssertionError('accepted db '+name)
  except A.Refused as e:check.need(str(e)==guard,'db guard');results.append({'name':'database-'+name,'actual_guard':str(e)})
 bad=copy.deepcopy(emoji);bad['start_utf16']+=1;rd=A.Reader(out/'positive',source)
 try:rd.resolve(bad);raise AssertionError('accepted split surrogate')
 except A.Refused as e:check.need(str(e)=='hit-surrogate','range guard');results.append({'name':'surrogate-boundary','actual_guard':str(e)})
 finally:rd.close()
 check.need(check.freeze()==before,'source-mutated');summary={'status':'PASS','directory':str(out.relative_to(ROOT)),'sources_before':before,'sources_after':check.freeze(),'controls':results,'mutations':mutations,'flow':flow,'flow_controls':flow_controls,'raw_receipts':raw,'oracle':oracle,'storage_new_bytes':sum(p.stat().st_size for p in out.rglob('*') if p.is_file())}
 check.coverage(summary);summary['coverage_controls']=[]
 for name,key,mode in [('omitted-control','controls','omit'),('duplicate-control','controls','duplicate'),('omitted-mutations','mutations','empty'),('omitted-flow','flow_controls','empty')]:
  check.coverage(summary);m=copy.deepcopy(summary)
  if mode=='omit':m[key]=m[key][1:]
  elif mode=='duplicate':m[key].append(m[key][0])
  else:m[key]=[]
  try:check.coverage(m);raise AssertionError('coverage mutation accepted')
  except ValueError as e:check.need(str(e)=='coverage-'+key,'coverage-guard');summary['coverage_controls'].append({'name':name,'guard':str(e)})
 check.need(summary['storage_new_bytes']<=64*1024**2,'synthetic-output-budget');A.atomic(BASE/'synthetic.json',summary)
 print(json.dumps({'status':'PASS','controls':len(results),'mutations':len(mutations),'bytes':summary['storage_new_bytes']}))
def prefix():
 before=check.freeze();s=json.loads((BASE/'synthetic.json').read_text());check.need(s['status']=='PASS' and s['sources_before']==before,'synthetic-before-prefix');check.need(json.loads((BASE/'build.json').read_text())['exit']==0,'build-before-prefix')
 preflight={'executable':{'path':sys.executable,'version':A.version(sys.executable),'sha256':A.filehash(sys.executable)},'source_versions':{p:A.version(ROOT/p) for p in check.INPUTS},'sources':before,'meminfo':available(),'archive_stat':A.version(ARCHIVE),'expected_sha256_from_acquisition':IDENTITY,'hash_scope':'No full archive hash: only bounded compressed read prefix','limits':A.LIMITS,'task':'541-current-wikipedia-xml-source-adapter','pid':os.getpid(),'start_ns':time.monotonic_ns()}
 with open(BASE/'prefix-attempt.json','x') as f:json.dump(preflight,f)
 r=A.build(ARCHIVE,BASE/'prefix',IDENTITY,provisional=True,expected={'size':26899580121,'inode':4272766,'device':57},cancel=lambda:CANCEL)
 A.atomic(BASE/'prefix-runtime-after.json',{'executable':{'path':sys.executable,'version':A.version(sys.executable),'sha256':A.filehash(sys.executable)},'source_versions':{p:A.version(ROOT/p) for p in check.INPUTS}});A.atomic(BASE/'prefix-sources-after.json',check.freeze());check.need(check.freeze()==before,'post-prefix-source');check.rawcheck(r,IDENTITY);check.need(r['status']=='PROVISIONAL_PREFIX','prefix-state')
 rd=A.Reader(BASE/'prefix',IDENTITY)
 try:
  ident=rd.db.execute("SELECT stable_id FROM records WHERE disposition='inspection-only' ORDER BY page,revision LIMIT 1").fetchone()[0];ins=rd.inspect(ident);query=ins['text'][:min(32,len(ins['text']))];hits=rd.search(query);[rd.resolve(h) for h in hits];ex=rd.export(ident,BASE/'prefix-export');flow={'query_rule':'first 32 Unicode scalars of first page/revision original; identity plumbing only, not answer evaluation','query':query,'hits':hits,'inspection':{k:v for k,v in ins.items() if k!='text'},'export':ex};A.atomic(BASE/'prefix-flow.json',flow)
 finally:rd.close()
 print(json.dumps({'status':r['status'],'pages':r['pages'],'records':r['records'],'compressed':r['compressed_read_bytes'],'decoded':r['decoded_bytes'],'stop':r['stop_reason']}))
def packet():
 before=json.loads((BASE/'synthetic.json').read_text())['sources_before'];raw={}
 for p in BASE.rglob('*'):
  if p.is_file() and p.suffix not in ['.sqlite','.bz2'] and p.name not in ['review.json']:
   check.need(p.stat().st_size<=8*1024**2,'raw-bound');raw[str(p.relative_to(BASE))]=check.envelope(p)
 p={'task':'541-current-wikipedia-xml-source-adapter','sources_before':before,'sources_after':check.freeze(),'source_content':{n:check.envelope(ROOT/n) for n in check.INPUTS},'raw':raw,'build':json.loads((BASE/'build.json').read_text()),'prefix_path':str((BASE/'prefix').relative_to(ROOT)),'prefix_flow':json.loads((BASE/'prefix-flow.json').read_text()) if (BASE/'prefix-flow.json').exists() else None,'status':'UNVALIDATED','limitations':['Provisional host-only original wikitext; no renderedHTML, Android runtime, rights/census/latest/full profile or rival qualification.']}
 try:check.validate_packet(p);p['status']='PASS_HOST_PROVISIONAL_ONLY'
 except Exception as e:p['status']='FAIL';p['error']=type(e).__name__+': '+str(e)
 A.atomic(ROOT/'docs/evidence/current-xml-source-review.json',p);print(p['status']);return int(p['status']=='FAIL')
if __name__=='__main__':
 try:
  available();result={'synthetic':synthetic,'prefix':prefix,'packet':packet}[sys.argv[1]]();sys.exit(result or 0)
 except Exception:
  error=traceback.format_exc();path=BASE/('error-'+str(time.time_ns())+'.txt');path.write_text(error);print(error,file=sys.stderr);sys.exit(1)
