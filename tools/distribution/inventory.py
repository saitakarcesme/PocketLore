#!/usr/bin/env python3
"""Capture actual resolved artifacts and notices; unknown terms remain explicit."""
import hashlib,json,os,re,shlex,subprocess,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
TC=Path(os.environ.get('POCKETLORE_TOOLCHAIN','/home/isa/Android/atlas-toolchain'))
CACHE=TC/'gradle-user/caches/modules-2/files-2.1'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def path(p):
 p=Path(p).absolute()
 for base,label in [(ROOT,'PROJECT'),(TC,'TOOLCHAIN')]:
  if p.is_relative_to(base):return label+'/'+str(p.relative_to(base))
 if str(p) in ['/usr/bin/python3','/usr/bin/make','/usr/bin/bash']:return 'HOST/'+str(p).lstrip('/')
 raise ValueError('Unexpected artifact location: '+str(p))
def resolve(s):return {'PROJECT':ROOT,'TOOLCHAIN':TC,'HOST':Path('/')}[s.split('/',1)[0]]/s.split('/',1)[1]
def file(p,role):
 p=Path(p);return {'path':path(p),'bytes':p.stat().st_size,'sha256':sha(p),'role':role}
def embedded(p):
 try:
  with zipfile.ZipFile(p) as z:
   return [{'entry':n,'sha256':hashlib.sha256(z.read(n)).hexdigest(),'bytes':len(z.read(n))} for n in sorted(z.namelist()) if re.search(r'(^|/)(license|notice|copying)([._-]|$)',n,re.I) and not n.endswith(('/','.class'))]
 except zipfile.BadZipFile:return []
def pom(coordinate,seen=None):
 seen=set() if seen is None else seen
 if coordinate in seen:return [],[]
 seen.add(coordinate);g,a,v=coordinate.split(':');matches=sorted((CACHE/g/a/v).glob('*/*.pom'))
 if not matches:return [],[]
 p=matches[0];root=ET.parse(p).getroot();ns={'m':'http://maven.apache.org/POM/4.0.0' if root.tag.startswith('{') else ''}
 licenses=[{'name':l.findtext('m:name',default='',namespaces=ns),'url':l.findtext('m:url',default='',namespaces=ns),'comments':l.findtext('m:comments',default='',namespaces=ns),'declared_in':path(p)} for l in root.findall('m:licenses/m:license',ns)]
 descriptors=[file(p,'resolved-pom')]
 if not licenses:
  parent=root.find('m:parent',ns)
  if parent is not None:
   parentid=':'.join(parent.findtext('m:'+n,default='',namespaces=ns) for n in ['groupId','artifactId','version'])
   if '$' not in parentid:
    inherited,others=pom(parentid,seen);licenses+=inherited;descriptors+=others
 return licenses,descriptors
def capture():
 out=ROOT/'downloads/distribution';out.mkdir(parents=True,exist_ok=True)
 apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk'
 inv={'schema':1,'distribution_ready':False,'scope':'Debug candidate inventory; no publication, legal clearance or independent clean-machine reproduction','apk':file(apk,'debug-candidate'),'native':[],'resolved_build_dependencies':[],'toolchain':[],'models':[],'data':[],'gaps':[]}
 with zipfile.ZipFile(apk) as z:
  inv['apk_entries']=[{'entry':n,'sha256':hashlib.sha256(z.read(n)).hexdigest(),'bytes':len(z.read(n))} for n in sorted(z.namelist()) if n.startswith(('lib/','assets/'))]
  required=json.loads((ROOT/'tools/distribution/native-notices.lock.json').read_text())
  for n in required:assert hashlib.sha256(z.read(n['apk_path'])).hexdigest()==n['sha256']
 for abi in ['arm64-v8a','x86_64']:
  build=ROOT/'android/native-build/build'/abi;link=build/'CMakeFiles/pocketlore.dir/link.txt'
  trace=subprocess.run(shlex.split(link.read_text())+['-###'],cwd=build,capture_output=True,text=True,check=True).stderr
  (out/('link-'+abi+'.txt')).write_text(trace)
  command=shlex.split(next(line for line in trace.splitlines() if 'ld.lld"' in line));dirs=[Path(x[2:]) for x in command if x.startswith('-L')]
  inputs=[]
  def locate(name):
   for d in dirs:
    if (d/name).is_file():return d/name
   raise ValueError('Unresolved native input '+name)
  for token in command:
   if token.endswith(('.a','.o')) and not token.startswith('-'):
    p=Path(token);inputs.append(p if p.is_absolute() else build/p)
   elif token in ['-latomic','-lc++','-l:libunwind.a']:
    name={'-latomic':'libatomic.a','-lc++':'libc++.a','-l:libunwind.a':'libunwind.a'}[token];p=locate(name);inputs.append(p)
    if name=='libc++.a':inputs += [locate('libc++_static.a'),locate('libc++abi.a')]
  rows=[]
  for p in sorted(set(inputs)):
   project=p.is_relative_to(ROOT)
   # Link inputs include archives with garbage-collected members, not proof every member survives.
   rows.append({**file(p,'static-link-input'),'license':'MIT' if project and 'llama/' in str(p) else ('Apache-2.0' if project else 'LicenseRef-NDK-aggregate'),'notice': 'PROJECT/android/app/src/main/assets/licenses/llama.cpp.txt' if project and 'llama/' in str(p) else ('PROJECT/THIRD_PARTY_NOTICES' if project else 'TOOLCHAIN/android-ndk-r27c/NOTICE.toolchain')})
  llvm=TC/'android-ndk-r27c/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf'
  elf=subprocess.run([str(llvm),'-d',str(build/'libpocketlore.so')],capture_output=True,text=True,check=True).stdout;(out/('elf-'+abi+'.txt')).write_text(elf)
  inv['native'].append({'abi':abi,'packaged_library':file(ROOT/'android/app/build/generated/nativeLibs'/abi/'libpocketlore.so','packaged-native-library'),'llama_revision':'bb4caa7540188872173c44d161602d9271386413','link_command':file(link,'link-command'),'inputs':rows,'elf_needed':re.findall(r'Shared library: \[(.*?)\]',elf),'caveat':'Static archives are actual link inputs; --gc-sections can discard members. Platform shared libraries are not bundled.'})
 for r in json.loads((out/'resolved.json').read_text()):
  p=Path(r['artifact']);licenses,descriptors=pom(r['coordinate'])
  inv['resolved_build_dependencies'].append({'coordinate':r['coordinate'],'configuration':r['configuration'],'project':r['project'],'artifact':file(p,'build-only-dependency'),'declared_licenses':licenses,'pom_chain':descriptors,'embedded_notices':embedded(p),'terms_status':'declared; not a redistribution clearance' if licenses else 'missing local POM license declaration'})
 tools=[
 ('JDK',TC/'jdk',[TC/'jdk/bin/java',TC/'jdk/release',TC/'jdk/NOTICE',*sorted((TC/'jdk/legal').rglob('*'))]),
 ('Gradle 8.13',TC/'gradle-8.13',[TC/'gradle-8.13/LICENSE',TC/'gradle-8.13/NOTICE',*sorted((TC/'gradle-8.13/lib').rglob('*.jar'))]),
 ('NDK r27c',TC/'android-ndk-r27c',[TC/'android-ndk-r27c/source.properties',TC/'android-ndk-r27c/NOTICE',TC/'android-ndk-r27c/NOTICE.toolchain',TC/'android-ndk-r27c/toolchains/llvm/prebuilt/linux-x86_64/bin/clang',TC/'android-ndk-r27c/toolchains/llvm/prebuilt/linux-x86_64/sysroot/NOTICE']),
 ('CMake 3.22.1',TC/'cmake-3.22.1',[TC/'cmake-3.22.1/bin/cmake',TC/'cmake-3.22.1/bin/ninja',*sorted((TC/'cmake-3.22.1/doc').rglob('*'))])]
 for name,base,files in tools:
  chosen=[p for p in files if p.is_file() and (p in files[:4] or p.suffix=='.jar' or any(x in p.name.lower() for x in ['notice','license','copyright']) or 'jdk/legal' in str(p))]
  inv['toolchain'].append({'name':name,'scope':'installed build tools; not bundled wholesale','files':[file(p,'installed-tool-or-notice') for p in dict.fromkeys(chosen)]})
 for rel in ['sdk/build-tools/35.0.0','sdk/platforms/android-35','sdk/platform-tools','sdk/cmdline-tools/latest','sdk/emulator','sdk/system-images/android-35/default/x86_64']:
  base=TC/rel
  selected=[p for p in base.rglob('*') if p.is_file() and p.name in ['source.properties','package.xml','NOTICE.txt','NOTICE.csv','LICENSE','android.jar','adb','aapt2','apksigner','zipalign','d8','emulator']]
  inv['toolchain'].append({'name':rel,'scope':'installed SDK/build or emulator validation tool; not bundled wholesale','files':[file(p,'installed-tool-or-notice') for p in sorted(selected)]})
 modeldefs=[
 ('SmolLM2-135M','downloads/runtime/SmolLM2-135M-Instruct-Q3_K_M.gguf','32db44d69cedb731dc0fc96f60e01a86c6f5919d','smoke-model-Apache-2.0.txt'),
 ('Qwen2.5-0.5B','downloads/answers/model/qwen2.5-0.5b-instruct-q4_k_m.gguf','9217f5db79a29953eb74d5343926648285ec7e67','qwen2.5-Apache-2.0.txt'),
 ('Qwen2.5-1.5B','downloads/synthesis/model/qwen2.5-1.5b-instruct-q4_k_m.gguf','91cad51170dc346986eccefdc2dd33a9da36ead9','synthesis-model-Apache-2.0.txt'),
 ('Qwen3-1.7B','downloads/synthesis/model/Qwen3-1.7B-Q8_0.gguf','90862c4b9d2787eaed51d12237eafdfe7c5f6077','synthesis-qwen3-Apache-2.0.txt')]
 for name,rel,revision,notice in modeldefs:inv['models'].append({'name':name,'revision':revision,'artifact':file(ROOT/rel,'optional-not-bundled-model'),'license':'Apache-2.0 as declared by publisher','license_file':file(ROOT/'android/app/src/main/assets/licenses'/notice,'model-license'),'limitation':'Publisher quantization; not independently reproduced'})
 for rel in ['android/knowledge-sources.json','tools/packs/sources.lock.json','tools/packs/science-sources.lock.json','tools/packs/regional-sources.lock.json']:
  inv['data'].append({'source_lock':file(ROOT/rel,'licensed-source-lock'),'provenance':json.loads((ROOT/rel).read_text())})
 for rel in ['downloads/packs/english-reference.plpack','downloads/science/science-supplement-2026-10-01-v1.plpack']:
  p=ROOT/rel
  with zipfile.ZipFile(p) as z:m=json.loads(z.read('manifest.json'))
  inv['data'].append({'artifact':file(p,'optional-not-bundled-pack'),'manifest':m})
 for t in inv['toolchain']:
  t['version_metadata']={}
  for f in t['files']:
   if Path(f['path']).name in ['release','source.properties']:
    t['version_metadata'][f['path']]=resolve(f['path']).read_text()
 inv['host_build_utilities']=[]
 for name in ['python3','make','bash']:
  p=Path('/usr/bin')/name
  version=subprocess.run([str(p),'--version'],capture_output=True,text=True,check=True).stdout.splitlines()[0]
  inv['host_build_utilities'].append({'name':name,'version':version,'artifact':file(p,'host-build-utility'),'license_status':'Host OS license/dependency closure not audited; not bundled.'})
 for model in inv['models']:
  repo={'SmolLM2-135M':'tensorblock/SmolLM2-135M-Instruct-GGUF','Qwen2.5-0.5B':'Qwen/Qwen2.5-0.5B-Instruct-GGUF','Qwen2.5-1.5B':'Qwen/Qwen2.5-1.5B-Instruct-GGUF','Qwen3-1.7B':'Qwen/Qwen3-1.7B-GGUF'}[model['name']]
  model['deployment_role']='production/demo, imported separately' if model['name']=='Qwen2.5-0.5B' else 'optional evaluated or smoke candidate, not deployed'
  model['source_repository']='https://huggingface.co/'+repo
  model['pinned_url']=model['source_repository']+'/resolve/'+model['revision']+'/'+Path(model['artifact']['path']).name
 inv['build_recipe']=[file(ROOT/rel,'build-recipe') for rel in ['tools/android-build.sh','tools/runtime/build-native.sh','tools/runtime/pins.env','tools/release/finalize_apk.py','tools/distribution/native-notices.lock.json','android/build.gradle','android/app/build.gradle','android/app/src/main/cpp/CMakeLists.txt']]
 inv['required_notices']=[file(ROOT/'android/app/src/main/assets/licenses/llama.cpp.txt','required-notice'),*[file(TC/n['toolchain_path'],'required-notice') for n in required]]
 missing=[r['coordinate'] for r in inv['resolved_build_dependencies'] if not r['declared_licenses']]
 no_notice=[r['coordinate'] for r in inv['resolved_build_dependencies'] if not r['embedded_notices']]
 inv['gaps']=[{'id':'build-tool-full-notice-review','status':'open for redistribution of tools only','components_without_embedded_plain_notice':no_notice,'next':'POM declarations are recorded; a missing embedded notice is not a finding that no license exists. Collect/review full component notices if distributing these build-only jars; they are not APK dependencies.'},{'id':'build-dependency-license-declarations','components':missing,'status':'open' if missing else 'locally declared','next':'Resolve remaining parent POM or upstream terms before redistributing build-tool artifacts; do not infer permission from hashes.'},
 {'id':'toolchain-redistribution','status':'open','next':'Installed aggregate notices are inventoried, but SDK terms and per-component alternatives must be reviewed for any toolchain bundle; no such bundle is authorized or produced.'},
 {'id':'independent-reproduction','status':'external','next':'Separate provisioned machine/operator must reproduce the candidate; same-rig capture is not independent.'},
 {'id':'production-signing','status':'owner decision','next':'Owner selects key custody, signing and publication policy; no production key generated or read.'}]
 return inv
if __name__=='__main__':
 inventory=capture();p=ROOT/'docs/distribution-inventory.json';p.write_text(json.dumps(inventory,indent=2)+'\n');print(p)
