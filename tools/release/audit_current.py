#!/usr/bin/env python3
"""Non-release audit of current bytes while final freeze is explicitly deferred.
Never replaces release-v4 or the distribution inventory accepted for that release.
"""
import argparse,datetime,hashlib,importlib.util,json,pathlib,re,shlex,shutil,subprocess,tempfile,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('inventory',ROOT/'tools/distribution/inventory.py');inv=importlib.util.module_from_spec(spec);spec.loader.exec_module(inv)
def cmd(args,cwd=ROOT):return subprocess.check_output(list(map(str,args)),cwd=cwd,text=True)
def record(p,role):return inv.file(p,role)
def walk(node):
 if isinstance(node,dict):
  if {'path','sha256','bytes','role'}<=node.keys():yield node
  for v in node.values():yield from walk(v)
 elif isinstance(node,list):
  for v in node:yield from walk(v)
def check(path,r):
 if not path.is_file() or path.stat().st_size!=r['bytes'] or inv.sha(path)!=r['sha256']:raise ValueError('Missing/changed artifact: '+str(path))
def index_component(abi,out):
 build=ROOT/'downloads/sqlite'/('build-'+abi);link=build/'CMakeFiles/pocketlore_index.dir/link.txt'
 trace=subprocess.run(shlex.split(link.read_text())+['-###'],cwd=build,capture_output=True,text=True,check=True).stderr
 (out/('index-link-'+abi+'.txt')).write_text(trace)
 line=next(x for x in trace.splitlines() if 'ld.lld"' in x);tokens=shlex.split(line);dirs=[pathlib.Path(x[2:]) for x in tokens if x.startswith('-L')];inputs=[]
 def locate(name):return next(d/name for d in dirs if (d/name).is_file())
 for t in tokens:
  if t.endswith(('.a','.o')) and not t.startswith('-'):
   p=pathlib.Path(t);inputs.append(p if p.is_absolute() else build/p)
  elif t in ('-latomic','-lc++','-l:libunwind.a'):
   name={'-latomic':'libatomic.a','-lc++':'libc++.a','-l:libunwind.a':'libunwind.a'}[t];inputs.append(locate(name))
   if name=='libc++.a':inputs.extend([locate('libc++_static.a'),locate('libc++abi.a')])
 rows=[]
 for p in sorted(set(inputs)):
  sqlite=p.name=='sqlite3.c.o';own=p.name=='index.cpp.o'
  notice=ROOT/'android/app/src/main/assets/licenses/sqlite.txt' if sqlite else (ROOT/'LICENSE' if own else inv.TC/'android-ndk-r27c/NOTICE.toolchain')
  rows.append({'artifact':record(p,'index-static-link-input'),'license':'Public domain' if sqlite else ('Apache-2.0' if own else 'LicenseRef-NDK-aggregate'),'notice':record(notice,'index-component-notice')})
 assert any(x['artifact']['path'].endswith('sqlite3.c.o') for x in rows)
 assert any(x['artifact']['path'].endswith('index.cpp.o') for x in rows)
 library=ROOT/'android/app/build/generated/nativeLibs'/abi/'libpocketlore_index.so'
 elf=cmd([inv.TC/'android-ndk-r27c/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf','-d',library])
 return {'abi':abi,'library':record(library,'packaged-index-native'),'link':record(link,'index-link-command'),'inputs':rows,'elf_needed':re.findall(r'Shared library: \[(.*?)\]',elf),'scope':'Actual linker inputs; discarded members are not asserted to survive'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
 target=out/'current-audit.json'
 if target.exists():raise ValueError('Refusing to replace preserved audit')
 original={x:inv.sha(ROOT/x) for x in ['docs/evidence/release-v4/manifest.json','docs/distribution-inventory.json']}
 report=inv.capture();report['scope']='Current task300 development bytes; final task213 release freeze DEFERRED until selected model/bulk integration. Not a replacement release inventory.'
 report['created_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['source_commit']=cmd(['git','rev-parse','HEAD']).strip()
 report['index_native']=[index_component(abi,out) for abi in ('arm64-v8a','x86_64')]
 report['sqlite_pin']=json.loads((ROOT/'tools/runtime/sqlite-pin.json').read_text())
 report['sqlite_sources']=[record(ROOT/'downloads/sqlite/sqlite-amalgamation-3530400'/name,'pinned-sqlite-source') for name in ('sqlite3.c','sqlite3.h')]
 for r in report['sqlite_sources']:assert r['sha256']==report['sqlite_pin']['source_files'][pathlib.Path(r['path']).name]
 report['reviewed_broad_pack']=record(ROOT/'downloads/broad-reference/rendered-v2/broad-reference.plpack','reviewed-broad-not-bulk-wiki')
 assert report['reviewed_broad_pack']['sha256']=='b8d18801b099402205938979ab2bb44ee9a316f06f030aab789cf93ba3605012'
 report['scale_receipts']={k:json.loads((ROOT/'docs/evidence/scale-integration'/(k+'-receipt.json')).read_text()) for k in ('wiki','places')}
 report['prior_identity_files_preserved']=original
 apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk'
 with zipfile.ZipFile(apk) as z:
  report['complete_apk_entries']={n:{'bytes':len(z.read(n)),'sha256':hashlib.sha256(z.read(n)).hexdigest()} for n in z.namelist() if not n.endswith('/')}
  expected={f'lib/{abi}/{name}' for abi in ('arm64-v8a','x86_64') for name in ('libpocketlore.so','libpocketlore_index.so')}
  assert {n for n in z.namelist() if n.startswith('lib/') and n.endswith('.so')}==expected
  for r in report['index_native']:assert hashlib.sha256(z.read('lib/'+r['abi']+'/libpocketlore_index.so')).hexdigest()==r['library']['sha256']
  assert z.read('assets/licenses/sqlite.txt')==(ROOT/'android/app/src/main/assets/licenses/sqlite.txt').read_bytes()
 adb=[inv.TC/'sdk/platform-tools/adb','-s','emulator-5560']
 path=cmd(adb+['shell','pm','path','org.pocketlore.app']).strip().removeprefix('package:')
 assert cmd(adb+['shell','sha256sum',path]).split()[0]==report['apk']['sha256']
 catalog=json.loads(cmd(adb+['exec-out','run-as','org.pocketlore.app','cat','files/pack-library/catalog.json']))
 installed=[]
 for e in catalog['collections']:
  for suffix in ('.plpack','.sqlite'):
   name='files/pack-library/'+e['sha256']+suffix
   if suffix=='.sqlite' and e['sha256']!=report['reviewed_broad_pack']['sha256']:continue
   size=int(cmd(adb+['shell','run-as','org.pocketlore.app','stat','-c','%s',name]).strip());digest=cmd(adb+['shell','run-as','org.pocketlore.app','sha256sum',name]).split()[0]
   if suffix=='.plpack':assert digest==e['sha256']
   installed.append({'path':name,'bytes':size,'sha256':digest})
 model='files/model.gguf';modelsha=cmd(adb+['shell','run-as','org.pocketlore.app','sha256sum',model]).split()[0]
 assert modelsha=='74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db'
 report['installed_observation']={'scope':'Existing emulator installation, not fresh release demonstration','catalog':catalog,'files':installed,'model_sha256':modelsha,'disk':cmd(adb+['shell','df','-k','/data']),'app_allocation_kib':cmd(adb+['shell','run-as','org.pocketlore.app','du','-k','-s','files','cache'])}
 seen=set()
 for r in walk(report):
  if r['path'] in seen:continue
  check(inv.resolve(r['path']),r);seen.add(r['path'])
 mutations=[]
 selected=[report['apk'],report['index_native'][1]['library'],report['index_native'][1]['inputs'][0]['notice'],record(ROOT/'docs/evidence/scale-integration/acceptance-run/native.json','actual-jni-receipt')]
 with tempfile.TemporaryDirectory(prefix='pocketlore-release-audit-') as d:
  for i,r in enumerate(selected):
   path=pathlib.Path(d)/str(i);shutil.copyfile(inv.resolve(r['path']),path);check(path,r)
   with path.open('r+b') as f:v=f.read(1);f.seek(0);f.write(bytes([v[0]^1]))
   for mode in ('changed','missing'):
    if mode=='missing':path.unlink()
    try:check(path,r)
    except ValueError as e:mutations.append({'artifact':r['path'],'mutation':mode,'rejected':str(e)})
    else:raise AssertionError('Bad artifact accepted')
 report['integrity_regressions']=mutations;report['verified_unique_host_files']=len(seen)
 assert all(inv.sha(ROOT/n)==h for n,h in original.items())
 target.write_text(json.dumps(report,indent=2)+'\n');print('PASS current-byte audit; final freeze DEFERRED:',target)
if __name__=='__main__':main()
