#!/usr/bin/env python3
"""Check exact source extraction, deterministic bytes, and actual Android controls."""
import datetime,hashlib,json,math,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/packs'))
from build_travel import build,LOCK
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 out=ROOT/'downloads/regional'/datetime.datetime.now(datetime.timezone.utc).strftime('run-%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True);print(out,flush=True)
 def run(args,name,input=None):
  p=subprocess.run(list(map(str,args)),input=input,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=240);(out/name).write_bytes(p.stdout)
  if p.returncode:raise RuntimeError('Command failed: '+str(out/name))
  return p.stdout
 fixture=ROOT/'tools/evaluation/regional-poi/cases.json'
 assert sha(fixture.read_bytes())=='b52adce5df4f28138b6f1f33a3fe4c750c7c5933fb9a0809c3fa5065cb81a513'
 assert sha(LOCK.read_bytes())=='0d3105f89698d52746dc1edc6c777c74ddbb860c11e3beb2012867fedaaa9772'
 spec=json.loads(fixture.read_text());lock=json.loads(LOCK.read_text());sources={s['id']:s for s in lock['sources']}
 pack,manifest=build();raw=pack.read_bytes();assert build()[0].read_bytes()==raw
 assert len(sources)==25 and len(manifest['categories'])==4
 # Independent extraction checks against each original pinned entity and selected statement.
 for row in raw.decode().splitlines():
  v=row.split('\t');s=sources[v[0]];e=json.loads((ROOT/'downloads/regional/raw'/f"{v[0]}.json").read_bytes())['entities'][v[0]]
  assert v[1]==e['labels'][s['label_language']]['value'] and v[2]==e['descriptions']['en']['value']
  coord=next(c['mainsnak']['datavalue']['value'] for c in e['claims']['P625'] if c['id']==s['coordinate_claim'])
  assert [float(v[3]),float(v[4])]==[coord['latitude'],coord['longitude']]
  assert v[6]==str(e['lastrevid']) and v[7]==s['sha256'] and v[8]==s['url'] and v[9]=='CC0-1.0'
 tc=Path(os.environ.get('POCKETLORE_TOOLCHAIN','/home/isa/Android/atlas-toolchain'));adb=[tc/'sdk/platform-tools/adb','-s','emulator-5560']
 assert run(adb+['shell','getprop','sys.boot_completed'],'boot.txt').strip()==b'1'
 run(adb+['shell','getprop','ro.build.fingerprint'],'fingerprint.txt')
 before=run(adb+['shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf','files/knowledge.plpack'],'saved-before.txt')
 run(['bash',ROOT/'tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',ROOT/'tools/evaluation/regional-poi/source.gradle','-PpocketloreTestRunner=org.pocketlore.app.RegionalInstrumentation'],'build.log')
 assert raw==(ROOT/'android/app/src/main/assets/dc-monuments.tsv').read_bytes()
 assert manifest==json.loads((ROOT/'android/app/src/main/assets/dc-monuments-manifest.json').read_text())
 artifacts={}
 for sub in ['debug/app-debug.apk','androidTest/debug/app-debug-androidTest.apk']:
  apk=ROOT/'android/app/build/outputs/apk'/sub;artifacts[apk.name]={'sha256':sha(apk.read_bytes()),'bytes':apk.stat().st_size};shutil.copyfile(apk,out/apk.name);run(adb+['install','-r',apk],'install-'+apk.name+'.txt')
 run(adb+['shell','am','force-stop','org.pocketlore.app'],'stop.txt')
 run(adb+['shell','run-as','org.pocketlore.app','mkdir','-p','files/regional-tests'],'mkdir.txt')
 run(adb+['shell','run-as','org.pocketlore.app','sh','-c',"'cat > files/regional-tests/cases.json'"],'provision.txt',fixture.read_bytes())
 run(adb+['shell','run-as','org.pocketlore.app','rm','-f','files/regional-tests/results.json'],'clear.txt')
 log=run(adb+['shell','am','instrument','-w','org.pocketlore.app.test/org.pocketlore.app.RegionalInstrumentation'],'instrumentation.txt')
 result=run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/regional-tests/results.json'],'results.json');r=json.loads(result)
 after=run(adb+['shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf','files/knowledge.plpack'],'saved-after.txt');assert before==after
 assert b'INSTRUMENTATION_CODE: -1' in log and r['status']=='PASS',str(out/'results.json')
 assert len(r['sources'])==25 and {p['id'] for p in r['sources']}==set(sources)
 for p in r['sources']:
  s=sources[p['id']]
  assert p['name']==s['label'] and p['description']==s['description'] and p['category']==s['category']
  assert [p['lat'],p['lon']]==[s['latitude'],s['longitude']]
  assert p['revision']==str(s['revision']) and p['source_hash']==s['sha256'] and p['url']==s['url'] and p['coordinate_claim']==s['coordinate_claim']
 assert {c['id']:c['actual'] for c in r['filters']}=={c['id']:c['expected'] for c in spec['cases']}
 def distance(s):
  a=sources['Q178114'];lat1,lat2=map(math.radians,[a['latitude'],s['latitude']]);dl=math.radians(s['longitude']-a['longitude'])
  h=math.sin((lat2-lat1)/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin(dl/2)**2
  return 6371.0088*2*math.atan2(math.sqrt(h),math.sqrt(1-h))
 def expected(cat,yes='',no=''):
  candidates=[s for s in sources.values() if s['id']!='Q178114' and s['category']==cat and yes in (s['label']+' '+s['description']).lower() and (not no or no not in (s['label']+' '+s['description']).lower()) and distance(s)<=2]
  return [s['id'] for s in sorted(candidates,key=lambda s:(distance(s),s['id']))[:3]]
 for p in r['plans']:assert p['ids']==expected(p['category'])
 assert r['preferred_plan']['ids']==expected('museum','art museum','women')
 assert r['activity_plan']==r['preferred_plan']['text'] and r['activity_controls'] and r['rejected_controls']==7
 for p in [*r['plans'],r['preferred_plan']]:
  assert all('['+id+']' in p['text'] for id in p['ids'])
  assert all(t in p['text'] for t in ['Not a route','hours may be stale','Routing and walking times are unavailable'])
 run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/regional-tests/inspection.png'],'inspection.png')
 summary={'status':'PASS','environment':'API35 x86_64 emulator-5560; no physical device','edition':manifest,'pack_bytes':len(raw),'artifacts':artifacts,'filter_cases':len(r['filters']),'exact_provenance_rows':len(r['sources']),'results_sha256':sha(result),'fixture_sha256':sha(fixture.read_bytes()),'limitations':'Public literal filters and deterministic straight-line candidates; no inference, live availability, route or human usefulness acceptance'}
 (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
