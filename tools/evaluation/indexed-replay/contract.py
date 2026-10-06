"""545: bounded exact-byte consumption, independent authority and storage accounting."""
import hashlib,json,os,pathlib,subprocess,time
ROOT=pathlib.Path(__file__).resolve().parents[3];BASE=pathlib.Path(__file__).parent
RUN=ROOT/'downloads/indexed-replay-545';FROZEN=RUN/'final-deduplicated';LOGS=ROOT/'downloads/indexed-replay-545-verification'
OLD=ROOT/'downloads/indexed-recovery-544';AUTHORITY_BASE=ROOT/'tools/evaluation/indexed-recovery'
INITIAL_SHA='ba9875fe4f6103904748ec4a9c3c09a31d5e25bdc8fbed102e66df53666fc298'
CAP=2097152;COMBINED_CAP=8388608
class Refused(ValueError):pass
def need(ok,g):
 if not ok:raise Refused(g)
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def version(p):
 s=os.stat(p);return dict(device=s.st_dev,inode=s.st_ino,size=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns)
def path(rel):
 need(isinstance(rel,str) and rel and not pathlib.PurePosixPath(rel).is_absolute() and all(s not in ('','.','..') for s in rel.split('/')),'reference-path');p=ROOT
 for s in rel.split('/'):p=p/s;need(not p.is_symlink(),'reference-symlink')
 need(p.is_file(),'reference-missing');return p

def consume(r,json_value=False,between=None,observe=False):
 """Parse only bytes hashed from this held FD. Never return a reopenable path."""
 need(type(r['bytes']) is int and 0<=r['bytes']<=33554432,'reference-size');p=path(r['path']);fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW);data=bytearray();h=hashlib.sha256();start=time.monotonic();context=None
 try:
  before=version(p);need(before['size']==r['bytes'],'reference-size');need('version' not in r or before==r['version'],'reference-version');need(before==version('/proc/self/fd/'+str(fd)),'reference-fd')
  # Exact former validation->consumption seam, engineered owned injections only.
  if between is not None:between()
  while True:
   need(time.monotonic()-start<30,'reference-deadline');b=os.read(fd,65536)
   if not b:break
   need(len(data)+len(b)<=r['bytes'],'reference-size');data.extend(b);h.update(b)
  need(len(data)==r['bytes'] and h.hexdigest()==r['sha256'],'reference-content');need(before==version(p)==version('/proc/self/fd/'+str(fd)),'reference-replaced')
  if observe:
   context={'pid':os.getpid(),'stat':pathlib.Path('/proc/self/stat').read_text(),'status':pathlib.Path('/proc/self/status').read_text(),'namespaces':{n:os.readlink('/proc/self/ns/'+n) for n in ('pid','mnt','user')},'fd':fd,'fdinfo':pathlib.Path('/proc/self/fdinfo',str(fd)).read_text(),'mountinfo':pathlib.Path('/proc/self/mountinfo').read_text(),'version':before};validate_context(context,r)
  raw=bytes(data)
  if json_value:need(len(raw)<=16*1024**2,'json-bound');value=json.loads(raw)
  else:value=raw
  need(before==version(p)==version('/proc/self/fd/'+str(fd)),'reference-replaced');return (value,context) if observe else value
 finally:os.close(fd)
def validate_context(c,r):
 need('version' in r and c['version']==r['version'],'context-authority-version')
 info=dict(l.split(':',1) for l in c['fdinfo'].splitlines());st=dict(l.split(':',1) for l in c['status'].splitlines() if ':' in l)
 need(c['pid']==int(st['Pid'])==int(c['stat'].split(' (')[0]),'context-PID');need(int(info['flags'],8)&3==0,'context-readonly');need(int(info['ino'])==c['version']['inode'],'context-inode');need(int(info['pos'])==r['bytes'],'context-position');need(info['mnt_id'].strip() in {l.split()[0] for l in c['mountinfo'].splitlines()},'context-mount');need(set(c['namespaces'])=={'pid','mnt','user'},'context-namespace')
def initial():
 p=BASE/'initial.json';return consume({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':INITIAL_SHA},True)
def old_ref(p):
 rel=str(pathlib.Path(p).relative_to(ROOT));rows=initial()['old544_files']+initial()['old544_generated']
 for r in rows:
  if r['path']==rel:return r
 raise Refused('unregistered-old-reference')
def git_bytes(commit,rel,expected=None):
 need(len(commit)==40 and all(x in '0123456789abcdef' for x in commit),'git-commit');need(not rel.startswith('/') and '..' not in rel.split('/'),'git-path')
 p=subprocess.run(['git','cat-file','-s',commit+':'+rel],cwd=ROOT,capture_output=True,timeout=10);need(p.returncode==0,'git-source');size=int(p.stdout);need(0<=size<=16*1024**2,'git-size')
 b=subprocess.run(['git','cat-file','blob',commit+':'+rel],cwd=ROOT,capture_output=True,timeout=15,check=True).stdout;need(len(b)==size and (expected is None or sha(b)==expected),'git-content');return b
def old_git(rel):
 r=next(x for x in initial()['old544_git'] if x['path']==rel);return git_bytes(r['commit'],rel,r['sha256'])
def hash_file(p,cap=33554432):
 h=hashlib.sha256();n=0
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(65536),b''):n+=len(b);need(n<=cap,'hash-bound');h.update(b)
 return h.hexdigest()
def descriptor(p):
 p=pathlib.Path(p);v=version(p);h=hash_file(p);need(v==version(p),'descriptor-race');return dict(path=str(p.relative_to(ROOT)),bytes=v['size'],sha256=h,version=v)
def paths():
 out=[]
 for root in [RUN,LOGS,BASE,AUTHORITY_BASE]:
  if root.exists():out += [p for p in root.rglob('*') if p.is_file()]
 out += [ROOT/p for p in ['tools/packs/current-xml/indexed.py','tools/packs/current-xml/integrity.py','tools/packs/current-xml/FORMAT.md','tools/evaluation/check_indexed_integrity_recovery.sh','tools/evaluation/check_indexed_reference_replay.sh','docs/evidence/indexed-reference-replay.md','docs/evidence/indexed-reference-replay-review.json','FINDINGS.md','docs/RELEASE_GAPS.md'] if (ROOT/p).is_file()]
 return sorted(set(out))
def inventory():return [descriptor(p) for p in paths()]
def used():return sum(p.stat().st_size for p in paths())
class Budget:
 def __init__(self,cap=CAP):self.cap=cap;self.reserved=0
 def reserve(self,n):need(n>=0 and used()+self.reserved+n<=self.cap and initial()['old544_conservative_bytes']+used()+self.reserved+n<=COMBINED_CAP,'storage-reservation');self.reserved+=n;return n
 def release(self,n):self.reserved-=n;need(used()+self.reserved<=self.cap,'storage-observed')
 def write(self,p,b):
  n=self.reserve(2*len(b)+4096);p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.staging')
  try:
   with open(tmp,'xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
   os.replace(tmp,p)
  finally:self.release(n)
BUDGET=Budget()
def save(p,v):BUDGET.write(p,canonical(v)+b'\n')
def admit_local(p):return descriptor(p)

CONTEXTS={}
def manifest():return json.loads(old_git('tools/evaluation/indexed-recovery/historical-manifest.json'))
def verify_reference(name,descriptor=None,read_json=False):
 m=manifest();need(name in m['references'],'reference-name');e=m['references'][name];r=e if descriptor is None else descriptor
 need(set(r)==set(e),'reference-shape')
 for k,g in [('kind','reference-format'),('bytes','reference-size'),('sha256','reference-hash'),('path','reference-path')]:need(r[k]==e[k],g)
 if r['kind']=='git':
  need(r['commit']==e['commit'],'reference-commit');b=git_bytes(r['commit'],r['path'],r['sha256']);need(len(b)==r['bytes'],'reference-size');need(not read_json,'git-json-policy');return {'name':name,'sha256':r['sha256'],'bytes':r['bytes'],'kind':'git'}
 need(r['version']['inode']==e['version']['inode'],'reference-inode');need(r['version']==e['version'],'reference-version');value,ctx=consume(r,read_json,observe=True);CONTEXTS[name]=ctx
 result={'name':name,'sha256':r['sha256'],'bytes':r['bytes'],'kind':'local','version':r['version']}
 return (result,value) if read_json else result

def stable_historical(captured):
 # The sole removed field is explicit namespace-local FD observation. Every
 # other key, including counts, outcomes, timing, commitments and versions stays.
 import copy
 value=copy.deepcopy(captured)
 for name,r in value['references'].items():
  if r['kind']=='local':
   info=dict(l.split(':',1) for l in r.pop('fdinfo').splitlines());need(set(info)=={'pos','flags','mnt_id','ino'},'legacy-fd-fields');need(int(info['ino'])==r['version']['inode'] and int(info['pos'])==r['bytes'],'legacy-fd-identity');need(int(info['flags'],8)&3==0 and int(info['mnt_id'])>0,'legacy-fd-readonly')
 return value

POLICY=json.loads(old_git('tools/evaluation/indexed-recovery/policy.json'))
