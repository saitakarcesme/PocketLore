from pathlib import Path
import json,hashlib,tempfile,shutil,subprocess,sys
R=Path(__file__).resolve().parents[3];P=R/'docs/evidence/general-generation-repair';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def verify(d):
 seal=json.loads((d/'seal.json').read_text());assert seal['status']=='PASS'
 for n,h in seal['files'].items():assert sha(d/n)==h,n
 inputs=json.loads((d/'source.json').read_text())
 for n,h in inputs.items():
  # Bind production, instrumentation and executed build/capture inputs; the newly added offline checker was not compiled.
  executed=n.startswith('android/') or n.startswith('tools/evaluation/general-generation-repair/') or n in ['tools/android-build.sh','tools/evaluation/reference-expansion/capture.py']
  if executed:assert sha(R/n)==h,n
  elif sha(R/n)!=h:print('Recorded unexecuted repository file changed after run: '+n)
 report=json.loads((d/'report.json').read_text());assert report['source_hash']==sha(d/'source.json') and report['run_id']==d.name
 assert report['kind']=='ABSTAINED' and report['invoked_model'] is False and report['api']==37
 assert (d/'before-page.txt').read_text().strip()=='16384'
 for key in ['boot','font','catalog']:assert (d/('before-'+key+'.txt')).read_bytes()==(d/('final-'+key+'.txt')).read_bytes()
 for key,file in [('app','app-debug.apk'),('test','app-debug-androidTest.apk')]:assert (d/(key+'-hash.txt')).read_text().split()[0]==sha(d/'binaries'/file)
 for f in d.glob('*.command.json'):assert json.loads(f.read_text())['returncode']==0
 assert 'INSTRUMENTATION_CODE: -1' in (d/'instrumentation.txt').read_text()
h=json.loads((P/'HANDOFF.json').read_text());d=Path(h['run']);verify(d)
for name in ['report.json','app-hash.txt']:
 with tempfile.TemporaryDirectory() as t:
  copy=Path(t)/d.name;copy.mkdir()
  for f in d.iterdir():
   if f.is_file():shutil.copy2(f,copy/f.name)
  (copy/name).write_text('corrupt')
  try:verify(copy)
  except (AssertionError,ValueError):pass
  else:raise AssertionError('Corrupt Android receipt accepted')
subprocess.run([sys.executable,R/'tools/evaluation/general-generation-repair/check.py'],check=True)
print('PASS: actual API37 unavailable-verifier UI route, exact artifacts, retention, and corruption rejection; NOT selected-model JNI or quality')
