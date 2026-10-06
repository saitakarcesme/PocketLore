"""Fixed reference/control roster, verified original baselines before mutations."""
import copy
import contract as C,semantic as S
ROSTER=['hash','size','commit','path','inode','version','format','runtime','missing','oversized','traversal']
def run():
 out=[];m=C.manifest()
 for name in ROSTER:
  C.verify_reference('authored');key='authored';d=copy.deepcopy(m['references'][key])
  if name=='hash':d['sha256']='0'*64
  elif name=='size':d['bytes']+=1
  elif name=='commit':key='git:tools/packs/current-xml/indexed.py';d=copy.deepcopy(m['references'][key]);d['commit']='0'*40
  elif name=='path':d['path']='downloads/not-authorized.json'
  elif name=='inode':d['version']['inode']+=1
  elif name=='version':d['version']['mtime_ns']+=1
  elif name=='format':d['kind']='network'
  elif name=='oversized':d['bytes']=33554433
  elif name=='traversal':d['path']='../outside'
  try:
   if name=='missing':C.path('downloads/indexed-replay-545/absent-fixed-reference')
   elif name=='runtime':
    x={n:C.hash_file(C.ROOT/n) for n in S.RUNTIME};x[S.RUNTIME[1]]='0'*64;S.runtime_bindings(x)
   else:C.verify_reference(key,d)
  except C.Refused as err:out.append({'name':name,'guard':str(err),'descriptor':d,'base':key})
  else:raise C.Refused('control-accepted')
 expected=['reference-hash','reference-size','reference-commit','reference-path','reference-inode','reference-version','reference-format','historical-runtime','reference-missing','reference-size','reference-path']
 C.need([x['guard'] for x in out]==expected,'control-guards');return out
