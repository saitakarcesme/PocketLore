#!/usr/bin/env python3
"""Real Android controls/source dialog after full simultaneous installation."""
import pathlib,subprocess,time,xml.etree.ElementTree as ET,re,json
ROOT=pathlib.Path(__file__).resolve().parents[3];OUT=ROOT/'docs/evidence/full-capacity/ui';ADB=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5562']
def sh(*args):return subprocess.check_output(ADB+['shell',*args],text=True)
def snapshot(name):
 sh('uiautomator','dump','/sdcard/capacity-ui.xml');xml=sh('cat','/sdcard/capacity-ui.xml');(OUT/(name+'.xml')).write_text(xml);return ET.fromstring(xml)
def tap(node):
 x1,y1,x2,y2=map(int,re.findall(r'\d+',node.attrib['bounds']));sh('input','tap',str((x1+x2)//2),str((y1+y2)//2))
def find(tree,predicate):return next(n for n in tree.iter('node') if predicate(n.attrib))
def wait_text(text,prefix,timeout=300,scroll=False):
 start=time.monotonic();i=0
 while time.monotonic()-start<timeout:
  tree=snapshot(prefix+'-'+str(i));i+=1
  if any(text.lower() in n.attrib.get('text','').lower() for n in tree.iter('node')):return tree
  if scroll and i%3==0:
   bounds=list(map(int,re.findall(r'\d+',next(tree.iter('node')).attrib['bounds'])));w,h=bounds[2],bounds[3];sh('input','swipe',str(w//2),str(h*4//5),str(w//2),str(h//3),'400')
  time.sleep(2)
 raise RuntimeError('UI timeout: '+text)
def main():
 OUT.mkdir(exist_ok=False)
 sh('am','force-stop','org.pocketlore.app');sh('am','start','-n','org.pocketlore.app/.MainActivity')
 tree=wait_text('Reference and world places','main');tap(find(tree,lambda a:a.get('text','').lower()=='reference and world places'))
 tree=wait_text('Search reference','start');tap(find(tree,lambda a:a.get('text')=='Reference topic'));sh('input','text','Acid');sh('input','keyevent','KEYCODE_BACK')
 tree=snapshot('entered');tap(find(tree,lambda a:a.get('text')=='SEARCH REFERENCE' or a.get('text')=='Search reference'))
 tree=wait_text('Acid ·','search',scroll=True);tap(find(tree,lambda a:a.get('text','').startswith('Acid ·')))
 tree=wait_text('Citation identity:','source')
 texts=[n.attrib.get('text','') for n in tree.iter('node')];source=next(t for t in texts if 'Citation identity:' in t)
 assert 'Source-specific rights:' in source and 'not cleared for generated answers' in source and 'Text SHA-256:' in source
 with (OUT/'source-dialog.png').open('wb') as f:subprocess.run(ADB+['exec-out','screencap','-p'],stdout=f,check=True)
 (OUT/'source.txt').write_text(source)
 (OUT/'source-process-memory.txt').write_text(sh('dumpsys','meminfo','org.pocketlore.app'))
 pid=sh('pidof','org.pocketlore.app').strip();assert pid.isdigit();(OUT/'proc-status.txt').write_text(sh('run-as','org.pocketlore.app','cat','/proc/'+pid+'/status'))
 tap(find(tree,lambda a:a.get('text','').lower()=='close'));tree=snapshot('closed')
 bounds=list(map(int,re.findall(r'\d+',next(tree.iter('node')).attrib['bounds'])));w,h=bounds[2],bounds[3]
 for _ in range(3):sh('input','swipe',str(w//2),str(h//3),str(w//2),str(h*4//5),'300')
 tree=snapshot('top-controls')
 tap(find(tree,lambda a:a.get('text','').lower()=='active bulk collections'));tree=wait_text('Complete sealed','collections')
 collection_nodes=[n for n in tree.iter('node') if n.attrib.get('checkable')=='true']
 assert len(collection_nodes)==2 and all(n.attrib.get('checked')=='true' for n in collection_nodes)
 with (OUT/'active-collections.png').open('wb') as f:subprocess.run(ADB+['exec-out','screencap','-p'],stdout=f,check=True)
 (OUT/'result.json').write_text(json.dumps({'status':'PASS','serial':'emulator-5562','real_controls':True,'actual_source_dialog':True,'active_collections':2,'generation':False},indent=2)+'\n')
if __name__=='__main__':main()
