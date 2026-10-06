#!/usr/bin/env python3
"""Isolated subprocess phase barrier; only constructed fixtures, never live output."""
import argparse,json,os,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import production as p
q=argparse.ArgumentParser();q.add_argument('--root',required=True);q.add_argument('--phase',required=True);q.add_argument('--tag',required=True);q.add_argument('--barrier',action='store_true');a=q.parse_args();root=Path(a.root)
args=argparse.Namespace(mode='short',stage=str(root/'stage.sqlite'),out=str(root/'out'),ceiling=1,follow=a.phase=='wait_source',seconds=30,cutoff=min(p.CUTOFF,time.time()+60),acquisition=str(root/'acquisition.json') if a.phase=='wait_source' else None,stage_status=str(root/'stage-status.json') if a.phase=='wait_source' else None,resume=False)
class Hold(p.Guard):
 def check(self,write=False):
  if self.phase==a.phase and not self.held:
   self.held=True;(root/(a.tag+'-ready.json')).write_text(json.dumps({'pid':os.getpid(),'phase':self.phase}))
   while not (root/'release').exists():super().check();time.sleep(.01)
  super().check(write)
g=Hold(30,args.cutoff,root);g.held=False
try:
 if a.barrier:
  until=time.monotonic()+10
  while not (root/'start').exists():
   if time.monotonic()>until:raise RuntimeError('test start deadline')
   time.sleep(.01)
 p.run(args,g)
except BaseException as e:
 print(type(e).__name__+': '+str(e),file=sys.stderr);sys.exit(1)
sys.exit(0)
