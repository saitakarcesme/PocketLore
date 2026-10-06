"""Independent authored oracles against exact production Java; no Android substitution."""
import base64,hashlib,io,json,pathlib,random,struct,subprocess,time,zipfile,sys,uuid,resource
ROOT=pathlib.Path(__file__).resolve().parents[3];PREREQ=pathlib.Path('/home/isa/PocketLore-control/overnight-20261005/document-complete-authored-prerequisites-20261006T0548Z');JAVA='/home/isa/Android/atlas-toolchain/jdk/bin/'
def sha(b):return hashlib.sha256(b).hexdigest()
def freeze(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':sha(b),'base64':base64.b64encode(b).decode()}
def zip_bytes(items,compression=zipfile.ZIP_STORED):
 b=io.BytesIO()
 with zipfile.ZipFile(b,'w',compression=compression) as z:
  for name,data in items:
   entry=zipfile.ZipInfo(name,(2026,1,1,0,0,0));entry.compress_type=compression;z.writestr(entry,data)
 return b.getvalue()
def mutated(raw,name,data,extra=()):
 with zipfile.ZipFile(io.BytesIO(raw)) as z:items=[(n,data if n==name else z.read(n)) for n in z.namelist()]
 return zip_bytes(items+list(extra))
def main():
 rid=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'-'+uuid.uuid4().hex[:8];out=ROOT/'downloads/document-formats'/rid;out.mkdir();fixtures=out/'fixtures';fixtures.mkdir();classes=out/'classes';classes.mkdir();report={'run_id':rid,'scope':'Host production extractor controls; Android, catalog, provider and portable reimport execution separate','cases':[],'commands':[],'errors':[]};start=time.time()
 def run(argv,timeout=35):
  t=time.time();p=subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=timeout);r={'argv':argv,'start':t,'end':time.time(),'exit':p.returncode,'stdout':p.stdout.decode(),'stderr':p.stderr.decode()};report['commands'].append(r);return r
 try:
  manifest=(PREREQ/'manifest.json').read_bytes();assert sha(manifest)=='51881cf59891b337af44b93a2166c25f96ce4c6ac4841c54029320ec10c05040'
  oracle=json.loads((PREREQ/'independent-source-contexts.json').read_text());report['original_oracles']=[freeze(PREREQ/n) for n in ('manifest.json','independent-source-contexts.json','review.json','policy.json','package-checks.json')];report['limits']=freeze(ROOT/'docs/evidence/document-formats/limits.json')
  originals={p.name:p.read_bytes() for p in (PREREQ/'documents').iterdir()};report['authored_originals']=[freeze(p) for p in sorted((PREREQ/'documents').iterdir())]
  cases=[]
  for name,raw in sorted(originals.items()):
   o=oracle[name];paras=o.get('paragraphs') or sum([x['paragraphs'] for x in o.get('spine_order',o.get('slides_in_presentation_relationship_order',[]))],[]);cases.append((name,name.split('.')[-1],raw,'\n'.join(paras),-1))
  doc=originals['fixture.docx'];W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
  def word(body):return ('<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="'+W+'"><w:body>'+body+'</w:body></w:document>').encode()
  def para(text):return '<w:p><w:r><w:t>'+text+'</w:t></w:r></w:p>'
  def doccase(name,body,expected):cases.append((name,'docx',mutated(doc,'word/document.xml',word(body)),expected,-1))
  def bad(name,fmt,raw):cases.append((name,fmt,raw,None,-1))
  doccase('inline-entity-emoji.docx','<w:p><w:r><w:t>If &amp; only </w:t></w:r><w:r><w:t>then 🙂.</w:t></w:r></w:p>','If & only then 🙂.')
  doccase('office-fallback','<w:p xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"><mc:AlternateContent><mc:Choice Requires="extension"><w:r><w:t>UNSUPPORTED CHOICE</w:t></w:r></mc:Choice><mc:Fallback><w:r><w:t>Fallback only</w:t></w:r></mc:Fallback></mc:AlternateContent></w:p>','Fallback only')
  doccase('office-missing-fallback','<w:p xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"><mc:AlternateContent><mc:Choice Requires="extension"><w:r><w:t>Unsupported</w:t></w:r></mc:Choice></mc:AlternateContent></w:p>',None)
  doccase('visible-false-vanish','<w:p><w:r><w:rPr><w:vanish w:val="false"/></w:rPr><w:t>Visible</w:t></w:r></w:p>','Visible')
  doccase('hidden-word-run','<w:p><w:r><w:rPr><w:vanish/></w:rPr><w:t>HIDDEN</w:t></w:r><w:r><w:t>Visible</w:t></w:r></w:p>','Visible')
  bad('wrong-extension','odt',doc);bad('not-zip','docx',b'not a ZIP');bad('corrupt-zip','docx',doc[:-30]);bad('input-over','html',b'x'*(4194304+1))
  with zipfile.ZipFile(io.BytesIO(doc)) as z:base=[(n,z.read(n)) for n in z.namelist()]
  bad('duplicate','docx',zip_bytes(base+[base[0]]));bad('traversal','docx',zip_bytes(base+[('../escape',b'x')]))
  bad('encrypted-flag','docx',doc[:6]+struct.pack('<H',struct.unpack('<H',doc[6:8])[0]|1)+doc[8:])
  bad('entry-over','docx',zip_bytes(base+[('big',b'x'*(2097152+1))]));bad('ratio-bomb','docx',zip_bytes(base+[('bomb',b'x'*2000000)],zipfile.ZIP_DEFLATED))
  cases.append(('entries-exact','docx',zip_bytes(base+[(f'empty/{i}',b'') for i in range(256-len(base))]),'\n'.join(oracle['fixture.docx']['paragraphs']),-1))
  bad('entries-over','docx',zip_bytes(base+[(f'empty/{i}',b'') for i in range(257-len(base))]))
  rng=random.Random(526);chunk=rng.randbytes(65536);payload=chunk*32
  # Ratio below100 and input below4MiB; actual aggregate expansion exceeds16MiB.
  bad('aggregate-over','docx',zip_bytes(base+[(f'expanded/{i}',payload) for i in range(9)],zipfile.ZIP_DEFLATED))
  cases.append(('entry-exact','docx',zip_bytes(base+[('exact',b'x'*2097152)]),'\n'.join(oracle['fixture.docx']['paragraphs']),-1))
  doccase('depth-exact','<w:customXml>'*59+para('depth')+'</w:customXml>'*59,'depth');doccase('depth-over','<w:customXml>'*60+para('depth')+'</w:customXml>'*60,None)
  doccase('paragraph-exact',para('x'*20000),'x'*20000);doccase('paragraph-over',para('x'*20001),None)
  doccase('segments-exact',para('x')*1000,'\n'.join(['x']*1000));doccase('segments-over',para('x')*1001,None)
  pieces=['x'*19999]*24+['x'*20000];doccase('output-exact',''.join(para(x) for x in pieces),'\n'.join(pieces));doccase('output-over',''.join(para(x) for x in pieces)+para('x'),None)
  bad('unused-malformed-xml','docx',zip_bytes(base+[('unused.xml',b'<unclosed>')]))
  bad('html-wrong-charset','html',b'<meta charset=windows-1252><p>text</p>')
  bad('malformed-xml','docx',mutated(doc,'word/document.xml',b'<unclosed>'))
  bad('xxe','docx',mutated(doc,'word/document.xml',('''<!DOCTYPE w:document [<!ENTITY external SYSTEM "file:///never-read">]>'''+word(para('&external;')).decode().split('?>',1)[1]).encode()))
  bad('empty-image-only','docx',mutated(doc,'word/document.xml',word('<w:p/>')))
  bad('external-main','docx',mutated(doc,'_rels/.rels',b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="x" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" TargetMode="External" Target="https://invalid.invalid/a.xml"/></Relationships>'))
  epub=originals['fixture.epub'];bad('epub-spine','epub',mutated(epub,'OEBPS/content.opf',b'<bad/>')) if 'OEBPS/content.opf' in zipfile.ZipFile(io.BytesIO(epub)).namelist() else None
  with zipfile.ZipFile(io.BytesIO(epub)) as z:opf=next(n for n in z.namelist() if n.endswith('.opf'));opfraw=z.read(opf)
  bad('epub-missing-idref','epub',mutated(epub,opf,opfraw.replace(b'idref="two"',b'idref="missing"') if b'idref="two"' in opfraw else opfraw.replace(b'<spine>',b'<spine><itemref idref="missing"/>')))
  with zipfile.ZipFile(io.BytesIO(epub)) as z:chapter=z.read('OEBPS/chapter-two.xhtml')
  csschapter=chapter.replace(b'</head>',b'<link rel="stylesheet" href="local.css" /></head>').replace(b'</body>',b'<p class="hide">HIDDEN</p></body>')
  expected_epub='\n'.join(sum([x['paragraphs'] for x in oracle['fixture.epub']['spine_order']],[]))
  cases.append(('epub-local-css','epub',mutated(epub,'OEBPS/chapter-two.xhtml',csschapter,extra=[('OEBPS/local.css',b'.hide {display:none}')]),expected_epub,-1))
  bad('encrypted-epub','epub',mutated(epub,opf,opfraw,extra=[('META-INF/encryption.xml',b'<encryption/>')]))
  html=b'<html><head><style>.hide {display:none} p {color:blue}</style></head><body><p>Visible <b>conditional</b> text &amp; emoji &#128578;.</p><p hidden>HIDDEN</p><p class="hide">CSS HIDDEN</p><div style="visibility:hidden">INLINE HIDDEN</div><script>BAD</script><style>p {color: red}</style><p><a href="https://invalid.invalid/no-fetch">Inert link</a></p></body></html>'
  cases.append(('html-hidden','html',html,'Visible conditional text & emoji 🙂.\nInert link',-1));bad('html-external-style','html',b'<link rel="stylesheet" href="https://invalid.invalid/x"><p>unsafe style visibility</p>');bad('html-xxe','html',b'<!DOCTYPE html SYSTEM "https://invalid.invalid"><p>text</p>');bad('html-malformed','html',b'<div><span>text</div>');bad('html-hidden-only','html',b'<p hidden>secret</p>');bad('html-complex-css','html',b'<style>@media screen {p {display:none}}</style><p>x</p>')
  cases.append(('html-length-changing-unicode','html','<p>İstanbul visible</p><script>HIDDEN</script><style>p{color:blue}</style>'.encode(),'İstanbul visible',-1))
  cases.append(('html-print-only-css','html',b'<style media="print">p{display:none}</style><link rel="stylesheet" media="print" href="https://invalid.invalid/no-fetch"><p>Visible</p>','Visible',-1))
  bad('html-zero-opacity','html',b'<p style="opacity:.0">Hidden</p>')
  bad('html-transparent-color','html',b'<p style="color:transparent">Hidden</p>')
  bad('html-unresolved-position','html',b'<p style="position:absolute;left:-9999px">Offscreen</p>')
  cases.append(('css-last-declaration','html',b'<p style="display:none; display:block">Visible</p>','Visible',-1))
  cases.append(('css-cascade','html',b'<style>.x{display:none}.x{display:block} #keep{visibility:visible} .x{visibility:hidden}</style><p class="x" id="keep">Visible</p>','Visible',-1))
  cases.append(('css-important','html',b'<style>.x{display:none!important}</style><p class="x" style="display:block">HIDDEN</p><p>Visible</p>','Visible',-1))
  cases.append(('css-visible-descendant','html',b'<div style="visibility:hidden">HIDDEN<span style="visibility:visible">Visible</span></div>','Visible',-1))
  with zipfile.ZipFile(io.BytesIO(originals['fixture.odt'])) as z:odf=z.read('content.xml')
  altered=odf.replace(b'<office:text>',b'<office:text><text:section text:name="hidden" text:display="none"><text:p>HIDDEN</text:p></text:section>',1)
  assert altered!=odf
  cases.append(('odf-hidden-section','odt',mutated(originals['fixture.odt'],'content.xml',altered),'\n'.join(oracle['fixture.odt']['paragraphs']),-1))
  central=bytearray(zip_bytes(base));position=central.index(b'PK\x01\x02');central[position+10:position+12]=struct.pack('<H',8);bad('central-method-conflict','docx',bytes(central))
  central=bytearray(doc);position=central.index(b'PK\x01\x02');length=struct.unpack_from('<H',central,position+28)[0];central[position+46+length:position+46+length]=b'/';struct.pack_into('<H',central,position+28,length+1);struct.pack_into('<I',central,position+24,0);end=central.rindex(b'PK\x05\x06');struct.pack_into('<I',central,end+12,struct.unpack_from('<I',central,end+12)[0]+1);bad('central-file-directory-conflict','docx',bytes(central))
  cases.append(('nonbreaking-space','html',b'<p>Non&nbsp;breaking &#160;space.</p>','Non\u00a0breaking \u00a0space.',-1))
  bad('ampersand-flood','html',b'&'*4194304)
  cases.append(('ampersand-cancel','html',b'&'*4194304,None,32))
  bad('css-over','html',b'<style>'+b' '*65537+b'</style><p>x</p>')
  cases.extend([('cancel-before','docx',doc,None,0),('cancel-inflate','docx',doc,None,8),('cancel-xml','docx',doc,None,100)])
  # Freeze all expected outcomes and exact authored hostile bytes before invoking Java.
  ledger=[]
  for i,(name,fmt,raw,expected,stop) in enumerate(cases):
   p=fixtures/(str(i)+'-'+name);p.write_bytes(raw);ledger.append(dict(name=name,format=fmt,input_sha256=sha(raw),input_bytes=len(raw),expected_text=expected,cancel_after_checks=stop))
  (out/'frozen-cases.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2));report['frozen_cases']=freeze(out/'frozen-cases.json')
  source=[ROOT/'android/app/src/main/java/org/pocketlore/app'/f'{n}.java' for n in ('PersonalText','DocumentBytes','StructuredDocuments','DocumentHtml','DocumentFormatPolicy')]+[ROOT/'tools/evaluation/document-formats/ExtractionProbe.java',ROOT/'tools/evaluation/document-formats/FormatPolicyProbe.java']
  report['executed_sources']=[freeze(p) for p in source];assert run([JAVA+'javac','-d',str(classes)]+list(map(str,source)))['exit']==0
  assert run([JAVA+'java','-ea','-Xmx128m','-XX:ActiveProcessorCount=2','-cp',str(classes),'org.pocketlore.app.FormatPolicyProbe'],timeout=30)['exit']==0
  for i,(name,fmt,raw,expected,stop) in enumerate(cases):
   p=fixtures/(str(i)+'-'+name);r=run([JAVA+'java','-Xmx128m','-XX:ActiveProcessorCount=2','-cp',str(classes),'org.pocketlore.app.ExtractionProbe',str(p),fmt,str(out),str(stop)]);case={'name':name,'expected':'refusal' if expected is None else 'exact extraction','input':freeze(p),'command_index':len(report['commands'])-1,'passed':False}
   if expected is None:case['passed']=r['exit']==2
   elif r['exit']==0:
    lines=r['stdout'].splitlines();text=base64.b64decode(lines[0].split('\t')[1]).decode();spans=[]
    for line in lines[1:]:
     _,a,b,loc=line.split('\t');a,b=int(a),int(b);part=text.encode('utf-16-le')[a*2:b*2].decode('utf-16-le');spans.append({'start':a,'end':b,'location':base64.b64decode(loc).decode(),'text':part,'sha256':sha(part.encode())})
    case.update(actual_text_sha256=sha(text.encode()),spans=spans);case['passed']=text==expected and [s['text'] for s in spans]==expected.split('\n')
    offset=0
    for span,paragraph in zip(spans,expected.split('\n')):
     end=offset+len(paragraph.encode('utf-16-le'))//2;case['passed'] &= span['start']==offset and span['end']==end and bool(span['location']);offset=end+1
   report['cases'].append(case)
  assert all(c['passed'] for c in report['cases']),[c['name'] for c in report['cases'] if not c['passed']]
 except Exception as e:report['errors'].append(type(e).__name__+': '+str(e))
 report.update(end=time.time(),start=start,host_pass=not report['errors'],android_executed=False,host_child_maxrss_bytes=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss*1024,memory_scope='Host child highwater across javac and serial Java processes; configured128MiBheap/2activeCPUs, not total process-tree or Android peak',owned_fixture_logical_bytes=sum(p.stat().st_size for p in fixtures.iterdir()),owned_fixture_allocated_bytes=sum(p.stat().st_blocks*512 for p in fixtures.iterdir()));(out/'host-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(out),'cases':len(report['cases']),'errors':report['errors'],'host_pass':report['host_pass']}));return 0 if report['host_pass'] else 1
if __name__=='__main__':raise SystemExit(main())
