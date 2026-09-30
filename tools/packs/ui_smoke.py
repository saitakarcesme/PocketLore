#!/usr/bin/env python3
"""Exercise Android's document picker, pack replacement, restart and source UI."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import xml.etree.ElementTree as ET
p=argparse.ArgumentParser();p.add_argument('--adb',required=True);p.add_argument('--serial',required=True);p.add_argument('--pack',type=Path,required=True);p.add_argument('--bad',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
assert a.serial.startswith('emulator-'),'This smoke is labeled emulator-only'
counter=0

def adb(*args):return subprocess.check_output([a.adb,'-s',a.serial,*args],text=True)
def tree():
 global counter
 adb('shell','uiautomator','dump','/sdcard/pocketlore-pack-ui.xml');xml=adb('shell','cat','/sdcard/pocketlore-pack-ui.xml');counter+=1;(a.out/f'{counter:03}.xml').write_text(xml);return ET.fromstring(xml)
def find(t,label):return next((n for n in t.iter('node') if n.get('text','').casefold()==label.casefold() or n.get('content-desc')==label),None)
def tap(n):
 assert n is not None,'Missing UI target'
 x1,y1,x2,y2=map(int,re.findall(r'\d+',n.get('bounds')));assert x2>x1 and y2>y1;adb('shell','input','tap',str((x1+x2)//2),str((y1+y2)//2))
def wait(fragment):
 for _ in range(20):
  t=tree()
  if fragment.casefold() in ET.tostring(t,encoding='unicode').casefold():return t
  time.sleep(.2)
 raise AssertionError('UI text absent: '+fragment)
def launch():
 adb('shell','am','force-stop','org.pocketlore.app');adb('shell','am','start','-n','org.pocketlore.app/.MainActivity');time.sleep(.7)
def pick(name):
 t=wait('Import knowledge pack');n=find(t,'Import knowledge pack')
 for _ in range(20):
  if n is not None and n.get('enabled')=='true':break
  time.sleep(.2);n=find(tree(),'Import knowledge pack')
 tap(n);t=tree();roots=find(t,'Show roots')
 if roots is not None:tap(roots)
 t=tree();matches=[n for n in t.iter('node') if n.get('text')=='Downloads']
 if matches:tap(matches[-1])
 tap(find(tree(),name))
def installed_hash():return adb('shell','run-as','org.pocketlore.app','sha256sum','files/knowledge.plpack').split()[0]
for path,name in [(a.pack,'pocketlore-reference.plpack'),(a.bad,'pocketlore-corrupt.plpack')]:adb('push',str(path),'/sdcard/Download/'+name)
launch();pick('pocketlore-reference.plpack');wait('186 passages');expected=hashlib.sha256(a.pack.read_bytes()).hexdigest();assert installed_hash()==expected
launch();t=wait('186 passages');assert expected in ET.tostring(t,encoding='unicode')
pick('pocketlore-corrupt.plpack');wait('Pack rejected; previous library retained.');assert installed_hash()==expected
launch();t=wait('186 passages');tap(find(t,'Research question'));adb('shell','input','text','Yosemite');adb('shell','input','keyevent','4');tap(find(tree(),'Answer offline'))
source=None
for _ in range(16):
 t=tree();source=next((n for n in t.iter('node') if n.get('text','').startswith('Inspect [yosemite-')),None)
 if source is not None:break
 adb('shell','input','swipe','520','1600','520','650','250')
assert source is not None,'Imported pack not used by answer flow';tap(source);t=tree();alltext=ET.tostring(t,encoding='unicode')
assert 'https://www.nps.gov/yose/' in alltext and 'National Park Service' in alltext and '2025-07-17' in alltext,alltext
(a.out/'source-dialog.png').write_bytes(subprocess.check_output([a.adb,'-s',a.serial,'exec-out','screencap','-p']))
result={'result':'PASS','environment':'AOSP x86_64 emulator; not physical hardware','pack_sha256':expected,'checks':['SAF pack selection and import','persisted pack reload after process restart','corrupted import rejected with saved hash unchanged','retrieval and source inspection use imported NPS provenance']}
(a.out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
