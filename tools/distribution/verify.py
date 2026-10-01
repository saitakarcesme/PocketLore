#!/usr/bin/env python3
"""Validate frozen inventory against bytes and current resolution; mutate isolated copies."""
import copy,datetime,hashlib,json,shutil,sys,zipfile
from pathlib import Path
from inventory import ROOT,TC,sha,resolve,path
def files(node):
 if isinstance(node,dict):
  if set(['path','sha256','bytes','role'])<=set(node):yield node
  for value in node.values():yield from files(value)
 elif isinstance(node,list):
  for value in node:yield from files(value)
def verify(inv,overrides=None):
 overrides=overrides or {}
 if inv['distribution_ready'] is not False:raise ValueError('Unsupported distribution-ready claim')
 if not inv['gaps']:raise ValueError('Missing open owner/reproduction gates')
 if {n['abi'] for n in inv['native']}!={'arm64-v8a','x86_64'}:raise ValueError('Native ABI coverage')
 expected={'runtime.cpp.o','crtbegin_so.o','crtend_so.o','libllama.a','libggml.a','libggml-base.a','libggml-cpu.a','libatomic.a','libc++.a','libc++_static.a','libc++abi.a','libunwind.a'}
 for n in inv['native']:
  names={Path(x['path']).name for x in n['inputs']}
  if not expected<=names or not any(x.startswith('libclang_rt.builtins-') for x in names):raise ValueError('Native component coverage mismatch')
  if len(n['inputs'])!=13:raise ValueError('Unexpected native input count; review inventory schema')
 actual=json.loads((ROOT/'downloads/distribution/resolved.json').read_text())
 keys=lambda rows:{(r['coordinate'],r['project'],r['configuration'],r['artifact']['path']) for r in rows}
 normalized=[{**r,'artifact':{'path':path(r['artifact'])}} for r in actual]
 if keys(inv['resolved_build_dependencies'])!=keys(normalized):raise ValueError('Resolved dependency coverage mismatch')
 required={path(ROOT/'android/app/src/main/assets/licenses/llama.cpp.txt')}
 for n in json.loads((ROOT/'tools/distribution/native-notices.lock.json').read_text()):required.add(path(TC/n['toolchain_path']))
 if {r['path'] for r in inv['required_notices']}!=required:raise ValueError('Required notice coverage mismatch')
 seen=set()
 for r in [*inv['required_notices'],*files(inv)]:
  if r['path'] in seen:continue
  seen.add(r['path']);p=overrides.get(r['path'],resolve(r['path']))
  if not p.is_file():raise ValueError('Missing artifact/notice: '+r['path'])
  if p.stat().st_size!=r['bytes'] or sha(p)!=r['sha256']:raise ValueError('Artifact hash mismatch: '+r['path'])
 with zipfile.ZipFile(resolve(inv['apk']['path'])) as z:
  entries=[{'entry':n,'sha256':hashlib.sha256(z.read(n)).hexdigest(),'bytes':len(z.read(n))} for n in sorted(z.namelist()) if n.startswith(('lib/','assets/'))]
  if entries!=inv['apk_entries']:raise ValueError('APK payload/notice entries differ')
  for n in inv['native']:
   if hashlib.sha256(z.read('lib/'+n['abi']+'/libpocketlore.so')).hexdigest()!=n['packaged_library']['sha256']:raise ValueError('Native APK/source identity mismatch')
 return len(seen)
def main():
 out=ROOT/'downloads/distribution'/datetime.datetime.now(datetime.timezone.utc).strftime('verify-%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True)
 inv=json.loads((ROOT/'docs/distribution-inventory.json').read_text());count=verify(inv);results=[]
 def reject(name,modified,overrides=None):
  try:verify(modified,overrides)
  except ValueError as error:results.append({'case':name,'rejected':True,'reason':str(error)});return
  raise AssertionError('Mutation accepted: '+name)
 notice=inv['required_notices'][0];p=out/'notice-copy.txt';shutil.copyfile(resolve(notice['path']),p);p.unlink();reject('missing-notice',inv,{notice['path']:p})
 for name,record in [('changed-native-artifact',inv['native'][0]['packaged_library']),('changed-build-artifact',inv['resolved_build_dependencies'][0]['artifact'])]:
  p=out/(name+'.copy');shutil.copyfile(resolve(record['path']),p)
  with p.open('r+b') as f:b=f.read(1);f.seek(0);f.write(bytes([b[0]^1]))
  reject(name,inv,{record['path']:p})
 modified=copy.deepcopy(inv);modified['native'][0]['inputs'].pop(0);reject('missing-component',modified)
 modified=copy.deepcopy(inv);modified['distribution_ready']=True;reject('false-distribution-ready',modified)
 fixture=json.loads((ROOT/'tools/distribution/regressions.json').read_text());assert {x['case'] for x in results}=={x['id'] for x in fixture['cases']}
 result={'status':'PASS','distribution_ready':False,'verified_unique_files':count,'resolved_build_artifacts':len(inv['resolved_build_dependencies']),'native_link_inputs':{n['abi']:len(n['inputs']) for n in inv['native']},'inventory_sha256':sha(ROOT/'docs/distribution-inventory.json'),'apk_sha256':inv['apk']['sha256'],'regressions':results,'limits':inv['gaps']}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(out);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
