#!/usr/bin/env python3
"""Rebuild pinned science text and exercise actual Android retrieval/import/inspection."""
from pathlib import Path
import datetime,json,sys,hashlib,subprocess,os,zipfile,copy,shutil
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/packs'))
from build_science import build,LOCK
from build_pack import sha

def main():
    out=ROOT/'downloads/science'/datetime.datetime.now(datetime.timezone.utc).strftime('run-%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True);print(out,flush=True)
    def run(args,name,input=None):
        p=subprocess.run(list(map(str,args)),input=input,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180);(out/name).write_bytes(p.stdout)
        if p.returncode:raise RuntimeError('Command failed: '+str(out/name))
        return p.stdout
    fixture=ROOT/'tools/evaluation/science-supplement/cases.json';assert sha(fixture.read_bytes())=='d775afe09a6e64e565872894d4510e264ebd49de5c156629aeae71693f595198';spec=json.loads(fixture.read_text());assert sha(LOCK.read_bytes())==spec['source_lock_sha256']
    pack,m=build(output=out/'valid.plpack');repeat,_=build(output=out/'repeat.plpack');assert pack.read_bytes()==repeat.read_bytes()
    assert len(m['documents'])>=8 and len({d['category'] for d in m['documents']})>=3 and m['passage_count']==24
    (out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');shutil.copyfile(fixture,out/'cases.json')
    with zipfile.ZipFile(pack) as z:files={n:z.read(n) for n in z.namelist()}
    def corrupt(name,contents):
        with zipfile.ZipFile(out/name,'w') as z:
            for n,v in contents.items():z.writestr(n,v)
    bad=dict(files);bad['passages.tsv']=bad['passages.tsv'].replace(b'earthquake',b'earthquack',1);assert bad['passages.tsv']!=files['passages.tsv'];corrupt('bitflip.plpack',bad)
    for name,change in [('rights.plpack',lambda d:d['documents'][0].update(license='')),('source-hash.plpack',lambda d:d['documents'][0]['passages'][0].update(sha256='0'*64))]:
        doc=copy.deepcopy(m);change(doc);bad=dict(files);bad['manifest.json']=json.dumps(doc).encode();corrupt(name,bad)
    tc=Path(os.environ.get('POCKETLORE_TOOLCHAIN','/home/isa/Android/atlas-toolchain'));adb=[tc/'sdk/platform-tools/adb','-s','emulator-5560']
    assert run(adb+['shell','getprop','sys.boot_completed'],'boot.txt').strip()==b'1'
    run(adb+['shell','getprop','ro.build.fingerprint'],'fingerprint.txt');before=run(adb+['shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf','files/knowledge.plpack'],'saved-before.txt')
    run(['bash',ROOT/'tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',ROOT/'tools/evaluation/science-supplement/source.gradle','-PpocketloreTestRunner=org.pocketlore.app.ScienceInstrumentation'],'build.log')
    artifacts={}
    for path in ['debug/app-debug.apk','androidTest/debug/app-debug-androidTest.apk']:
        apk=ROOT/'android/app/build/outputs/apk'/path;artifacts[apk.name]={'sha256':sha(apk.read_bytes()),'bytes':apk.stat().st_size};shutil.copyfile(apk,out/apk.name);run(adb+['install','-r',apk],'install-'+apk.name+'.txt')
    run(adb+['shell','am','force-stop','org.pocketlore.app'],'stop.txt');run(adb+['shell','run-as','org.pocketlore.app','mkdir','-p','files/science-tests'],'mkdir.txt')
    for p in [out/'cases.json',pack,*[out/n for n in ['bitflip.plpack','rights.plpack','source-hash.plpack']]]:run(adb+['shell','run-as','org.pocketlore.app','sh','-c',"'cat > files/science-tests/"+p.name+"'"],'provision-'+p.name+'.txt',p.read_bytes())
    run(adb+['shell','run-as','org.pocketlore.app','rm','-f','files/science-tests/results.json'],'clear-results.txt')
    log=run(adb+['shell','am','instrument','-w','org.pocketlore.app.test/org.pocketlore.app.ScienceInstrumentation'],'instrumentation.txt')
    raw=run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/science-tests/results.json'],'results.json');r=json.loads(raw)
    after=run(adb+['shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf','files/knowledge.plpack'],'saved-after.txt');assert before==after,'Original saved assets changed'
    assert b'INSTRUMENTATION_CODE: -1' in log and r['status']=='PASS',str(out/'results.json')
    assert r['pack_sha256']==sha(pack.read_bytes()) and r['pack_id']==m['id'] and len(r['retrieval'])==12
    assert {c['id']:c['question'] for c in r['retrieval']}=={c['id']:c['question'] for c in spec['cases']}
    assert all(c['found_required'] if c['expected']=='present' else c['without_model_route']=='ABSTAINED' for c in r['retrieval'])
    assert len(r['corruption'])==3 and r['activity_import'] and r['activity_corrupt_rejected'] and r['original_library_restored'] and r['staging_cleanup']
    run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/science-tests/source-dialog.png'],'source-dialog.png')
    summary={'status':'PASS','scope':'Builder-authored public retrieval and emulator import/source UI, not generated-answer or physical acceptance','pack_sha256':sha(pack.read_bytes()),'pack_bytes':pack.stat().st_size,'documents':len(m['documents']),'passages':m['passage_count'],'topics':sorted({d['category'] for d in m['documents']}),'supported_top4':sum(c['found_required'] for c in r['retrieval']),'absent_blocked':sum(c['without_model_route']=='ABSTAINED' for c in r['retrieval'] if c['expected']=='absent'),'artifacts':artifacts,'fixture_sha256':sha(fixture.read_bytes()),'results_sha256':sha(raw)}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
