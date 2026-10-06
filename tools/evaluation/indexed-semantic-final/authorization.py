"""Parent-owned prerequisite; no code here issues an authorization certificate."""
import os,json,pathlib,hashlib,subprocess,time
import core as C
R=C.R
TASK='547-exact-owned-pid-and-original-export-repair'
REQUEST=pathlib.Path('/home/isa/PocketLore-control/runtime/547-source-review-request.json')
CERTIFICATE=pathlib.Path('/home/isa/PocketLore-control/runtime/547-source-review-authorization.json')
def read(p,limit=131072):
 p=pathlib.Path(p);C.need(not p.is_symlink(),'review-symlink');fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  v=R.version(p);C.need(v==R.version('/proc/self/fd/'+str(fd)) and v['size']<=limit,'review-size-version');b=bytearray()
  while True:
   x=os.read(fd,65536)
   if not x:break
   C.need(len(b)+len(x)<=limit,'review-size');b.extend(x)
  C.need(v==R.version(p)==R.version('/proc/self/fd/'+str(fd)) and len(b)==v['size'],'review-replaced');return json.loads(b),{'sha256':R.sha(bytes(b)),'bytes':len(b),'version':v}
 finally:os.close(fd)
def verify(commit):
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=C.ROOT,text=True).strip();anchor=json.loads(R.git_bytes(head,'tools/evaluation/indexed-semantic-final/request-authority.json'));request,rd=read(REQUEST)
 C.need(rd['sha256']==anchor['request_sha256'] and rd['bytes']==anchor['request_bytes'],'review-request-authority');sources=C.freeze(commit);roster=[{'path':p,'bytes':(C.ROOT/p).stat().st_size,'sha256':sources[p]} for p in C.ROSTER];rh=R.sha(R.canonical(roster))
 C.need(request['taskid']==TASK and request['source_commit']==commit and request['roster']==roster and request['roster_sha256']==rh,'review-request-source')
 cert,cd=read(CERTIFICATE)
 C.need(cert['verdict']=='continue' and cert['taskid']==TASK and cert['source_commit']==commit and cert['roster_sha256']==rh and cert['request_sha256']==rd['sha256'],'review-authorization')
 manifests={}
 for name in ['independent_input_manifest','independent_review_manifest']:
  d=cert[name];p=pathlib.Path(d['path']);C.need(str(p).startswith('/home/isa/PocketLore-control/continue-20261006/indexed-final-source-recovery/') and '..' not in p.parts,'review-manifest-path');value,observed=read(p,1048576);C.need(observed['sha256']==d['sha256'] and observed['bytes']==d['bytes'],'review-manifest-content');manifests[name]={'sha256':observed['sha256'],'bytes':observed['bytes']}
 return {'taskid':TASK,'source_commit':commit,'roster_sha256':rh,'request_sha256':rd['sha256'],'certificate_sha256':cd['sha256'],'certificate_version':cd['version'],'verdict':'continue','manifests':manifests}
