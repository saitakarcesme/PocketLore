#!/usr/bin/env python3
"""Real emulator UI: SAF selection, import confirmation, restart, and source dialog."""
import argparse, hashlib, json, pathlib, re, subprocess, time, xml.etree.ElementTree as ET
p=argparse.ArgumentParser();p.add_argument('--adb',required=True);p.add_argument('--serial',required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--model',type=pathlib.Path,required=True);p.add_argument('--import-only',action='store_true');a=p.parse_args()
assert a.serial.startswith('emulator-')
a.out.mkdir(parents=True,exist_ok=True)
count=0

def adb(*args,binary=False):
    return subprocess.check_output([a.adb,'-s',a.serial,*args],text=not binary)
def tree(label):
    global count
    adb('shell','uiautomator','dump','/sdcard/pocketlore-answer-ui.xml')
    value=adb('shell','cat','/sdcard/pocketlore-answer-ui.xml');count+=1
    (a.out/f'{count:03d}-{label}.xml').write_text(value)
    return ET.fromstring(value)
def find(t,label):
    return next((n for n in t.iter('node') if n.get('text','').casefold()==label.casefold() or n.get('content-desc','')==label),None)
def tap(n):
    assert n is not None
    x1,y1,x2,y2=map(int,re.findall(r'\d+',n.get('bounds')))
    assert x2>x1 and y2>y1
    adb('shell','input','tap',str((x1+x2)//2),str((y1+y2)//2))
def scroll_to(label):
    for _ in range(12):
        t=tree('scroll');n=find(t,label)
        if n is not None:return n
        dims=list(map(int,re.findall(r'\d+',adb('shell','wm','size').splitlines()[-1])))
        w,h=dims[-2:];adb('shell','input','swipe',str(w//2),str(h*4//5),str(w//2),str(h//3),'250')
    raise AssertionError('UI control not found: '+label)
def wait_text(fragment,label):
    for _ in range(15):
        t=tree(label)
        if any(fragment in n.get('text','') for n in t.iter('node')):return t
        time.sleep(.2)
    raise AssertionError('UI text not found: '+fragment)
def launch():
    adb('shell','am','force-stop','org.pocketlore.app');adb('shell','am','start','-n','org.pocketlore.app/.MainActivity')
    time.sleep(.5)

def screenshot(name):
    (a.out/(name+'.png')).write_bytes(adb('exec-out','screencap','-p',binary=True))

checks=[]
adb('push',str(a.model),'/sdcard/Download/pocketlore-runtime-smoke.gguf')
launch();tap(scroll_to('Import local GGUF'))
t=tree('picker');roots=find(t,'Show roots')
if roots is not None:tap(roots)
t=tree('roots');matches=[n for n in t.iter('node') if n.get('text')=='Downloads'];assert matches;tap(matches[-1])
tap(scroll_to('pocketlore-runtime-smoke.gguf'))
t=wait_text('Required additional storage:','confirm');assert str(a.model.stat().st_size) in ET.tostring(t,encoding='unicode');screenshot('import-confirmation')
tap(find(t,'Import'));wait_text('Local model ready','imported')
checks.append('local SAF import and explicit copy-size confirmation')
expected=hashlib.sha256(a.model.read_bytes()).hexdigest()
actual=adb('shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf').split()[0]
assert actual==expected,(actual,expected)
checks.append('imported model hash matches pinned GGUF');screenshot('imported')
launch();scroll_to('Import local GGUF');wait_text('Local model ready','reloaded');checks.append('saved model reload after process restart');screenshot('reloaded')
if a.import_only:
    result={'status':'pass','environment':'emulator only; SAF import/restart, no answer quality claim','model_sha256':actual,'checks':checks}
    (a.out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));raise SystemExit(0)
# Actual normal question UI and source dialog after the restored model.
launch();t=tree('query');tap(find(t,'Research question'));adb('shell','input','text','Compare%sevaporation%sand%scondensation');adb('shell','input','keyevent','4')
tap(find(tree('query-filled'),'Answer offline'))
# The question's source links must remain available regardless of generation acceptance.
source=None
for _ in range(12):
    t=tree('answer-sources')
    source=next((n for n in t.iter('node') if n.get('text','').startswith('Inspect [water-02]')),None)
    if source is not None:break
    dims=list(map(int,re.findall(r'\d+',adb('shell','wm','size').splitlines()[-1])));w,h=dims[-2:]
    adb('shell','input','swipe',str(w//2),str(h*4//5),str(w//2),str(h//3),'250')
assert source is not None,'Source button missing';tap(source)
t=tree('source-dialog');text='\n'.join(n.get('text','') for n in t.iter('node'))
assert 'https://www.usgs.gov/' in text and 'verbatim USGS paragraph' in text,text
checks.append('source provenance dialog from live answer flow');screenshot('source-dialog')
result={'status':'pass','environment':'emulator only','model_sha256':actual,'checks':checks}
(a.out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
