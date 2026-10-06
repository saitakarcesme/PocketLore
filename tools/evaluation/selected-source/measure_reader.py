import hashlib,importlib.util,json,pathlib,resource,sqlite3,sys,time,zlib
ROOT=pathlib.Path(__file__).resolve().parents[3];path=ROOT/'tools/packs/selected-source/read.py';spec=importlib.util.spec_from_file_location('reader',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def run(out):
 out=pathlib.Path(out);fixtures=json.loads((ROOT/'docs/evidence/selected-source-production/reader-fixtures.json').read_text());r=m.InspectionReader(out/'index.sqlite');results=[]
 for query in fixtures['queries']:
  measurements=[]
  for repeat in range(2):
   begin=time.perf_counter();rows=r.search(query);measurements.append({'seconds':time.perf_counter()-begin,'rows':len(rows),'ids':[x[0] for x in rows]});assert len(rows)<=20 and all(len(x[7])<=240 for x in rows)
  assert measurements[0]['ids']==measurements[1]['ids'];results.append({'query':query,'first_open_and_repeat_not_cold_OS':measurements})
 row=r.db.execute("SELECT page,revision,start,end FROM pieces WHERE kind='html' AND part=0 ORDER BY page LIMIT 1").fetchone();page,rev,a,b=row;window=r.html_window(page,rev,a,b)
 # Independently reconstruct original JSON from exact original capsule chunks.
 original=b''.join(zlib.decompress(x[0]) for x in r.db.execute("SELECT c.z FROM pieces p JOIN capsules c ON c.sha=p.sha WHERE page=? AND revision=? AND p.kind='original' ORDER BY part",(page,rev)))
 source=json.loads(original)['article_body']['html'].encode('utf-16-le');assert window.encode('utf-16-le')==source[a*2:b*2]
 negatives=[]
 for name,fn in [('limit',lambda:r.search('water',21)),('window',lambda:r.html_window(page,rev,0,8193))]:
  try:fn()
  except ValueError:negatives.append(name)
  else:raise AssertionError('Negative accepted '+name)
 r.close();r=m.InspectionReader(out/'index.sqlite',lambda:True)
 try:r.search('water')
 except InterruptedError:negatives.append('cancel before search')
 else:raise AssertionError('Cancellation ignored')
 r.close();calls=[0]
 def cancel():calls[0]+=1;return calls[0]>=2
 r=m.InspectionReader(out/'index.sqlite',cancel)
 try:r.html_window(page,rev,a,b)
 except (InterruptedError,sqlite3.OperationalError):negatives.append('cancel during window')
 else:raise AssertionError('Window cancellation ignored')
 r.close();report={'executed_harness_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'status':'PASS','fixture_sha256':hashlib.sha256((ROOT/'docs/evidence/selected-source-production/reader-fixtures.json').read_bytes()).hexdigest(),'reader_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_index_sha256':json.loads((out/'status.json').read_text())['index_sha256'],'queries':results,'negative_controls':negatives,'window':{'page':page,'revision':rev,'start16':a,'end16':b,'sha256':hashlib.sha256(window.encode()).hexdigest()},'harness_including_oracle_peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'android_execution':False}
 (out/'reader-measurements-v2.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':run(sys.argv[1])
