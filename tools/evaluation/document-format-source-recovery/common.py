"""Task 554 fixed source, content and raw-version contracts; no recognition."""
import os,pathlib,json,hashlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[3];BASE=pathlib.Path(__file__).resolve().parent
OUT=ROOT/'downloads/document-format-source-recovery-554';BUILD=OUT/'build';RUN=OUT/'run'
JDK=pathlib.Path('/home/isa/Android/atlas-toolchain/jdk')
REQUEST=pathlib.Path('/home/isa/PocketLore-control/runtime/554-documents-host-run-request.json')
RESULT=REQUEST.with_name('554-documents-host-run-result.json')
TASK='554-lossless-nullable-document-refusal-receipts';UNIT='pocketlore-documents-host-554-20261006.service'
APP='android/app/src/main/java/org/pocketlore/app/'
ROSTER=[APP+n+'.java' for n in ['DocumentZip','DocumentBytes','DocumentFormatPolicy','DocumentHtml','StructuredDocuments','PersonalText','PersonalDocuments','PersonalDocumentsActivity','KnowledgePack','PackLibrary']]+['tools/evaluation/document-formats/'+n for n in ['FormatPolicyProbe.java','source.gradle','AndroidManifest.xml','tests/DocumentFormatsInstrumentation.java','tests/FormatFixtureProvider.java']]+['tools/android-build.sh','tools/release/finalize_apk.py','tools/evaluation/check_document_format_source_recovery.sh']+['tools/evaluation/document-format-source-recovery/'+n for n in ['common.py','worker.py','check.py','BatchProbe.java','CentralProbe.java','RefusalReceipt.java','cases.json','cases.tsv','recovery.json','build-inputs-554.json','accounting.py','accounting_controls.py','accounting-policy.json','recovery552.json','recovery553.json','recovery554.json','refusal-policy.json','central-policy.json','central_fixtures.py','central-cases.json','central-cases.tsv']]

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
def frozen(commit):
 current=sources()
 for p,d in current.items():need(d['sha256']==digest(subprocess.check_output(['git','show',commit+':'+p],cwd=ROOT)),'source-git')
 return current
def inventory():
 from accounting import inventory_detail
 return inventory_detail()['total']

def save(path,x):
 b=canonical(x)+b'\n';need(inventory()+2*len(b)+65536<8388608,'storage-reserve')
 path=pathlib.Path(path);tmp=path.with_name(path.name+'.partial')
 with open(tmp,'xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 need(not path.exists(),'no-overwrite');os.rename(tmp,path)
def command():return [str(JDK/'bin/java'),'-ea','-Xms16m','-Xmx128m','-XX:MaxMetaspaceSize=64m','-XX:ReservedCodeCacheSize=32m','-XX:MaxDirectMemorySize=32m','-XX:CompressedClassSpaceSize=32m','-XX:ActiveProcessorCount=2','-Xss512k','-cp',str(BUILD/'classes'),'org.pocketlore.app.CentralProbe',str(BASE/'cases.tsv'),str(RUN/'staging'),str(BASE/'central-cases.tsv')]

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
 need(set(actual)>={'java','libjvm','modules','javac','python','cases_json','cases_tsv','historical_ledger'} and len([k for k in actual if k.startswith('class_')])>=7 and actual==expected,'input-authority')
