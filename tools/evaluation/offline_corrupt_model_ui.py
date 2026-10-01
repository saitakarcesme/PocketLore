#!/usr/bin/env python3
"""SAF corrupt-model rejection and confirmation cancellation on the offline emulator."""
import argparse,json,re,subprocess,time,xml.etree.ElementTree as ET
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--adb',required=True);p.add_argument('--out',required=True,type=Path);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);count=0
base=[a.adb,'-s','emulator-5560']
def adb(*args):return subprocess.check_output(base+list(args),text=True)
def tree():
 global count
 adb('shell','uiautomator','dump','/sdcard/pocketlore-offline-ui.xml');xml=adb('shell','cat','/sdcard/pocketlore-offline-ui.xml');count+=1;(a.out/f'{count:03}.xml').write_text(xml);return ET.fromstring(xml)
def find(t,label):return next((n for n in t.iter('node') if n.get('text','').casefold()==label.casefold() or n.get('content-desc')==label),None)
def tap(n):
 assert n is not None,'Missing UI element';b=list(map(int,re.findall(r'\d+',n.get('bounds'))));assert b[2]>b[0] and b[3]>b[1];adb('shell','input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2))
def scroll(label):
 for _ in range(16):
  n=find(tree(),label)
  if n is not None:return n
  adb('shell','input','swipe','520','1650','520','600','250')
 raise AssertionError('Missing '+label)
def wait(fragment):
 for _ in range(30):
  t=tree()
  if fragment in ET.tostring(t,encoding='unicode'):return t
  time.sleep(.2)
 raise AssertionError('Missing text '+fragment)
def launch():
 adb('shell','am','force-stop','org.pocketlore.app');adb('shell','am','start','-n','org.pocketlore.app/.MainActivity');time.sleep(1);scroll('Import local GGUF');wait('Local model ready')
def pick():
 tap(scroll('Import local GGUF'));t=tree();n=find(t,'Show roots')
 if n is not None:tap(n)
 t=tree();options=[n for n in t.iter('node') if n.get('text')=='Downloads']
 if options:tap(options[-1])
 tap(scroll('pocketlore-offline-corrupt.gguf'));return wait('Required additional storage:')
def saved():return adb('shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf').split()[0]
source=a.out/'corrupt.gguf';source.write_bytes(b'BAD!test');adb('push',str(source),'/sdcard/Download/pocketlore-offline-corrupt.gguf');old=saved()
launch();tap(find(pick(),'Cancel'));assert saved()==old
launch();tap(find(pick(),'Import'));wait('Import failed: Not a GGUF file');assert saved()==old
status=adb('shell','run-as','org.pocketlore.app','sh','-c',"'test ! -e files/model.partial && echo no-stage'");assert status.strip()=='no-stage'
(a.out/'rejected.png').write_bytes(subprocess.check_output(base+['exec-out','screencap','-p']))
launch();assert saved()==old
r={'status':'PASS','checks':['model confirmation cancelled without replacement','corrupt GGUF rejected without replacement','stage removed','saved valid model reloads after rejection'],'retained_model_sha256':old};(a.out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
