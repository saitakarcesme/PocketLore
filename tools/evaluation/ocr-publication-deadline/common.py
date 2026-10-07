"""Task557 frozen helper controls; no recognition or Android execution."""
import os,pathlib,json,hashlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[3];BASE=pathlib.Path(__file__).resolve().parent
OUT=ROOT/'downloads/ocr-publication-deadline-557';BUILD=OUT/'build';RUN=OUT/'run'
JDK=pathlib.Path('/home/isa/Android/atlas-toolchain/jdk')
REQUEST=pathlib.Path('/home/isa/PocketLore-control/runtime/557-ocr-deadline-controls-v3-request.json')
RESULT=REQUEST.with_name('557-ocr-deadline-controls-v3-result.json')
TASK='557-ocr-whole-operation-stale-result-refusal';UNIT='pocketlore-ocr-deadline-controls-557-20261007.service'
ROSTER=['android/app/src/main/java/org/pocketlore/app/'+n+'.java' for n in ['OcrDeadline','AttachmentEngine','AttachmentAssets','AttachmentsActivity','AttachmentNative','DocumentInput','PersonalDocuments','PersonalText','KnowledgePack','BroadPack','ResourceStorage']]+['android/attachments-native/'+n for n in ['attachments.cpp','text_transport.h','ocr_deadline.h','CMakeLists.txt']]+['tools/attachments/'+n for n in ['build.sh','prepare.py','sources.json','models.json']]+['tools/android-build.sh','tools/release/finalize_apk.py','tools/evaluation/check_ocr_publication_deadline.sh']+['tools/evaluation/attachment-utf16/'+n for n in ['Transport.java','bridge.cpp','cases.json','cases.tsv']]+['tools/evaluation/ocr-publication-deadline/'+n for n in ['common.py','worker.py','check.py','policy.json','DeadlineProbe.java','bridge.cpp','build-inputs.json','accounting.py','accounting_controls.py','accounting-policy.json','accounting-baseline.json','receipt-policy.json']]
PROPERTIES={'MemoryMax':536870912,'MemorySwapMax':0,'CPUQuota':'200%','CPUAffinity':'0-3','TasksMax':64,'Restart':'no','KillMode':'control-group','RuntimeMaxSec':50,'TimeoutStopSec':5}
def need(ok,guard):
 if not ok:raise ValueError(guard)
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def digest(b):return hashlib.sha256(b).hexdigest()
def version(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
def identity(path,consume=False,cap=1048576):
 path=pathlib.Path(path);fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
 try:
  before=os.fstat(fd);total=0;need(version(path.stat())==version(before),'path-fd');h=hashlib.sha256();chunks=[]
  if consume:need(before.st_size<=cap,'read-cap')
  while True:
   b=os.read(fd,65536)
   if not b:break
   h.update(b);total+=len(b)
   if consume:
    need(total<=cap,'read-growth-cap');chunks.append(b)
  need(version(os.fstat(fd))==version(before)==version(path.stat()),'file-mutated')
  desc={'path':str(path),'bytes':before.st_size,'sha256':h.hexdigest(),'version':version(before)}
  return (desc,b''.join(chunks)) if consume else desc
 finally:os.close(fd)
def read(path,expected=None):
 d,b=identity(path,True)
 if expected is not None:need(d==expected,'raw-identity')
 return json.loads(b)
def content(d):return {k:d[k] for k in ['path','bytes','sha256']}
def sources():return {p:content(identity(ROOT/p)) for p in ROSTER}
def source_versions():return {p:identity(ROOT/p) for p in ROSTER}
def frozen(commit):
 current=sources()
 for p,d in current.items():need(d['sha256']==digest(subprocess.check_output(['git','show',commit+':'+p],cwd=ROOT)),'source-git')
 return current
def inventory_detail():
 from accounting import scan_roots,RESERVES,FILE_CAP,MANDATORY_ROOTS
 roots=(OUT,BASE,pathlib.Path('/home/isa/PocketLore-control/continue-20261007/ocr-publication-deadline'))
 files=scan_roots(roots,MANDATORY_ROOTS)
 paths=[ROOT/n for n in ROSTER+['FINDINGS.md','docs/RELEASE_GAPS.md','docs/evidence/ocr-publication-deadline.md','docs/evidence/ocr-publication-deadline-review.json']]
 paths+=list(REQUEST.parent.glob('557-ocr-deadline-controls*.json'))
 legacy=pathlib.Path('/home/isa/PocketLore-control/continue-20261006/ocr-publication-deadline')
 if legacy.exists():files.update(scan_roots((legacy,),(legacy,)))
 for p in paths:
  if p.exists():
   need(not p.is_symlink(),'inventory-symlink');s=p.stat();need(s.st_size<=FILE_CAP,'per-file-cap');files[str(p)]={'bytes':s.st_size,'version':version(s)}
 baseline=read(BASE/'accounting-baseline.json');need(baseline['bytes']==sum(x['bytes'] for x in baseline['records']),'old-source-count')
 return {'files':files,'actual_bytes':sum(x['bytes'] for x in files.values()),'old_git_bytes':baseline['bytes'],'additional_reserves':RESERVES,'charged_bytes':sum(x['bytes'] for x in files.values())+baseline['bytes']+RESERVES}
def inventory():return inventory_detail()['charged_bytes']

def save(path,x):
 b=canonical(x)+b'\n';need(len(b)<=262144,'receipt-cap');need(inventory()+2*len(b)+65536<8388608,'storage-reserve')
 path=pathlib.Path(path);tmp=path.with_name(path.name+'.partial')
 with open(tmp,'xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 need(not path.exists(),'no-overwrite');os.rename(tmp,path)
def command():return [str(JDK/'bin/java'),'-Xcheck:jni','-XX:ErrorFile='+str(RUN/'jvm-error.log'),'-Xms16m','-Xmx64m','-XX:MaxMetaspaceSize=64m','-XX:ReservedCodeCacheSize=32m','-XX:MaxDirectMemorySize=32m','-XX:CompressedClassSpaceSize=32m','-XX:ActiveProcessorCount=2','-Xss256k','-cp',str(BUILD),'org.pocketlore.app.DeadlineProbe',str(BUILD/'libdeadline.so'),str(ROOT/'tools/evaluation/attachment-utf16/cases.tsv')]
def process(pid):
 p=pathlib.Path('/proc')/str(pid)
 return {'pid':pid,'stat':(p/'stat').read_text(),'status':(p/'status').read_text(),'limits':(p/'limits').read_text(),'cgroup':(p/'cgroup').read_text(),'namespace':os.readlink(p/'ns/pid'),'affinity':sorted(os.sched_getaffinity(pid))}
def ticks(p):return int(p['stat'].rsplit(')',1)[1].split()[19])
def kernel():
 raw=pathlib.Path('/proc/self/cgroup').read_text();group=pathlib.Path('/sys/fs/cgroup')/raw.split('::',1)[1].strip().lstrip('/')
 return {'path':str(group),'inode':group.stat().st_ino,'raw_cgroup':raw,**{n:(group/n).read_text() for n in ['memory.max','memory.swap.max','memory.current','memory.peak','memory.swap.current','memory.events','cpu.max','cpu.stat','pids.max']}}
def kernel_contract(k):
 need(k['path'].endswith('/'+UNIT),'owned-unit')
 for key,value in {'memory.max':'536870912','memory.swap.max':'0','cpu.max':'200000 100000','pids.max':'64'}.items():need(k[key].strip()==value,'kernel-'+key)
 need(int(k['memory.swap.current'])==0 and int(k['memory.peak'])<=536870912,'kernel-memory')
def pidfd_owner(raw,pid):
 rows=[line.split(':',1)[1].strip() for line in raw.splitlines() if line.split(':',1)[0]=='Pid']
 need(len(rows)==1 and rows[0].isdigit() and int(rows[0])==pid and pid>0,'pidfd-owner')

def input_contract(actual,expected):
 need(bool(expected) and set(actual)==set(expected) and actual==expected,'input-authority')

BUILD_RECEIPT=OUT/'android-build-v3.json'
def build_authority(actual,expected,record,src):
 need(actual['path']==expected['path']==str(BUILD_RECEIPT),'build-receipt-path')
 need(actual==expected,'build-receipt-descriptor')
 need(record['exit']==0,'build-receipt-exit')
 need(record['sources']==src,'build-receipt-source')
