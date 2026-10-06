"""Same-process owned readonly mapping leases; never infer identity from path alone."""
import ctypes,os,pathlib,time,hashlib,re
L=ctypes.CDLL(None,use_errno=True)
L.mmap.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_long];L.mmap.restype=ctypes.c_void_p
L.munmap.argtypes=[ctypes.c_void_p,ctypes.c_size_t];L.madvise.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_int];L.mincore.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p]
PAGE=os.sysconf('SC_PAGE_SIZE');MAX_WINDOW=128*1024**2
HEAD=re.compile(r'^([0-9a-f]+)-([0-9a-f]+)\s+(\S+)\s+([0-9a-f]+)\s+(\S+)\s+(\d+)(?:\s+(.*))?$')
def state(fd):
 s=os.fstat(fd);return dict(device=s.st_dev,inode=s.st_ino,bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,nlink=s.st_nlink)
def namespaces():return {n:os.readlink("/proc/self/ns/"+n) for n in ("pid","mnt","user")}
def assert_descriptor(fd,expected):
 if state(fd)!={k:v for k,v in expected.items() if k!="sha256"}:raise RuntimeError("Wrong descriptor identity")
def ticks():return int(pathlib.Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19])
def check(cancel,deadline):
 if cancel() or time.monotonic()>deadline:raise RuntimeError('Cancelled or deadline exceeded')
def syscall(value):
 if value!=0:raise OSError(ctypes.get_errno(),os.strerror(ctypes.get_errno()))
class BoundFile:
 def __init__(self,path,expected_sha,timeout=120,cancel=lambda:False,observe=lambda:None):
  self.path=str(pathlib.Path(path).resolve());self.fd=os.open(self.path,os.O_RDONLY|os.O_NOFOLLOW);self.closed=False;self.active=0;self.cancel=cancel;self.deadline=time.monotonic()+timeout
  try:
   self.identity=state(self.fd);h=hashlib.sha256();offset=0
   while offset<self.identity['bytes']:
    check(cancel,self.deadline);b=os.pread(self.fd,min(4*1024**2,self.identity['bytes']-offset),offset)
    if not b:raise RuntimeError('Short identity read')
    h.update(b);os.posix_fadvise(self.fd,offset,len(b),os.POSIX_FADV_DONTNEED);offset+=len(b)
    if offset%(64*1024**2)==0:observe()
   self.identity['sha256']=h.hexdigest()
   if h.hexdigest()!=expected_sha:raise RuntimeError('Wrong full file digest')
   self.ns=namespaces();self.pid=os.getpid();self.startticks=ticks();self.fdinfo=pathlib.Path(f'/proc/self/fdinfo/{self.fd}').read_text();mid=re.search(r'^mnt_id:\s+(\d+)$',self.fdinfo,re.M)[1]
   self.mount=next(x for x in pathlib.Path('/proc/self/mountinfo').read_text().splitlines() if x.split()[0]==mid)
   self.verify(self.identity)
  except BaseException:os.close(self.fd);self.closed=True;raise
 def verify(self,expected):
  if self.closed or self.pid!=os.getpid() or self.startticks!=ticks() or self.ns!=namespaces():raise RuntimeError('Closed or changed owner')
  check(self.cancel,self.deadline)
  if expected!=self.identity:raise RuntimeError('Changed file or expected identity')
  assert_descriptor(self.fd,expected)
  if self.identity['nlink']<=0 or os.readlink(f'/proc/self/fd/{self.fd}')!=self.path:raise RuntimeError('Deleted or renamed file')
  p=os.stat(self.path,follow_symlinks=False)
  if (p.st_dev,p.st_ino)!=(self.identity['device'],self.identity['inode']):raise RuntimeError('Path replaced; held identity not promoted')
 def window(self,offset,length):return Window(self,offset,length)
 def close(self):
  if self.active:raise RuntimeError('Live mapping cannot lose descriptor')
  if not self.closed:os.close(self.fd);self.closed=True
class Window:
 total=0
 def __init__(self,owner,offset,length):
  owner.verify(owner.identity)
  if length<=0 or length>MAX_WINDOW or Window.total+length>MAX_WINDOW or offset<0 or offset%PAGE or length%PAGE or offset+length>owner.identity['bytes']:raise RuntimeError('Invalid bounded window')
  self.owner=owner;self.offset=offset;self.length=length;self.closed=False
  self.address=L.mmap(None,length,1,1,owner.fd,offset)
  if self.address==ctypes.c_void_p(-1).value:raise OSError(ctypes.get_errno(),'mmap')
  owner.active+=length;Window.total+=length
 def inspect(self,expected):
  if self.closed:raise RuntimeError('Absent owned mapping')
  self.owner.verify(expected);raw=pathlib.Path('/proc/self/smaps').read_text();rows=[];row=None
  for line in raw.splitlines():
   m=HEAD.match(line)
   if m:
    if row:rows.append(row)
    row={'start':int(m[1],16),'end':int(m[2],16),'permission':m[3],'offset':int(m[4],16),'device':m[5],'inode':int(m[6]),'path':m[7],'raw':[line]}
   elif row:
    row['raw'].append(line)
    if ':' in line:
     k,v=line.split(':',1)
     if k in ['Rss','Pss','Anonymous','Private_Clean','Private_Dirty','Swap']:
      if not re.fullmatch(r'\s*\d+ kB',v):raise RuntimeError('Bad smaps units')
      row[k]=int(v.split()[0])*1024
  if row:rows.append(row)
  hit=[x for x in rows if x['start']<self.address+self.length and x['end']>self.address];cursor=self.address;mountdev=self.owner.mount.split()[2];ma,mi=map(int,mountdev.split(':'));observed_dev=f'{ma:02x}:{mi:02x}'
  for x in hit:
   lo=max(x['start'],self.address);hi=min(x['end'],self.address+self.length)
   if lo!=cursor or x['permission']!='r--s' or x['inode']!=expected['inode'] or x['offset']+(lo-x['start'])!=self.offset+(lo-self.address):raise RuntimeError('Partial, replaced or mixed mapping')
   # Preserve both device values. The kernel mount device, not an invented stat rewrite, binds this owned VMA.
   if x['device']!=observed_dev:raise RuntimeError('Unreconciled mapping/mount device')
   cursor=hi
  if cursor!=self.address+self.length:raise RuntimeError('Absent or partial mapping')
  if hit[0]['start']!=self.address or hit[-1]['end']!=self.address+self.length:raise RuntimeError('Coalesced VMA has unresolved per-window accounting')
  mf=f'/proc/self/map_files/{hit[0]["start"]:x}-{hit[0]["end"]:x}';proof={}
  try:proof['stat']=dict(device=os.stat(mf).st_dev,inode=os.stat(mf).st_ino)
  except OSError as e:proof['stat_error']={'errno':e.errno,'message':str(e)}
  proof['link']=os.readlink(mf)
  if proof['link']!=self.owner.path:raise RuntimeError('Mapping link differs from held file; path is not sole proof')
  self.owner.verify(expected)
  return {'pid':os.getpid(),'startticks':ticks(),'epoch':time.time(),'monotonic_ns':time.monotonic_ns(),'address':self.address,'length':self.length,'offset':self.offset,'fd':self.owner.fd,'namespaces':self.owner.ns,'fd_identity':state(self.owner.fd),'fdinfo':self.owner.fdinfo,'mount':self.owner.mount,'map_files':proof,'mappings':hit,'raw_smaps':raw,'status':pathlib.Path('/proc/self/status').read_text(),'attribution':'Owned same-process mmap of held full-hash-verified fd; not arbitrary foreign VMA attribution'}
 def resident_pages(self):
  self.inspect(self.owner.identity);v=(ctypes.c_ubyte*((self.length+PAGE-1)//PAGE))();syscall(L.mincore(self.address,self.length,v));return sum(x&1 for x in v)
 def read(self,cancel=lambda:False):
  self.inspect(self.owner.identity);out=bytearray()
  for i in range(0,self.length,65536):check(cancel,self.owner.deadline);out.extend(ctypes.string_at(self.address+i,min(65536,self.length-i)))
  self.owner.verify(self.owner.identity);return bytes(out)
 def evict(self):
  self.inspect(self.owner.identity);syscall(L.madvise(self.address,self.length,4));os.posix_fadvise(self.owner.fd,self.offset,self.length,os.POSIX_FADV_DONTNEED)
 def close(self):
  if not self.closed:syscall(L.munmap(self.address,self.length));self.owner.active-=self.length;Window.total-=self.length;self.closed=True
