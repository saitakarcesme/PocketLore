"""Current-code native lifecycle gate. No model execution or historical credit."""
import copy,json,pathlib,re,struct,subprocess,sys,time,zipfile,os,hashlib
from contract import ROOT,SOURCES,BINARIES,identity,sha,source_contract,process_stat,status_pid,sample_identity,elf_machine
from run import BASE
POLICY=ROOT/'docs/evidence/native-cache-inputs/repair-2/policy.json'
COMMON={'unaligned','oversized','absent-map','async-reader','alias-mapping','live-lifetime','nested-owner','partial-map','cancelled','closed-map','reader-after-unregister'}
FIXTURE=COMMON|{'retiring-reader','retiring-advice','exception-unmapped','wrong-inode','wrong-size','wrong-hash','deadline','renamed'}

def validate_policy(policy,layout):
 assert policy['model_sha256']==layout['model_sha256']=='96b9c0af5c77a4ecaabe3983175112b5ece763261c1ece12b2494b692a70dad7'
 assert policy['model_bytes']==layout['model_bytes']==12290628576
 assert layout['metadata']['general.architecture']=='qwen35moe' and layout['tensor_count']==733
 first=layout['tensors'][0];assert policy['tensor']==first and first['ggml_type']==12
 # Pinned GGML Q4_K stores 256 values in 144 bytes. The first tensor's
 # recorded interval is exactly its tensor bytes, not trailing alignment.
 count=1
 for n in first['dims']:count*=n
 assert count%256==0 and count//256*144==first['stored_interval_bytes_including_alignment']
 start=layout['data_start']+first['relative_data_offset'];expected=(start+16383)//16384*16384
 assert policy['offset']==expected and policy['window']==4194304 and expected>=start and expected+policy['window']<=start+count//256*144
 assert policy['charged_payload']==12582912 and policy['max_model_payload']==67108864 and policy['full_hash_passes']==1
 return True

def mappings(o,offset):
 assert o['pid']>0 and int(o['startticks'])>0 and status_pid(o['status'])==o['pid']
 assert len(o['regions'])==1;r=o['regions'][0];assert r['offset']==offset and r['bytes']==4194304 and r['page_size']>0
 device=tuple(map(int,o['mount'].split()[2].split(':')));found=[]
 for block in re.split(r'(?=^[0-9a-f]+-[0-9a-f]+ )',o['smaps'],flags=re.M):
  if not block.strip():continue
  h=block.splitlines()[0].split()
  if '-' not in h[0]:continue
  lo,hi=[int(v,16) for v in h[0].split('-')]
  if lo!=r['address']:continue
  assert hi-lo==r['bytes'] and h[1]=='r--s' and int(h[2],16)==offset
  assert tuple(int(v,16) for v in h[3].split(':'))==device and int(h[4])==o['inode']
  f={k:int(v)*1024 for k,v in re.findall(r'^(Rss|Pss|Private_Clean|Private_Dirty|Anonymous|Swap):\s+(\d+) kB$',block,re.M)}
  assert set(f)=={'Rss','Pss','Private_Clean','Private_Dirty','Anonymous','Swap'}
  assert f['Pss']<=f['Rss']<=r['bytes'] and f['Anonymous']==f['Swap']==f['Private_Dirty']==0
  assert r['cache_present_pages']*r['page_size']>=f['Rss'];found.append(f)
 assert len(found)==1;return found[0]

def validate(r,current=True):
 assert r['kind'] in ['fixture','model']
 assert r['exit']==0 and not r.get('failure') and not r.get('cleanup_failure')
 assert r['pidfd_opened'] is True and int(re.search(r'^Pid:\s+(\d+)',r['pidfd_fdinfo'],re.M)[1])==r['pid']
 assert r['cleanup'][-1]['action']=='REAPED' and r['cleanup'][-1]['exit']==0
 f=r['frozen'];source_contract(f['source'],current)
 assert r['post_source']==f['source'] and r['post_binary']==f['binary']
 assert set(f['binary'])==set(BINARIES) and f['binary']
 for p,v in f['binary'].items():
  if current:
   now=identity(ROOT/p);assert now['sha256']==v['sha256'] and now['version']['size']==v['version']['size'],p
 assert r['executable_before']==r['executable_after']==f['binary'][BINARIES[0]]
 assert r['start_ns']<r['end_ns'] and r['samples']
 policy=json.loads(POLICY.read_text());layout_path=POLICY.with_name('tensor-layout.json');assert sha(layout_path)==policy['source_layout_sha256'];validate_policy(policy,json.loads(layout_path.read_text()));offset=policy['offset'] if r['kind']=='model' else 0
 expected_size=policy['model_bytes'] if r['kind']=='model' else 4194304
 lines=[json.loads(x) for x in r['stdout'].splitlines() if x.startswith('{')]
 expected=COMMON if r['kind']=='model' else FIXTURE
 assert expected<={x.get('control') for x in lines if x.get('refused') is True}
 positives={x.get('control') for x in lines if x.get('pass') is True}
 assert 'mapped-pread-after-advice' in positives
 if r['kind']=='fixture':assert {'inherited-fd','deferred-destructor-observation'}<=positives
 assert not any(x in r['stdout'] for x in ['OWNED_UNMAP_FAILURE','OWNED_RELEASE_REFUSED','OWNED_UNKNOWN_RELEASE_REFUSED','OWNED_READER_CLEANUP_REFUSED'])
 a=json.loads(r['raw']['native-resident.json']);b=json.loads(r['raw']['native-released.json'])
 for key in ['pid','startticks','fd','stat_device','inode','bytes','sha256','mount','fdinfo','namespaces']:
  assert a[key]==b[key],key
 assert a['bytes']==expected_size and a['pid']==r['pid'] and int(a['startticks'])==r['startticks']
 if r['kind']=='model':
  assert a['sha256']==policy['model_sha256'] and r['input_before']==r['input_after']
  assert a['inode']==r['input_before']['inode'] and a['stat_device']==r['input_before']['device']
 assert mappings(a,offset)['Rss']==4194304 and mappings(b,offset)['Rss']==0
 assert r['start_ns']<a['monotonic_ns']<b['monotonic_ns']<r['end_ns']
 previous=0;phase_covered=False
 ns=r['samples'][0]['namespaces'];expected_cgroup=r['samples'][0]['cgroup']
 assert a['namespaces']==''.join(ns[n] for n in ['mnt','pid','user'])
 for sample in r['samples']:
  sample_identity(sample,r['pid'],r['startticks'],ns)
  assert sample['cgroup']==expected_cgroup
  assert r['start_ns']<=sample['monotonic_ns']<=r['end_ns'] and sample['monotonic_ns']>previous
  previous=sample['monotonic_ns']
  assert sample['phase'] in ['hash-or-setup','resident-observation-present','release-observation-present']
  phase_covered|=a['monotonic_ns']<sample['monotonic_ns']<b['monotonic_ns'] and sample['phase']=='resident-observation-present'
 assert phase_covered,'No live resident-window sample'
 k=f['kernel'];assert int(k['memory.max'])<=9663676416 and int(k['memory.swap.max'])==0 and int(k['pids.max'])<=512
 q,p=map(int,k['cpu.max'].split());assert 0<q<=2*p and len(k['affinity_cpus'])<=4
 return True

def mutations(base):
 def raw_status(x):x['samples'][0]['status']=re.sub(r'^Pid:.*$', 'Pid:\t999999',x['samples'][0]['status'],flags=re.M)
 def raw_start(x):
  v=x['samples'][0]['stat'];at=v.rfind(')')+2;parts=v[at:].split();parts[19]=str(int(parts[19])+1);x['samples'][0]['stat']=v[:at]+' '.join(parts)
 def change_region(x):
  a=json.loads(x['raw']['native-resident.json']);a['regions'][0]['offset']+=4096;x['raw']['native-resident.json']=json.dumps(a)
 changes=[('empty-source',lambda x:x['frozen']['source'].clear()),('missing-source',lambda x:x['frozen']['source'].pop(SOURCES[0])),('changed-source',lambda x:x['frozen']['source'][SOURCES[0]].update(sha256='0'*64)),('missing-binary',lambda x:x['frozen']['binary'].pop(BINARIES[0])),('numeric-pid',lambda x:x['samples'][0].update(pid=999999)),('raw-pid',raw_status),('raw-startticks',raw_start),('missing-status',lambda x:x['samples'][0].pop('status')),('missing-namespace',lambda x:x['samples'][0].pop('namespaces')),('reversed-time',lambda x:x['samples'][0].update(monotonic_ns=x['end_ns']+1)),('missing-window',lambda x:x.update(samples=[])),('wrong-offset',change_region),('unreaped',lambda x:x.update(cleanup=[])),('failed-execution',lambda x:x.update(exit=7))]
 outcomes=[]
 for name,mutate in changes:
  d=copy.deepcopy(base);mutate(d)
  try:validate(d)
  except (AssertionError,KeyError,ValueError,TypeError,IndexError) as e:
   import hashlib
   outcomes.append({'case':name,'refused':True,'error_type':type(e).__name__,'mutated_receipt_sha256':hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()});continue
  raise AssertionError('Corrupt receipt passed '+name)
 return outcomes

def artifacts(source_path):
 for cache in [ROOT/'downloads/native-cache-build/host/CMakeCache.txt']+[ROOT/f'downloads/native-cache-build/android/{abi}/CMakeCache.txt' for abi in ['arm64-v8a','x86_64']]:
  selected=next(l.split('=',1)[1] for l in cache.read_text().splitlines() if l.startswith('LLAMA_SOURCE:'));assert selected==source_path
 out={};reader='/home/isa/Android/atlas-toolchain/android-ndk-r27c/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf'
 for n in BINARIES[:-1]:
  machine=elf_machine(ROOT/n);expected=183 if 'arm64-v8a' in n else 62;assert machine==expected,n
  headers=subprocess.check_output([reader,'-lW',str(ROOT/n)],text=True,timeout=15)
  if n.endswith('.so'):assert any(l.lstrip().startswith('LOAD') for l in headers.splitlines()) and all(int(l.split()[-1],16)>=16384 for l in headers.splitlines() if l.lstrip().startswith('LOAD'))
  out[n]={'identity':identity(ROOT/n),'machine':machine,'program_headers':headers}
 apk=ROOT/BINARIES[-1]
 with zipfile.ZipFile(apk) as z,apk.open('rb') as f:
  for abi in ['arm64-v8a','x86_64']:
   n=f'android/app/build/generated/nativeLibs/{abi}/libpocketlore.so';i=z.getinfo(f'lib/{abi}/libpocketlore.so');import hashlib
   assert hashlib.sha256(z.read(i)).hexdigest()==out[n]['identity']['sha256']
   f.seek(i.header_offset);head=f.read(30);a,b=struct.unpack_from('<HH',head,26);offset=i.header_offset+30+a+b
   assert i.compress_type==zipfile.ZIP_STORED and offset%16384==0
   out[n]['apk_data_offset']=offset
 out[BINARIES[-1]]=identity(apk);return out

def collect_runs(base, names):
 # Collect every byte before evaluating any packet. One bad fixture cannot hide
 # a separately retained model observation. Missing inputs remain explicit.
 runs={}; originals={}; errors={}
 for name in names:
  try:
   p=pathlib.Path((base/(name+'-receipt-path.txt')).read_text());raw=p.read_bytes()
   originals[name]={'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'text':raw.decode()}
   runs[name]=json.loads(raw)
  except Exception as e:errors[name]=type(e).__name__+': '+str(e)
 return runs,originals,errors

def atomic_packet(destination, packet):
 raw=json.dumps(packet,indent=2).encode()
 # Content addressed observations never replace an earlier success or failure.
 archive=destination.parent/'observations';archive.mkdir(parents=True,exist_ok=True)
 retained=archive/(hashlib.sha256(raw).hexdigest()+'.json')
 if not retained.exists():
  with retained.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 temp=destination.with_name(destination.name+'.tmp')
 with temp.open('wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 os.replace(temp,destination)

def main(fixture_only=False):
 packet={'status':'FAIL','inference':False,'android_execution':False,'source_admission':False,'started_ns':time.monotonic_ns()};error=None
 names=['fixture'] if fixture_only else ['fixture','model']
 packet['runs'],packet['original_receipts'],packet['collection_errors']=collect_runs(BASE,names)
 try:
  assert not packet['collection_errors'],packet['collection_errors']
  assert set(packet['runs'])==set(names)
  for name in names:
   r=packet['runs'][name];validate(r);packet.setdefault('mutations',{})[name]=mutations(r)
  packet['artifacts']=artifacts(packet['runs']['fixture']['frozen']['source_path']);packet['controls']=json.loads(pathlib.Path((BASE/'controls-path.txt').read_text()).read_text());assert packet['controls']['status']=='PRE_SAMPLE_CONTROLS_PASS'
  packet['reproducibility']=json.loads((BASE/'reproducibility.json').read_text());assert packet['reproducibility']['status']=='PASS'
  for n,h in packet['reproducibility']['native_hashes'].items():assert sha(ROOT/n)==h,n
  src=pathlib.Path(packet['runs']['fixture']['frozen']['source_path']);manifest=src.parent/'native-manifest.json'
  assert identity(manifest,True)==packet['runs']['fixture']['frozen']['derivation']
  for n,v in json.loads(manifest.read_text())['files'].items():assert sha(src/n)==v,n
  packet['derived_mmap_source']=(src/'src/llama-mmap.cpp').read_text()
  packet['status']='FIXTURE_PASS' if fixture_only else 'PASS_BOUNDED_NATIVE_LIFECYCLE_ONLY'
 except Exception as e:error=type(e).__name__+': '+str(e);packet['failure']=error
 finally:
  packet['finished_ns']=time.monotonic_ns();packet['checker_source']={'sha256':sha(pathlib.Path(__file__)),'text':pathlib.Path(__file__).read_text()}
  packet['build_receipts']={p.name:{'sha256':sha(p),'text':p.read_text()} for p in sorted((BASE/'logs').glob('*')) if p.is_file()}
  packet['stdout']=packet['status']+(' '+error if error else '')+'\n';packet['exit']=1 if error else 0
  destination=BASE/'fixture-check.json' if fixture_only else ROOT/'docs/evidence/native-cache-lifecycle-review.json'
  # Preserve the previous canonical packet before changing the current view.
  if destination.exists():
   previous=destination.read_bytes();history=BASE/'previous-packets';history.mkdir(exist_ok=True)
   saved=history/(hashlib.sha256(previous).hexdigest()+'.json')
   if not saved.exists():saved.write_bytes(previous)
  atomic_packet(BASE/'current-check.json',packet)
  temp=destination.with_name(destination.name+'.tmp');temp.write_bytes((BASE/'current-check.json').read_bytes());os.replace(temp,destination)
  print(packet['stdout'],end='')
 return 1 if error else 0
if __name__=='__main__':raise SystemExit(main('--fixture-only' in sys.argv))
