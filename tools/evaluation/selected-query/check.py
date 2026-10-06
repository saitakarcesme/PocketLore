"""Frozen public query and original-source engineering controls, not admission."""
import copy,hashlib,importlib.util,json,pathlib,resource,shutil,sqlite3,subprocess,sys,time,traceback,zlib
ROOT=pathlib.Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools/packs/selected-source'));sys.path.insert(0,str(pathlib.Path(__file__).parent))
from read import InspectionReader
from observe import load,Guard,PACKET
from export_article import export
BASE=pathlib.Path('/home/isa/PocketLore-control/overnight-20261005')
def sha(b):return hashlib.sha256(b).hexdigest()
def refused(fn):
 try:fn()
 except (ValueError,KeyError,InterruptedError,TimeoutError,sqlite3.Error,UnicodeError) as e:return {'rejected':True,'error':type(e).__name__+': '+str(e)}
 raise AssertionError('Required negative accepted')
def binding(raw):
 x=json.loads(raw);return {'raw_sha256':sha(raw),'html_sha256':sha(x['article_body']['html'].encode()),'metadata':{k:x[k] for k in ('identifier','version','name','url','license','date_modified')}}
def main(out):
 out.mkdir(parents=True);started=time.time();result={'status':'FAIL','positives':[],'negatives':{},'source_admission_established':False,'android_execution':False}
 try:
  pins={'source-v3-cross-inline-prerequisites-20261006T0600Z':'723abffde5b3c0a3b5ddd79b5213e46da0858d1125df553b46506f8635cb82f1','source-context-independent-prerequisites-20261006T0606Z':'0d9c8a7b8ef1efeb83812ff19922ffbd5ca063bbd3fafbcab4aae6e6479af701','source-context-attribution-scope-erratum-20261006T0610Z':'6302fd7ae424fb6933301cfbff866c8682b7e6bcd318ce1c11d3157b36fd8094'}
  for folder,pin in pins.items():
   directory=BASE/folder;assert sha((directory/'manifest.json').read_bytes())==pin;entries=json.loads((directory/'manifest.json').read_text())['files'];entries=entries if isinstance(entries,list) else [dict(v,path=k) for k,v in entries.items()]
   for entry in entries:assert sha((directory/entry['path']).read_bytes())==entry['sha256']
  result['input_manifests']=pins;policy=json.loads((ROOT/'docs/evidence/selected-source-query/frozen-policy.json').read_text());p=load('producer',ROOT/'tools/packs/selected-source/producer.py');d=sqlite3.connect(out/'index.sqlite');d.executescript(p.SCHEMA);guard=Guard();originals={}
  items=[(PACKET/(f['id']+'.schema-corrected.original.json')).read_bytes() for f in policy['fixtures']]
  for folder,sequences in [('source-reader-prerequisite-review-20261006T0323Z',[2956,30000,100000,200000]),('source-reader-genuine-extended-review-20261006T0403Z',[1263712,342233,5010470])]:items += [(BASE/folder/('original-'+str(seq)+'.json')).read_bytes() for seq in sequences]
  # Supplemental authored controls, never factual articles or corpus counts.
  supplement=[('separate-blocks','<div>alpha</div><div>omega</div>'),('direct-body','Plain body evidence marker'),('pre-block','<pre>Verbatim code evidence marker</pre>'),('split-word','<p>micro<b>scope</b> &amp; lens</p>'),('unsafe-gap','<p>sun<script>evil</script>rise</p>'),('long-inline','<p>'+('padding '*4090)+'silver <b>blue</b> <i>green</i> amber'+(' trailing'*4090)+'</p>'),('empty-block','alpha<div></div>omega')]
  for i,(name,body) in enumerate(supplement):
   x=json.loads(items[0]);x['identifier']=800+i;x['version']['identifier']=9800+i;x['name']=name;x['url']='https://example.invalid/'+name;x['article_body']['html']='<html about="https://example.invalid/revision/'+str(9800+i)+'"><head><meta property="mw:pageId" content="'+str(800+i)+'"></head><body>'+body+'</body></html>';items.append(json.dumps(x).encode())
  (out/'originals').mkdir()
  for seq,raw in enumerate(items):
   x=json.loads(raw);page,rev=x['identifier'],x['version']['identifier'];row=(seq,page,rev,'frozen-public',seq,len(raw),sha(raw),json.dumps(x['license']),x['name'],None);p.transform(d,row,raw,guard);d.execute('INSERT INTO latest VALUES(?,?,?,?,0)',(page,rev,seq,sha(raw)));originals[page]=raw;(out/'originals'/('original-'+str(page)+'.json')).write_bytes(raw)
  d.execute("INSERT INTO search(search) VALUES('rebuild')");d.execute("INSERT INTO search(search) VALUES('integrity-check')");d.commit()
  result['storage']={'components':dict(d.execute('SELECT name,sum(pgsize) FROM dbstat GROUP BY name')),'canonical_text_bytes':d.execute('SELECT sum(length(CAST(text AS BLOB))) FROM texts').fetchone()[0],'query_units':d.execute('SELECT count(*) FROM query_units').fetchone()[0],'query_unit_columns':[r[1] for r in d.execute('PRAGMA table_info(query_units)')],'originals':len(items),'authored':11,'genuine':7};assert 'text' not in result['storage']['query_unit_columns'];d.close()
  index=out/'index.sqlite';pin=sha(index.read_bytes());r=InspectionReader(index,expected_index_sha256=pin);timings=[]
  queries=[(f['page'],q) for f in policy['fixtures'] for q in f['queries']]+[(801,'evidence marker'),(802,'code evidence'),(803,'microscope lens'),(805,'"silver blue green amber"')]
  for page,q in queries:
   start=time.perf_counter();hits=r.search_hits(q);timings.append(time.perf_counter()-start);hit=next(h for h in hits if h['page']==page);opened=r.open_hit(hit,binding(originals[page]));x=json.loads(originals[page]);source=x['article_body']['html'].encode('utf-16-le');a,b=opened['start16'],opened['end16'];windows=list(r.source_windows(page,hit['revision'],a,b));rebuilt=''.join(w['original_html'] for w in windows);assert rebuilt.encode('utf-16-le')==source[a*2:b*2] and not opened['generation_eligible']
   if page==701:assert 'If the road is closed' in rebuilt and 'only when daylight is available' in rebuilt
   if page==702:assert 'inhibits' in rebuilt and 'only under the stated conditions' in rebuilt
   if page==703:assert opened['kind']=='article-metadata' and hit['kind']=='metadata-title'
   if page==704:assert 'otherwise wait' in rebuilt
   result['positives'].append({'query':q,'hit':hit,'opened':opened,'window_hashes':[w['sha256'] for w in windows],'exact_original_sha256':sha(rebuilt.encode())})
  for q in policy['additional_negative_queries']+['"alphaomega"','alpha omega']:
   assert not r.search_hits(q);result['negatives']['absent-'+q]={'rejected':True,'meaning':'No matching coherent query unit'}
  sunrise=r.search_hits('sunrise');assert not any(h['page']==804 for h in sunrise);result['negatives']['unsafe-gap-page804']={'rejected':True,'other_source_hits':sunrise,'scope':'The authored script-gap page804 must not match; genuine Salar sunrise matches remain valid retrieval'}
  oracles=json.loads((BASE/'source-context-independent-prerequisites-20261006T0606Z/oracles.json').read_text());genuine=[]
  for oracle in oracles:
   page,rev=oracle['metadata']['identifier'],oracle['metadata']['version']['identifier'];assert binding(originals[page])=={k:oracle[k] for k in ('raw_sha256','html_sha256','metadata')};a,b=oracle['span_start16'],oracle['span_end16'];literal=''.join(w['original_html'] for w in r.source_windows(page,rev,a,b));assert literal==oracle['exact_original_fragment']
   matches=[]
   if oracle['id']!='disambiguation-negative':
    for node, in r.db.execute('SELECT node FROM contexts WHERE page=? AND revision=? AND start<? AND end>?',(page,rev,b,a)):
     c=r.context(page,rev,node)
     if c['root'][4]<=a and c['root'][5]>=b:matches.append((c['root'][5]-c['root'][4],node))
    assert matches;opened=r.verified_context(page,rev,min(matches)[1],oracle);assert not opened['generation_eligible']
   genuine.append({'id':oracle['id'],'fragment_sha256':sha(literal.encode()),'generation_eligible':False,'complete_context':bool(matches)})
  result['genuine_oracles']=genuine
  genuine_queries=[('table-elevation','Elevation'),('math-reaction','"reduced acceptor"'),('attributed-conditional-quotation','"full guarantee"'),('long-section-heading','Formation geology climate'),('disambiguation-negative','Nibelungs')]
  result['genuine_retrieval']=[]
  for oid,q in genuine_queries:
   oracle=next(o for o in oracles if o['id']==oid);page=oracle['metadata']['identifier'];hits=r.search_hits(q);opened=[]
   for hit in hits:
    view=r.open_hit(hit,binding(originals[hit['page']]))
    if hit['page']==page and view['start16']<=oracle['span_start16'] and view['end16']>=oracle['span_end16']:opened.append(view)
   assert opened,'Missing complete genuine retrieval context: '+oid
   result['genuine_retrieval'].append({'id':oid,'query':q,'all_hits':hits,'covering_inspections':opened,'scope':'Public development retrieval; no factual or rights promotion'})
  first=result['positives'][0]['hit'];bad=copy.deepcopy(first);bad['revision']+=1;result['negatives']['changed-hit']=refused(lambda:r.open_hit(bad,binding(originals[701])))
  result['negatives']['missing-context']=refused(lambda:r.verified_context(701,9001,999999,binding(originals[701])))
  emoji=json.loads(originals[704])['article_body']['html'];start16=len(emoji[:emoji.index('🙂')].encode('utf-16-le'))//2
  assert ''.join(w['original_html'] for w in r.source_windows(704,9004,start16,start16+2))=='🙂';result['negatives']['split-surrogate']=refused(lambda:list(r.source_windows(704,9004,start16+1,start16+2)))
  result['negatives']['query-bound']=refused(lambda:r.search_hits('a'*257));result['negatives']['malformed-query']=refused(lambda:r.search_hits('"'))
  r.close();cancel=InspectionReader(index,lambda:True);result['negatives']['cancelled-query']=refused(lambda:cancel.search_hits('water'));cancel.close()
  for label,sql in [('unsupported-query-contract',"UPDATE query_contract SET name='unreviewed'"),('missing-query-table','DROP TABLE query_units')]:
   path=out/(label+'.sqlite');shutil.copyfile(index,path);c=sqlite3.connect(path);c.execute(sql);c.commit();c.close()
   def attempt():
    rr=InspectionReader(path,expected_index_sha256=sha(path.read_bytes()))
    try:rr.search_hits('York')
    finally:rr.close()
   result['negatives'][label]=refused(attempt)
  result['negatives']['corrupt-index']=refused(lambda:InspectionReader(index,expected_index_sha256='0'*64))
  reopened=InspectionReader(index,expected_index_sha256=pin);assert reopened.search_hits('"New York"')[0]['page']==701;reopened.close()
  receipt=export(index,pin,701,9001,out/'export');assert not receipt['source_admission_established'];result['export']=receipt
  result.update(status='PASS',index_sha256=pin,index_bytes=index.stat().st_size,query_seconds=timings,max_query_seconds=max(timings),source={str(path.relative_to(ROOT)):sha(path.read_bytes()) for path in [ROOT/'tools/packs/selected-source/producer.py',ROOT/'tools/packs/selected-source/read.py',pathlib.Path(__file__)]})
 except BaseException as e:result['error']=type(e).__name__+': '+str(e);result['traceback']=traceback.format_exc()
 finally:
  result['elapsed_seconds']=time.time()-started;result['maxrss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024;(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
 return 0 if result['status']=='PASS' else 1
if __name__=='__main__':sys.exit(main(pathlib.Path(sys.argv[1])))
