#!/usr/bin/env python3
"""Use the real DocumentsUI picker to import one pinned release pack."""
import argparse,hashlib,json,pathlib,re,subprocess,time,xml.etree.ElementTree as ET
p=argparse.ArgumentParser();p.add_argument('--adb',required=True);p.add_argument('--serial',required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--pack',type=pathlib.Path,required=True);a=p.parse_args();assert a.serial=='emulator-5560';a.out.mkdir(parents=True,exist_ok=True)
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

digest=hashlib.sha256(a.pack.read_bytes()).hexdigest();name='release-'+a.pack.name
adb('push',str(a.pack),'/sdcard/Download/'+name)
launch();tap(scroll_to('Import knowledge pack'));t=tree('picker');roots=find(t,'Show roots')
if roots is not None:tap(roots)
matches=[n for n in tree('roots').iter('node') if n.get('text')=='Downloads'];assert matches;tap(matches[-1]);tap(scroll_to(name))
for _ in range(60):
    try:
        catalog=json.loads(adb('exec-out','run-as','org.pocketlore.app','cat','files/pack-library/catalog.json'))
        if any(e['sha256']==digest for e in catalog['collections']):break
    except (subprocess.CalledProcessError,json.JSONDecodeError):pass
    time.sleep(.3)
else:raise AssertionError('Imported pack not present in catalog')
actual=adb('shell','run-as','org.pocketlore.app','sha256sum','files/pack-library/'+digest+'.plpack').split()[0];assert actual==digest
screenshot('imported');(a.out/'result.json').write_text(json.dumps({'status':'PASS','method':'real DocumentsUI local SAF import','pack_sha256':digest,'catalog':catalog},indent=2)+'\n')
