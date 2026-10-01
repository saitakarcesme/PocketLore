#!/usr/bin/env python3
"""Exercise actual Android controls against the existing installed catalog; no fixture injection."""
import json,pathlib,re,subprocess,time,sys,xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parents[4];OUT=ROOT/'docs/evidence/research-brief/availability'
ADB='/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb'
def adb(*a):return subprocess.check_output([ADB,'-s','emulator-5560',*a],text=True)
def dump():
 adb('shell','uiautomator','dump','/sdcard/brief226-ui.xml');return adb('exec-out','cat','/sdcard/brief226-ui.xml')
def locate(attr,value):
 for attempt in range(12):
  xml=dump();direction="down" if value=="Research question" else "up"
  for n in ET.fromstring(xml).iter('node'):
   if n.get(attr)==value and n.get('enabled')=='true':
    x1,y1,x2,y2=map(int,re.findall(r'\d+',n.get('bounds')))
    if y1>100 and y2<2200:return ((x1+x2)//2,(y1+y2)//2)
    direction="down" if y1<=100 else "up"
  adb('shell','input','swipe','1000','1750' if direction=='up' else '750','1000','750' if direction=='up' else '1750','350')
 raise RuntimeError('Control unavailable: '+value)
def tap(p):adb('shell','input','tap',str(p[0]),str(p[1]))
cases=json.loads((ROOT/'tools/evaluation/research-brief/cases.json').read_text())
for id in (sys.argv[1:] or ['b22','b23','b24','b01']):
 # Return to the top before each question; imported data/model remain untouched.
 for _ in range(3):adb('shell','input','swipe','1000','650','1000','1900','300')
 c=next(c for c in cases if c['id']==id)
 tap(locate('content-desc','Research question'))
 adb('shell','input','keycombination','113','29')
 adb('shell','input','text',c['question'].replace(' ','%s'))
 adb('shell','input','keyevent','4')
 tap(locate('text','RESEARCH BRIEF · SOURCE QUOTATIONS'))
 xml=dump();(OUT/('ui-'+id+'.xml')).write_text(xml)
 answer=next(n.get('text') for n in ET.fromstring(xml).iter('node') if n.get('content-desc')=='Offline answer')
 assert c['question'] in answer,(id,'wrong question')
 if c['absent']:assert answer.startswith('Evidence unavailable') and 'No quotations selected.' in answer and 'Quote [' not in answer
 else:assert answer.startswith('Source-backed research brief') and 'two-step process' in answer
 print(id,'actual Activity control and output passed',flush=True)
