#!/usr/bin/env python3
"""Runs real JNI generation on the existing emulator; preserves failed output."""
from pathlib import Path
import datetime, hashlib, json, os, re, subprocess
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'downloads/synthesis'/datetime.datetime.now(datetime.timezone.utc).strftime('run-%Y%m%dT%H%M%SZ');OUT.mkdir(parents=True)
def run(args,**kw):
 p=subprocess.run(list(map(str,args)),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,**kw)
 if p.returncode:print(p.stdout.decode(errors='replace'));p.check_returncode()
 return p.stdout
fixture=ROOT/'tools/evaluation/synthesis-cases.json'
assert hashlib.sha256(fixture.read_bytes()).hexdigest()=='1eb30aa083e9f34be45b13ee09a67c7c7442d67a2ff81050b2d92b248450840e'
expected=json.loads(fixture.read_text());pack=ROOT/'downloads/packs/english-reference.plpack'
assert hashlib.sha256(pack.read_bytes()).hexdigest()==expected['pack_sha256']
tc=Path(os.environ.get('POCKETLORE_TOOLCHAIN','/home/isa/Android/atlas-toolchain'));adb=[tc/'sdk/platform-tools/adb','-s',os.environ.get('ANDROID_SERIAL','emulator-5560')]
assert str(adb[2]).startswith('emulator-')
assert run(adb+['shell','getprop','sys.boot_completed']).strip()==b'1'
(OUT/'build.log').write_bytes(run(['bash',ROOT/'tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-PpocketloreTestRunner=org.pocketlore.app.SynthesisInstrumentation']))
for apk in [ROOT/'android/app/build/outputs/apk/debug/app-debug.apk',ROOT/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk']:run(adb+['install','-r',apk])
run(adb+['shell','am','force-stop','org.pocketlore.app'])
run(adb+['shell','run-as','org.pocketlore.app','mkdir','-p','files/synthesis-tests'])
for name,path in [('cases.json',fixture),('reference.plpack',pack)]:run(adb+['shell','run-as','org.pocketlore.app','sh','-c',"'cat > files/synthesis-tests/"+name+"'"],input=path.read_bytes())
result=run(adb+['shell','am','instrument','-w','org.pocketlore.app.test/org.pocketlore.app.SynthesisInstrumentation']);(OUT/'instrumentation.txt').write_bytes(result)
assert b'INSTRUMENTATION_CODE: -1' in result,result.decode()
raw=run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/synthesis-tests/results.json']);(OUT/'results.json').write_bytes(raw);report=json.loads(raw)
checks={}
for row in report['cases']:
 absent=row['id']=='absent';checks[row['id']+'_route']=row['kind']==('ABSTAINED' if absent else 'GENERATED')
 checks[row['id']+'_budget']=row['prompt_tokens']+row['tokens']<=2048
 if not absent:
  ids=set(re.findall(r'\[([^\[\]]+)\]',row['text']));allowed={p['id'] for p in row['sources']}
  checks[row['id']+'_citations']=bool(ids) and ids<=allowed
  if row['id'] in ('comparison','synthesis'):checks[row['id']+'_multiple_sources']=len(ids)>=2
summary={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'scope':'Real generation, context and citation structure; source entailment requires recorded claim review','apk_sha256':hashlib.sha256((ROOT/'android/app/build/outputs/apk/debug/app-debug.apk').read_bytes()).hexdigest()}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(OUT);print(json.dumps(summary,indent=2))
raise SystemExit(0 if summary['status']=='PASS' else 1)
