#!/usr/bin/env python3
"""Offline reproducibility + real Android production import corruption regression.
Requires existing emulator-5560, compatible toolchain and source cache. Never launches an emulator.
"""
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import time
import zipfile
from build_pack import ROOT, build, sha

def run(args, **kw):
    result=subprocess.run(list(map(str,args)),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,**kw)
    if result.returncode:
        print(result.stdout.decode(errors="replace"),flush=True)
        result.check_returncode()
    return result.stdout

def main():
    start=time.monotonic();out=ROOT/'downloads/packs'/time.strftime('verify-%Y%m%dT%H%M%S');out.mkdir(parents=True)
    pack,m=build(output=out/'valid.plpack');other,_=build(output=out/'repeat.plpack')
    assert pack.read_bytes()==other.read_bytes(),'Non-reproducible build'
    assert {d['category'] for d in m['documents']}=={'science','history','practical','travel'}
    with zipfile.ZipFile(pack) as z: original={n:z.read(n) for n in z.namelist()}
    rejects=[]
    def case(name, files=None, raw=None):
        name+='.plpack'; rejects.append(name)
        if raw is not None:(out/name).write_bytes(raw);return
        with zipfile.ZipFile(out/name,'w',zipfile.ZIP_DEFLATED) as z:
            for n,b in (files or original).items():z.writestr(n,b)
    def altered(name, change, text=None):
        doc=copy.deepcopy(m);change(doc);files=dict(original)
        if text is not None:files['passages.tsv']=text;doc['passages_sha256']=sha(text)
        files['manifest.json']=json.dumps(doc).encode();case(name,files)
    case('bitflip',dict(original,**{'passages.tsv':original['passages.tsv'].replace(b'water',b'xxxxx',1)}))
    case('truncated',raw=pack.read_bytes()[:-12])
    damaged=bytearray(pack.read_bytes());damaged[-6:-2]=b'\xff'*4
    case('directory-offset',raw=bytes(damaged))
    case('missing-manifest',{'passages.tsv':original['passages.tsv']})
    case('zip-traversal',dict(original,**{'../escaped':'bad'}))
    case('decompression-limit',dict(original,**{'passages.tsv':b'x'*(16*1024*1024+1)}))
    case('bad-utf8',dict(original,**{'manifest.json':b'\xff'}))
    altered('schema',lambda d:d.update(schema=2))
    altered('fractional-schema',lambda d:d.update(schema=1.5))
    altered('language',lambda d:d.update(language='tr'))
    altered('count',lambda d:d.update(passage_count=1))
    altered('duplicate-document',lambda d:d['documents'].append(d['documents'][0]))
    altered('empty-rights',lambda d:d['documents'][0].update(license=''))
    altered('provenance',lambda d:d['documents'][0].update(url='https://example.com/wrong'))
    altered('citation',lambda d:d['documents'][0]['passages'][0].update(id='invented'))
    rows=original['passages.tsv'].decode().splitlines();fields=rows[0].split('\t');fields[5]+=' altered';rows[0]='\t'.join(fields)
    text=('\n'.join(rows)+'\n').encode()
    altered('rehashed-payload-wrong-passage',lambda d:None,text)
    text=original['passages.tsv'].splitlines(keepends=True)
    altered('duplicate-row',lambda d:None,b''.join([text[0]]+text[:-1]))
    # Duplicate names cannot be represented in a dictionary.
    with zipfile.ZipFile(out/'duplicate-entry.plpack','w') as z:
        for n,b in original.items():z.writestr(n,b)
        z.writestr('manifest.json',original['manifest.json'])
    rejects.append('duplicate-entry.plpack')
    (out/'cases.json').write_text(json.dumps({'rejects':rejects}))
    tc=Path(os.environ.get('POCKETLORE_TOOLCHAIN','/home/isa/Android/atlas-toolchain'))
    adb=[tc/'sdk/platform-tools/adb','-s',os.environ.get('ANDROID_SERIAL','emulator-5560')]
    assert run(adb+['shell','getprop','sys.boot_completed']).strip()==b'1','Existing emulator not booted'
    log=run(['bash',ROOT/'tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-PpocketloreTestRunner=org.pocketlore.app.PackSmokeInstrumentation']);(out/'build.log').write_bytes(log)
    apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk'
    test=ROOT/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk'
    for path in (apk,test):run(adb+['install','-r',path])
    run(adb+['shell','run-as','org.pocketlore.app','mkdir','-p','files/pack-tests'])
    for path in [pack,out/'cases.json']+[out/n for n in rejects]:
        run(adb+['shell','run-as','org.pocketlore.app','sh','-c',f"'cat > files/pack-tests/{path.name}'"],input=path.read_bytes())
    result=run(adb+['shell','am','instrument','-w','org.pocketlore.app.test/org.pocketlore.app.PackSmokeInstrumentation']);(out/'instrumentation.txt').write_bytes(result)
    assert b'INSTRUMENTATION_CODE: -1' in result and b'"passed": true' in result,result.decode()
    ui=run(['python3',ROOT/'tools/packs/ui_smoke.py','--adb',adb[0],'--serial',adb[2],'--pack',pack,'--bad',out/'bitflip.plpack','--out',out/'ui']);(out/'ui.log').write_bytes(ui)
    evidence={'pack_sha256':sha(pack.read_bytes()),'pack_bytes':pack.stat().st_size,'documents':len(m['documents']),'passages':m['passage_count'],'apk_sha256':sha(apk.read_bytes()),'test_apk_sha256':sha(test.read_bytes()),'elapsed_seconds':time.monotonic()-start,'corruption_cases':len(rejects),'environment':'LLMRig host build and existing x86_64 emulator; not physical Android','result':'PASS','source_acquisitions':[{'id':d['id'],'original_raw_sha256':d['raw_sha256'],'cached_raw_sha256':sha((ROOT/'downloads/packs/raw'/(d['id']+'.html')).read_bytes())} for d in m['documents']]}
    (out/'summary.json').write_text(json.dumps(evidence,indent=2)+'\n');print(json.dumps(evidence,indent=2));print(out)
if __name__=='__main__':main()
