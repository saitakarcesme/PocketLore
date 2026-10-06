"""Frozen current behavior collector. Full acceptance fails without actual Android receipts."""
import base64,hashlib,json,pathlib,subprocess,time,uuid,zlib,lzma,sys
R=pathlib.Path(__file__).resolve().parents[3];ART=R/'docs/evidence/document-formats-review.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def file(p):
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=sha(b),encoding='lzma+base64',data=base64.b64encode(lzma.compress(b,preset=3)).decode())
def main():
 rid=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'-'+uuid.uuid4().hex[:8];out=R/'downloads/document-formats'/('check-'+rid);out.mkdir();report={'run_id':rid,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'started':time.time(),'errors':[],'files':[]}
 try:
  source=subprocess.check_output(['git','ls-files','android','tools/evaluation/document-formats','tools/evaluation/check_document_formats.sh','tools/android-build.sh'],cwd=R,text=True).splitlines();report['source_manifest']={p:sha((R/p).read_bytes()) for p in source if (R/p).is_file()}
  for p in source:
   if '/document-formats/' in p or any(p.endswith('/'+n+'.java') for n in ('DocumentBytes','DocumentHtml','DocumentFormatPolicy','StructuredDocuments','PersonalDocuments','PersonalDocumentsActivity','PackLibrary','KnowledgePack','PersonalText')):report['files'].append(file(R/p))
  proc=subprocess.run([sys.executable,'tools/evaluation/document-formats/host_checks.py'],cwd=R,capture_output=True,timeout=180);report['host_invocation']={'exit':proc.returncode,'stdout':proc.stdout.decode(),'stderr':proc.stderr.decode()};(out/'host.stdout').write_bytes(proc.stdout);(out/'host.stderr').write_bytes(proc.stderr)
  summary=json.loads(proc.stdout.decode().splitlines()[-1]);current=pathlib.Path(summary['path'])/'host-report.json';host=json.loads(current.read_text());report['current_host_report_sha256']=sha(current.read_bytes());report['host_summary']={k:host[k] for k in ('run_id','host_pass','errors','host_child_maxrss_bytes','memory_scope','owned_fixture_logical_bytes','owned_fixture_allocated_bytes')};report['case_results']=[{k:c[k] for k in ('name','expected','passed')} for c in host['cases']];assert proc.returncode==0 and host['host_pass']
  builds=[]
  for kind in ('production','instrumentation'):
   dirs=sorted((R/'downloads/document-formats').glob('build-'+kind+'-*'));assert dirs,'Missing '+kind+' build';d=dirs[-1];b=json.loads((d/'receipt.json').read_text());assert b['exit']==0 and b['inputs_unchanged']
   for p,digest in b['source_after'].items():assert sha((R/p).read_bytes())==digest,'Stale build input: '+p
   for p,a in b['artifacts'].items():
    if ('androidTest' in p)==(kind=='instrumentation'):assert sha(pathlib.Path(p).read_bytes())==a['sha256'],'Changed APK'
   report['files'] += [file(d/n) for n in ('receipt.json','stdout','stderr')];builds.append({'kind':kind,'receipt_sha256':sha((d/'receipt.json').read_bytes()),'artifacts':b['artifacts']})
  report['builds']=builds
  assert report['source_manifest']=={p:sha((R/p).read_bytes()) for p in report['source_manifest']},'Source changed during check'
 except Exception as e:report['errors'].append(type(e).__name__+': '+str(e))
 finally:
  # Preserve all earlier task invocations and raw failures; compressed inline bytes remain independently inspectable.
  for p in sorted((R/'downloads/document-formats').glob('*/host-report.json')):report['files'].append(file(p))
  for d in sorted((R/'downloads/document-formats').glob('build-*')):
   for n in ('receipt.json','stdout','stderr'):
    p=d/n
    if p.is_file() and not any(f['path']==str(p) for f in report['files']):report['files'].append(file(p))
  terminal=pathlib.Path('/home/isa/PocketLore-control/overnight-20261005/swiftshader-terminal-20261006T0347Z.json')
  if terminal.is_file():report['files'].append(file(terminal))
  for p in sorted((R/'downloads/document-formats').glob('central-directory-red/*')):report['files'].append(file(p))
  for p in sorted((R/'downloads/document-formats').glob('initial/*')):report['files'].append(file(p))
  for name in ('initial-build.log','test-build.log','docx-independent-open.json'):
   p=R/'downloads/document-formats'/name
   if p.exists():report['files'].append(file(p))
  for p in (R/'docs/evidence/document-formats').glob('*.json'):report['files'].append(file(p))
  report.update(ended=time.time(),exit=1,classification='HOST_PASS_ANDROID_UNEXECUTED' if not report['errors'] else 'HOST_FAILURE_ANDROID_UNEXECUTED',android_executed=False,missing=['Real six-format Android extraction and exact spans','Real production SAF picker import/source reader journey','Actual portable reimport mismatch/disabled collections/fresh-process/Activity cancellation and protected catalog retention','Current full app/corpus/model/provider/update storage and aggregate memory; physical/GrapheneOS and matched unseen evidence'])
  (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');prior=json.loads(ART.read_text()) if ART.exists() else {'schema':1,'runs':[]};prior['runs'].append(report);ART.write_text(json.dumps(prior,indent=2)+'\n')
 print(json.dumps({k:report[k] for k in ('run_id','classification','errors','exit','missing')},indent=2));return 1
if __name__=='__main__':raise SystemExit(main())
