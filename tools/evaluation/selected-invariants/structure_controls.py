"""Actual genuine originals, independent HTML/UTF16 and final-format oracles."""
import argparse,base64,hashlib,html,importlib.util,json,pathlib,shutil,sqlite3,subprocess,sys,time,zlib
from html.parser import HTMLParser
ROOT=pathlib.Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools/packs/selected-source'))
from read import InspectionReader
from export_article import export
BASE=pathlib.Path('/home/isa/PocketLore-control/overnight-20261005')
OLD=BASE/'source-reader-prerequisite-review-20261006T0323Z';EXT=BASE/'source-reader-genuine-extended-review-20261006T0403Z'
def sha(b):return hashlib.sha256(b).hexdigest()
def refuse(fn):
 try:fn()
 except (ValueError,AssertionError,InterruptedError,sqlite3.Error):return
 raise AssertionError('Negative unexpectedly succeeded')
def make_inputs(out):
 stage=out/'stage.sqlite';d=sqlite3.connect(stage);d.execute('CREATE TABLE records(sequence INTEGER PRIMARY KEY,member TEXT,member_offset INTEGER,raw_bytes INTEGER,raw_sha256 TEXT,page INTEGER,revision INTEGER,title TEXT,license_json TEXT,metadata_error TEXT,original_zlib BLOB)');d.execute('CREATE TABLE oversized(sequence INTEGER PRIMARY KEY,member TEXT,member_offset INTEGER,raw_bytes INTEGER,raw_sha256 TEXT)');source=[]
 for packet,seq in [(OLD,2956),(OLD,30000),(OLD,100000),(OLD,200000),(EXT,1263712),(EXT,342233),(EXT,5010470)]:
  raw=(packet/f'original-{seq}.json').read_bytes();x=json.loads(raw);source.append({'fixture_sequence':seq,'page':x['identifier'],'revision':x['version']['identifier'],'raw_sha256':sha(raw),'original_file':str(packet/f'original-{seq}.json')});d.execute('INSERT INTO records VALUES(?,?,?,?,?,?,?,?,?,?,?)',(len(source)-1,'frozen-genuine-fixture',seq,len(raw),sha(raw),x['identifier'],x['version']['identifier'],x['name'],json.dumps(x['license']),None,zlib.compress(raw)))
 d.execute('INSERT INTO oversized VALUES(7,?,?,?,?)',('counted-unknown-original',0,17000000,'a'*64));d.commit();d.close()
 rank=out/'ranking.sqlite';d=sqlite3.connect(rank);d.execute('CREATE TABLE priority(id INTEGER PRIMARY KEY,views INTEGER,full INTEGER)');d.executemany('INSERT INTO priority VALUES(?,10,1)',[(x['page'],) for x in source]);d.commit();d.close();return stage,rank,source

def main(out):
 out.mkdir(parents=True)
 for directory,expected in [(OLD,'1d92e3890d276fb9caedfb9e2f65cc83f17bfecbb187a5674bc59924a74663bd'),(EXT,'ef5cdc59fdbe5c04ac50a6444c72bc35b961dea833a16cc46126ce70d9e737a8')]:
  assert sha((directory/'manifest.json').read_bytes())==expected
  for name,identity in json.loads((directory/'manifest.json').read_text()).items():assert sha((directory/name).read_bytes())==identity['sha256']
 stage,rank,sources=make_inputs(out);(out/'frozen-inputs.json').write_text(json.dumps(sources,indent=2));p=ROOT/'tools/packs/selected-source/producer.py';command=['python3',str(p),'--mode','engineering','--stage',str(stage),'--ranking',str(rank),'--ranking-sha256',sha(rank.read_bytes()),'--through','7','--count','7','--seconds','120','--cutoff','1791269954','--out',str(out/'candidate')];start=time.time();r=subprocess.run(command,capture_output=True,timeout=135);(out/'producer.stdout').write_bytes(r.stdout);(out/'producer.stderr').write_bytes(r.stderr);(out/'command.json').write_text(json.dumps({'argv':command,'start':start,'end':time.time(),'exit':r.returncode},indent=2));assert r.returncode==0,r.stderr.decode()
 status=json.loads((out/'candidate/status.json').read_text());assert status['counts']['articles']==7 and status['unresolved_original_identities']==1 and not status['source_admission_established'];assert status['independently_eligible_contexts']==0
 classes=out/'classes';classes.mkdir()
 compile_result=subprocess.run(['javac','-J-Xmx128m','-d',str(classes),str(ROOT/'android/app/src/main/java/org/pocketlore/app/SourceStructureParser.java'),str(ROOT/'tools/evaluation/source-structure/host/StructureParserProbe.java')],capture_output=True);(out/'javac.stdout').write_bytes(compile_result.stdout);(out/'javac.stderr').write_bytes(compile_result.stderr);assert compile_result.returncode==0
 d=sqlite3.connect(out/'candidate/index.sqlite');reader=InspectionReader(out/'candidate/index.sqlite');observations=[]
 for item in sources:
  raw=pathlib.Path(item['original_file']).read_bytes();x=json.loads(raw);page,rev=item['page'],item['revision'];source=x['article_body']['html'];units=source.encode('utf-16-le');collected=bytearray();nodes=[]
  for kind in ('original','html','structure'):
   parts=[]
   for part,a,b,key,size,blob in d.execute('SELECT p.part,p.start,p.end,p.sha,c.bytes,c.z FROM pieces p JOIN capsules c ON c.sha=p.sha WHERE page=? AND revision=? AND p.kind=? ORDER BY part',(page,rev,kind)):
    decoded=zlib.decompress(blob);assert sha(decoded)==key and len(decoded)==size;parts.append(decoded)
   if kind=='original':assert b''.join(parts)==raw
   elif kind=='html':assert b''.join(parts).decode()==source
   else:nodes=[n for part in parts for n in json.loads(part)]
  # Independent original slicing, not producer text/context functions.
  leaves={n[0]:n for n in nodes if n[7] in ('literal','entity') and n[6]}
  texts=d.execute('SELECT node,text FROM texts WHERE page=? AND revision=? ORDER BY node',(page,rev)).fetchall();assert len(texts)==len(leaves) and len({n for n,t in texts})==len(texts)
  for node,text in texts:
   n=leaves[node];literal=units[n[4]*2:n[5]*2].decode('utf-16-le');assert text==(html.unescape(literal) if n[7]=='entity' else literal)
  for node,start,end,digest,root,disposition in d.execute('SELECT node,start,end,fragment_sha,context_root,disposition FROM contexts WHERE page=? AND revision=?',(page,rev)):
   assert sha(units[2*start:2*end].decode('utf-16-le').encode())==digest;assert nodes[node-1][4:6]==[start,end];assert nodes[root-1][4]<=start<=end<=nodes[root-1][5];assert 'review' in disposition or disposition.startswith('inspection-only:')
  html_file=out/('html-'+str(item['fixture_sequence'])+'.html');html_file.write_text(source)
  java=subprocess.run(['java','-Xmx128m','-cp',str(classes),'org.pocketlore.app.StructureParserProbe',str(html_file)],capture_output=True,timeout=15);(out/('java-'+str(item['fixture_sequence'])+'.stdout')).write_bytes(java.stdout);(out/('java-'+str(item['fixture_sequence'])+'.stderr')).write_bytes(java.stderr);assert java.returncode==0
  lines=java.stdout.decode().splitlines();assert len(lines)==len(nodes)
  for line,node in zip(lines,nodes):
   n,parent,tag,attrs,a,b,text,kind=node;attributes=json.loads(attrs);attrtext=''.join(k+'='+('<null>' if v is None else v)+'\n' for k,v in sorted(attributes.items()));encode=lambda value:base64.b64encode(value.encode()).decode();expected='\t'.join([str(n),str(parent),encode(tag),encode(attrtext),str(a),str(b),encode(text),kind]);assert line==expected
  metadata=json.loads(d.execute('SELECT metadata FROM articles WHERE page=?',(page,)).fetchone()[0]);assert metadata['license']==x['license'] and metadata['version']==x['version'] and metadata['date_modified']==x['date_modified']
  assert reader.nodes(page,rev,1,min(128,len(nodes)))==nodes[:128]
  observations.append({'page':page,'revision':rev,'source':item,'nodes':len(nodes),'canonical_text_rows':len(texts),'source_utf16':len(units)//2,'license':x['license']})
 # Independent pre-tuning fragments: exact math operand context and attributed quote ranges.
 for entry in json.loads((EXT/'oracles.json').read_text())['records']:
  seq=entry['sequence'];item=next((i for i in sources if i['fixture_sequence']==seq),None)
  if not item:continue
  page,rev=item['page'],item['revision'];units=json.loads(pathlib.Path(item['original_file']).read_bytes())['article_body']['html'].encode('utf-16-le')
  def fragments(v):
   if isinstance(v,dict):
    if 'original_start16' in v:
     a,b=v['original_start16'],v['original_end16'];assert sha(units[a*2:b*2].decode('utf-16-le').encode())==v['utf8_fragment_sha256']
     if b-a<=8192:assert reader.html_window(page,rev,a,b).encode('utf-16-le')==units[a*2:b*2]
    for child in v.values():fragments(child)
   elif isinstance(v,list):
    for child in v:fragments(child)
  fragments(entry)
  if seq==1263712:
   a,b=entry['math_element']['original_start16'],entry['math_element']['original_end16'];node=d.execute('SELECT node FROM contexts WHERE page=? AND start=? AND end=?',(page,a,b)).fetchone()[0];context=reader.context(page,rev,node);assert context['root'][4]<=entry['containing_reaction_context']['original_start16'] and context['root'][5]>=entry['containing_reaction_context']['original_end16'];assert context['root'][2]=='dd'
  if seq==342233:
   a,b=entry['blockquote']['original_start16'],entry['blockquote']['original_end16'];node=d.execute('SELECT node FROM contexts WHERE page=? AND start=? AND end=?',(page,a,b)).fetchone()[0];context=reader.context(page,rev,node);assert context['root'][4]<=entry['attribution_and_callout']['original_start16'] and context['root'][5]>=b
 hits=reader.search('water');assert hits
 for hit in hits:
  context=reader.context(hit[1],hit[2],hit[3]);assert context['matched_node']==hit[3] and context['root'][0]<=hit[3]
 refuse(lambda:reader.nodes(1,1,1,129));reader.close();cancelled=InspectionReader(out/'candidate/index.sqlite',lambda:True);refuse(lambda:cancelled.search('water'));cancelled.close()
 sample=sources[0];index=out/'candidate/index.sqlite';index_sha=sha(index.read_bytes());adapt=export(index,index_sha,sample['page'],sample['revision'],out/'adapter');assert adapt['manifest']['articles']==1 and adapt['manifest']['db_bytes']<=67108864
 refuse(lambda:export(index,'f'*64,sample['page'],sample['revision'],out/'bad-hash'))
 refuse(lambda:export(index,index_sha,sample['page'],sample['revision']+1,out/'bad-revision'))
 refuse(lambda:export(index,index_sha,sample['page'],sample['revision'],out/'cancel-export',lambda:True))
 # Real cancellation inside packing, after verified-original and packaging directory exist.
 target=out/'cancel-during-pack'
 refuse(lambda:export(index,index_sha,sample['page'],sample['revision'],target,lambda:(target/'inspection-pack/index.sqlite').exists()))
 assert (target/'verified-original.json').exists() and not (target/'adapter.json').exists()
 # Actual fixture-file replacement after prehash/snapshot must not produce a success receipt.
 mutable=out/'mutable.sqlite';shutil.copyfile(index,mutable);target=out/'mutation-during-pack';replaced=[False]
 def mutate():
  if (target/'inspection-pack/index.sqlite').exists() and not replaced[0]:
   replacement=out/'replacement.sqlite';shutil.copyfile(index,replacement);replacement.replace(mutable);replaced[0]=True
  return False
 refuse(lambda:export(mutable,index_sha,sample['page'],sample['revision'],target,mutate))
 assert replaced[0] and not (target/'adapter.json').exists()
 d.close()
 # Corrupted format, missing capsule and changed metadata are separate real fixture files.
 negatives=[]
 for name,sql in [('format',"UPDATE format SET name='unsupported'"),('metadata',"UPDATE articles SET metadata=json_set(metadata,'$.name','Changed')"),('capsule',"DELETE FROM capsules WHERE sha IN (SELECT sha FROM pieces WHERE kind='original' LIMIT 1)")]:
  bad=out/(name+'.sqlite');shutil.copyfile(index,bad);db=sqlite3.connect(bad);db.execute(sql);db.commit();db.close()
  if name=='format':refuse(lambda:InspectionReader(bad))
  else:
   db=sqlite3.connect(bad);page,rev=db.execute('SELECT page,revision FROM articles ORDER BY page LIMIT 1').fetchone();db.close()
   if name=='capsule':
    db=sqlite3.connect(bad);page,rev=db.execute('SELECT page,revision FROM pieces WHERE sha NOT IN (SELECT sha FROM capsules) LIMIT 1').fetchone();db.close()
   refuse(lambda:export(bad,sha(bad.read_bytes()),page,rev,out/('bad-'+name)))
  negatives.append(name)
 report={'pass':True,'producer_sha256':sha(p.read_bytes()),'sources':observations,'status':status,'adapter':adapt,'negative_controls':negatives+['stale-index','stale-revision','cancellation','node-bound','search-hit-context','packaging-cancellation','index-replacement'],'node_text_not_duplicated':True,'actual_java_parser_sources':7,'external_kernel_qualified':False,'android_execution':False,'actual_fixture_count':7,'corpus_eligible_count':0};(out/'result.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));return report
if __name__=='__main__':main(pathlib.Path(sys.argv[1]))
