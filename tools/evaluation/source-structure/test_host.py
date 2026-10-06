"""Frozen original expectations and independent range/hash oracles; no Android claims."""
import base64,hashlib,html,importlib.util,json,pathlib,resource,sqlite3,sys,tempfile,time,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('producer',ROOT/'tools/packs/source-structure/produce.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
PACKET=pathlib.Path('/home/isa/PocketLore-control/overnight-20261005/source-reader-prerequisite-review-20261006T0323Z')
def digest(b):return hashlib.sha256(b).hexdigest()
def cut(s,a,b):return s.encode('utf-16-le')[a*2:b*2].decode('utf-16-le')
def verify(folder):
 m=json.loads((folder/'manifest.json').read_text());assert m['format']=='pocketlore-structured-source-v1' and m['source_admission_established'] is False
 assert digest((folder/'index.sqlite').read_bytes())==m['db_sha256']
 db=sqlite3.connect(folder/'index.sqlite');assert db.execute('pragma user_version').fetchone()[0]==523
 assert db.execute("select sql from sqlite_master where name='search'").fetchone()[0]=='CREATE VIRTUAL TABLE search USING fts4(text,content=nodes,tokenize=unicode61)'
 for page,title,meta,rawsha,htmlsha,size,units in db.execute('select * from articles'):
  raw=b''.join(b for b, in db.execute('select bytes from originals where article=? order by part',(page,)));assert digest(raw)==rawsha and len(raw)==size
  d=json.loads(raw);source=d['article_body']['html'];assert digest(source.encode())==htmlsha and len(source.encode('utf-16-le'))//2==units
  assert json.loads(meta)['license']==d['license'];assert json.loads(meta)['version']==d['version']
  merged=''.join(t for t, in db.execute('select text from html_chunks where article=? order by start',(page,)));assert merged==source
  for n,parent,tag,attrs,a,b,text,kind in db.execute('select id,parent,tag,attrs,start,end,text,kind from nodes where article=? order by id',(page,)):
   exact=cut(source,a,b)
   if kind=='literal':assert text==exact
   if kind=='entity':assert text==html.unescape(exact)
   if kind=='omitted-unsafe':assert text==''
   if parent:
    pa,pb=db.execute('select start,end from nodes where id=?',(parent,)).fetchone();assert pa<=a<=b<=pb
 return db,m
checks=[]
def test(name,fn):fn();checks.append(name)
def rejects(fn):
 try:fn()
 except (ValueError,AssertionError,UnicodeError):return
 raise AssertionError('Corruption was accepted')
def main(out):
 out.mkdir();start=time.monotonic();manifest=json.loads((PACKET/'manifest.json').read_text())
 for name,h in manifest.items():assert digest((PACKET/name).read_bytes())==h['sha256']
 inputs=[(n,PACKET/f'original-{n}.json') for n in (2956,30000,100000,200000)];m=p.build(inputs,out/'pack');db,m=verify(out/'pack');checks.append('four independent original JSON/HTML/license/revision and every UTF16 literal/entity mapping')
 for e in json.loads((PACKET/'independent-expectations.json').read_text()):
  raw=(PACKET/f"original-{e['sequence']}.json").read_bytes();d=json.loads(raw);source=d['article_body']['html'];a,b=e['original_start16'],e['original_end16'];assert digest(cut(source,a,b).encode())==e['fragment_sha256']
  rows=db.execute('select tag,attrs,start,end,text from nodes where article=? and start>=? and end<=? order by id',(d['identifier'],a,b)).fetchall();text=''.join(r[4] for r in rows)
  if 'header_text' in e:assert e['header_text'] in text and e['expected_cell_visible_text_or_prefix'] in text;assert any(r[0]=='th' for r in rows) and any(r[0]=='td' for r in rows)
  if 'expected_visible_text' in e:assert e['expected_visible_text'] in text
  if 'reference_id' in e:
   assert any(json.loads(r[1]).get('id')==e['reference_id'] for r in rows)
   attrs=[json.loads(a) for a, in db.execute('select attrs from nodes where article=?',(d['identifier'],))]
   assert any(a.get('id')==e['expected_callout_id'] for a in attrs)
   assert any(a.get('href','').endswith('#'+e['reference_id']) for a in attrs)
   assert any(a.get('href','').endswith('#'+e['expected_callout_id']) for a in attrs)
  if 'header_text' in e:
   structural=db.execute("select id,parent,tag,start,end from nodes where article=? and start>=? and end<=? and tag in ('th','td') order by id",(d['identifier'],a,b)).fetchall()
   assert len(structural)>=2 and structural[0][1]==structural[1][1]
   assert db.execute('select tag from nodes where id=?',(structural[0][1],)).fetchone()==('tr',)
  checks.append('independent '+str(e['sequence'])+' '+e['expectation_type']+' '+str(a))
 assert db.execute("select count(*) from search where search match 'Elevation'").fetchone()[0]>0;checks.append('host FTS4 unicode61 actual query (not Android proof)')
 # Execute actual pure Java parser against independently frozen originals and Python tree.
 classes=out/'classes';classes.mkdir();subprocess.run(['javac','-J-Xmx128m','-d',str(classes),str(ROOT/'android/app/src/main/java/org/pocketlore/app/SourceStructureParser.java'),str(ROOT/'tools/evaluation/source-structure/host/StructureParserProbe.java')],check=True)
 for seq,_ in inputs:
  source=(PACKET/f'html-{seq}.html').read_text();actual=subprocess.check_output(['java','-Xmx128m','-cp',str(classes),'org.pocketlore.app.StructureParserProbe',str(PACKET/f'html-{seq}.html')],timeout=15).decode().splitlines();rows=p.Tree(source).finish();assert len(actual)==len(rows),(seq,len(actual),len(rows))
  for line,row in zip(actual,rows):
   n,parent,tag,attrs,a,b,text,kind=row;attrs=json.loads(attrs);attrtext=''.join(k+'='+('<null>' if v is None else v)+'\n' for k,v in sorted(attrs.items()));encode=lambda v:base64.b64encode(v.encode()).decode()
   expected='\t'.join([str(n),str(parent),encode(tag),encode(attrtext),str(a),str(b),encode(text),kind]);assert line==expected,(seq,n,line[:150],expected[:150])
  checks.append('actual Java complete-tree oracle and cancellation '+str(seq))

 # Constructed structure fixtures do not count as factual articles.
 source='<html><body><h2>Heading</h2><p>A &#x1F600; &amp; B</p><table><caption>Measure</caption><tr><th scope="row">Unit</th><td>2 m</td></tr></table><math><mroot><mi>x</mi><mn>5</mn></mroot></math><blockquote>Quoted text</blockquote><script>evil()</script><p>'+('Long 😀 text. '*2000)+'</p></body></html>'
 rows=p.Tree(source).finish();assert any(r[2]=='mroot' for r in rows) and any(r[2]=='blockquote' for r in rows);assert any(r[7]=='omitted-unsafe' for r in rows)
 for row in rows:
  if row[7]=='literal':assert cut(source,row[4],row[5])==row[6]
  if row[7]=='entity':assert html.unescape(cut(source,row[4],row[5]))==row[6]
  assert len(row[6].encode('utf-16-le'))//2<=4096
 checks.append('constructed only: nonBMP/entity/long/math/quotation/unsafe mapping and bounded leaves')
 original=json.loads(inputs[0][1].read_bytes())
 for kind in ['uri','revision','page','unbalanced']:
  d=json.loads(json.dumps(original))
  if kind=='uri':d['license'][0]['url']='https://example.invalid/'
  if kind=='revision':d['version']['identifier']=1
  if kind=='page':d['identifier']=1
  if kind=='unbalanced':d['article_body']['html']+='<table>'
  rejects(lambda:p.inspect(json.dumps(d).encode()));checks.append('reject '+kind)
 # Counterfactual metadata controls only; not additional original documents.
 changed=json.loads(json.dumps(original));changed['version']['identifier']+=1;changed['license'][0]['url']='invalid';new=out/'constructed-later.json';new.write_text(json.dumps(changed))
 later=p.build([(1,inputs[0][1]),(2,new)],out/'later-refusal');assert later['articles']==0;checks.append('later unsafe revision removes earlier eligibility; retained dispositions')
 duplicate=p.build([(1,inputs[0][1]),(2,inputs[0][1])],out/'duplicates');assert duplicate['articles']==1 and duplicate['dispositions'][1][3]=='duplicate';checks.append('duplicate revision not extra breadth')

 # An independently altered range must fail the original round-trip oracle.
 db.execute("update nodes set start=start+1 where id=(select min(id) from nodes where kind='literal' and end>start)");db.commit();db.close()
 mm=json.loads((out/'pack/manifest.json').read_text());mm['db_sha256']=digest((out/'pack/index.sqlite').read_bytes());(out/'pack/manifest.json').write_text(json.dumps(mm));rejects(lambda:verify(out/'pack'));checks.append('altered range fails independent round trip even with rehashed database')
 # Keep corrupted experiment separate. Rebuild final capsule once with identical inputs.
 final=p.build(inputs,out/'final');db,final=verify(out/'final');costs=dict(db.execute('SELECT name,sum(pgsize) FROM dbstat GROUP BY name'));db.close()
 report={'status':'PASS','checks':checks,'genuine_documents':4,'genuine_math_quote_nonBMP_long_coverage':False,'source_admission_established':False,'elapsed_seconds':time.monotonic()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'component_page_bytes':costs,'allocated_database_bytes':(out/'final/index.sqlite').stat().st_blocks*512,'storage':{'database_bytes':(out/'final/index.sqlite').stat().st_size,'archive_bytes':(out/'final/sources.plsource').stat().st_size,'original_bytes':sum(x.stat().st_size for _,x in inputs)},'manifest':final}
 (out/'host.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main(pathlib.Path(sys.argv[1]))
