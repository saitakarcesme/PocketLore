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
expected=json.loads(fixture.read_text());pin=json.loads((ROOT/'tools/evaluation/synthesis-model.json').read_text());expected['model_sha256']=pin['sha256'];run_fixture=OUT/'cases.json';run_fixture.write_text(json.dumps(expected));pack=ROOT/'downloads/packs/english-reference.plpack'
assert hashlib.sha256(pack.read_bytes()).hexdigest()==expected['pack_sha256']
tc=Path(os.environ.get('POCKETLORE_TOOLCHAIN','/home/isa/Android/atlas-toolchain'));adb=[tc/'sdk/platform-tools/adb','-s',os.environ.get('ANDROID_SERIAL','emulator-5560')]
assert str(adb[2]).startswith('emulator-')
assert run(adb+['shell','getprop','sys.boot_completed']).strip()==b'1'
(OUT/'environment.txt').write_bytes(run(adb+['shell','getprop','ro.build.fingerprint'])+run(adb+['shell','getprop','ro.product.cpu.abi'])+run(adb+['shell','cat','/proc/meminfo']))
host=OUT/'host';host.mkdir()
src=ROOT/'android/app/src/main/java/org/pocketlore/app';tests=ROOT/'android/app/src/test/java/org/pocketlore/app'
run([tc/'jdk/bin/javac','-d',host,*[src/(n+'.java') for n in ['ResearchEngine','EvidencePrompt','AnswerEngine','NativeRuntime']],tests/'SynthesisCheck.java',tests/'AnswerEngineCheck.java'])
(OUT/'host-contract.txt').write_bytes(run([tc/'jdk/bin/java','-cp',host,'org.pocketlore.app.SynthesisCheck']))
(OUT/'answer-regression.txt').write_bytes(run([tc/'jdk/bin/java','-cp',host,'org.pocketlore.app.AnswerEngineCheck',ROOT/'android/app/src/main/assets/water-science.tsv']))
(OUT/'build.log').write_bytes(run(['bash',ROOT/'tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-PpocketloreTestRunner=org.pocketlore.app.SynthesisInstrumentation']))
for apk in [ROOT/'android/app/build/outputs/apk/debug/app-debug.apk',ROOT/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk']:run(adb+['install','-r',apk])
run(adb+['shell','am','force-stop','org.pocketlore.app'])
run(adb+['shell','run-as','org.pocketlore.app','mkdir','-p','files/synthesis-tests'])
for name,path in [('cases.json',run_fixture),('reference.plpack',pack)]:run(adb+['shell','run-as','org.pocketlore.app','sh','-c',"'cat > files/synthesis-tests/"+name+"'"],input=path.read_bytes())
model=ROOT/'downloads/synthesis/model'/pin['filename']
with model.open('rb') as stream:
 h=hashlib.file_digest(stream,'sha256').hexdigest()
assert h==pin['sha256']
saved=run(adb+['shell','run-as','org.pocketlore.app','sh','-c',"'sha256sum files/synthesis-tests/model.gguf 2>/dev/null || true'"]).decode().split()
if not saved or saved[0]!=pin['sha256']:
 with model.open('rb') as stream:run(adb+['shell','run-as','org.pocketlore.app','sh','-c',"'cat > files/synthesis-tests/model.gguf'"],stdin=stream)
result=run(adb+['shell','am','instrument' ,'-w','org.pocketlore.app.test/org.pocketlore.app.SynthesisInstrumentation']);(OUT/'instrumentation.txt').write_bytes(result)
assert b'INSTRUMENTATION_CODE: -1' in result,result.decode()
raw=run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/synthesis-tests/results.json']);(OUT/'results.json').write_bytes(raw);report=json.loads(raw)
checks={}
checks['case_identity']=len(report['cases'])==len(expected['cases'])+1 and {r['id']:r['question'] for r in report['cases'] if r['id']!='conflict-fixture'}=={r['id']:r['question'] for r in expected['cases']}
checks['model_identity']=report.get('model_sha256')==pin['sha256']
checks['pack_identity']=report.get('pack_sha256')==expected['pack_sha256']
for row in report['cases']:
 absent=row['id']=='absent';conflict=row['id']=='conflict-fixture';checks[row['id']+'_route']=row['kind'] in (['ABSTAINED'] if absent else ['GENERATED','FALLBACK'] if conflict else ['GENERATED'])
 checks[row['id']+'_budget']=row['prompt_tokens']+row['tokens']<=2048
 if not absent and not conflict:
  ids=set(re.findall(r'\[([^\[\]]+)\]',row['text']));allowed={p['id'] for p in row['sources']}
  checks[row['id']+'_citations']=row['kind']=='GENERATED' and bool(ids) and ids<=allowed
  if row['id'] in ('comparison','synthesis'):checks[row['id']+'_multiple_sources']=row['kind']=='GENERATED' and len(ids)>=2
# Development meaning checks are deliberately separate from citation syntax.
# They test key relations, not whole-answer exact strings or canned responses.
for row in report['cases']:
 text=re.sub(r'\[[^\]]+\]','',row['text']).lower(); kind=row['kind']=='GENERATED'
 if row['id']=='comparison':
  checks['comparison_no_cooling_transfer']=not bool(re.search(r'evaporation occurs(?:(?!condensation)[^.])*cooled',text))
  checks['comparison_phase_directions']=kind and bool(re.search(r'evaporat[^.]*liquid[^.]*vapo[ur]',text)) and bool(re.search(r'condens[^.]*vapo[ur][^.]*liquid',text))
 elif row['id']=='explanation':checks['explanation_heat_removal']=kind and 'heat' in text and bool(re.search(r'remov|cool|los',text))
 elif row['id']=='synthesis':
  checks['synthesis_no_destination_transfer']=not bool(re.search(r'runoff[^.]*lakes',text)) or 'lakes' in row['prompt'].split('[S2]',1)[-1].split('Question:',1)[0].lower()
  checks['synthesis_no_recharge_well_transfer']=not bool(re.search(r'runoff[^.]*recharge wells',text))
  checks['synthesis_both_processes']=kind and bool(re.search(r'groundwater|aquifer',text)) and 'runoff' in text and bool(re.search(r'infiltrat|recharg',text))
 elif row['id']=='conditions':checks['conditions_scope_qualifiers']=kind and 'deep' in text and 'shallow' in text and bool(re.search(r'centur|slow',text)) and bool(re.search(r'immediat|quick',text))
checks['conflict_fixture_safe_disclosure']=any(r['id']=='conflict-fixture' and r['kind'] in ('GENERATED','FALLBACK') and bool(re.search(r'disagree|conflict|unresolved|contradict',r['text'],re.I)) and {'fixture-a','fixture-b'}<=set(re.findall(r'\[([^\[\]]+)\]',r['text'])) for r in report['cases'])
checks['native_budget_and_cancel']=report.get('native_budget_and_cancel_checks') is True
checks['generated_claim_links']=all(r.get('claim_links_checked',0)>0 for r in report['cases'] if r['kind']=='GENERATED')
summary={'status' :'PASS' if all(checks.values()) else 'FAIL','checks':checks,'scope':'Real generation, context and citation structure; source entailment requires recorded claim review','apk_sha256':hashlib.sha256((ROOT/'android/app/build/outputs/apk/debug/app-debug.apk').read_bytes()).hexdigest()}
summary['results_sha256']=hashlib.sha256(raw).hexdigest()
summary['fixture_sha256']=hashlib.sha256(fixture.read_bytes()).hexdigest()
summary['test_apk_sha256']=hashlib.sha256((ROOT/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk').read_bytes()).hexdigest()
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(OUT);print(json.dumps(summary,indent=2))
raise SystemExit(0 if summary['status']=='PASS' else 1)
