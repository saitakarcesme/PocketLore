import pathlib,json,hashlib,sys,tempfile,shutil
ROOT=pathlib.Path(__file__).resolve().parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def verify(out):
 m=json.loads((out/'manifest.json').read_text());assert sha(out/'source.json')==m['source_hash']
 for n,h in m['files'].items():assert sha(out/n)==h,n
 for n,h in json.loads((out/'source.json').read_text())['inputs'].items():assert sha(ROOT/n)==h,n
 for key,a in m['apks'].items():
  assert sha(pathlib.Path(a['path']))==a['sha256']
  for when in ['installed','final']:assert (out/(when+'-'+key+'-hash.txt')).read_text().split()[0]==a['sha256']
 for state in ['boot','font','rotation','models']:assert (out/('before-'+state+'.txt')).read_bytes()==(out/('final-'+state+'.txt')).read_bytes()
 assert (out/'api.txt').read_text().strip()=='37' and (out/'pages.txt').read_text().strip()=='16384'
 for phase in ['install','restart']:
  r=json.loads((out/(phase+'.json')).read_text());assert r['status']=='PASS' and r['run_id']==m['run_id'] and r['source_hash']==m['source_hash']
  raw=(out/(phase+'-raw.txt')).read_text();assert 'INSTRUMENTATION_CODE: -1' in raw
  receipt=json.loads(next(x.split('=',1)[1] for x in raw.splitlines() if x.startswith('INSTRUMENTATION_RESULT: receipt=')));assert receipt['report_sha256']==sha(out/(phase+'.json')) and receipt['source_hash']==m['source_hash']
  assert len(r['outputs'])==8
  for row in r['outputs']:
   assert row['generated'] is False
   for q in row['quotes']:assert row['rendered'].encode('utf-16-le')[q['start']*2:q['end']*2].decode('utf-16-le')==q['text'] and hashlib.sha256(q['text'].encode()).hexdigest()==q['sha256']
  assert {'one request spans reviewed science and personal editions','cancellation within retrieval','deleted source absent in rebuilt catalog','conflicting conditions preserved verbatim','selection cancel retained'}.issubset(r['checks'])
 a=json.loads((out/'install.json').read_text());b=json.loads((out/'restart.json').read_text());assert a['catalog']==b['catalog'];assert [x['rendered'] for x in a['outputs']]==[x['rendered'] for x in b['outputs']]
 return m
if __name__=='__main__':
 h=json.loads((ROOT/'docs/evidence/federated/HANDOFF.json').read_text());out=pathlib.Path(h['run']);verify(out);neg=[]
 for name in ['final-app-hash.txt','install.json','final-boot.txt']:
  with tempfile.TemporaryDirectory() as tmp:
   dst=pathlib.Path(tmp)
   for p in out.iterdir():
    if p.is_file():shutil.copyfile(p,dst/p.name)
   (dst/name).write_text('changed')
   try:verify(dst)
   except (AssertionError,ValueError):neg.append(name)
   else:raise AssertionError('corruption accepted')
 print(json.dumps({'status':'PASS','run':h['run'],'negative_controls':neg,'scope':'API37 public development source briefs, not generated or unseen quality'}))
