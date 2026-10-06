"""Serial real mappings, independently computed byte oracles, retained failures."""
import pathlib,os,sys,json,time,hashlib,ctypes,importlib.util,traceback
R=pathlib.Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location("mapping",R/"tools/runtime/sparse/mapping.py");m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
M=pathlib.Path("/home/isa/PocketLore-control/overnight-20261005/strong-model-identity-research/weights-quarantine/Qwen3.6-35B-A3B-UD-Q2_K_XL.gguf")
SHA="96b9c0af5c77a4ecaabe3983175112b5ece763261c1ece12b2494b692a70dad7"
C=pathlib.Path("/sys/fs/cgroup"+pathlib.Path("/proc/self/cgroup").read_text().strip().split("::")[1])
O=R/"downloads/sparse-mapping"/time.strftime("%Y%m%dT%H%M%SZ",time.gmtime());O.mkdir(parents=True)
r={"started":time.time(),"checks":[],"errors":[],"samples":[],"hash_samples":[],"model_payload_read_bytes":0,"source_sha256":hashlib.sha256((R/"tools/runtime/sparse/mapping.py").read_bytes()).hexdigest()}
def snap(phase):
 x={"phase":phase,"epoch":time.time(),"monotonic_ns":time.monotonic_ns(),"pid":os.getpid(),"startticks":m.ticks(),"namespaces":m.namespaces(),"status":pathlib.Path("/proc/self/status").read_text(),"smaps_rollup":pathlib.Path("/proc/self/smaps_rollup").read_text(),"cgroup":str(C),"kernel":{n:(C/n).read_text() for n in ["memory.max","memory.swap.max","memory.current","memory.peak","memory.events","cpu.max","pids.max","cgroup.procs"]}}
 if int(x["kernel"]["memory.max"])>4*1024**3 or int(x["kernel"]["memory.swap.max"]):raise RuntimeError("Wrong supervising containment")
 if int(x["kernel"]["memory.current"])>int(3.5*1024**3):raise RuntimeError("Resource headroom exhausted")
 return x
def deny(name,f):
 try:f()
 except (RuntimeError,OSError,ValueError) as e:r["checks"].append({"case":name,"rejected":True,"error":str(e)});return
 raise AssertionError("Negative admitted: "+name)
def independent_read(fd,offset,n):
 data=os.pread(fd,n,offset);assert len(data)==n;return data
policy={"frozen_before_execution":time.time(),"model_offsets":[16777216,67108864],"model_window_bytes":4194304,"max_payload_reads":67108864,"max_any_window":134217728,"fixture_rule":"byte i = (i*17+31)%251, repeated to 2MiB; independent pread oracle","expected":["real owned mappings attributed","wrong expected digest/inode refused","same-size lookalike descriptor refused","renamed/deleted/replaced fixture refused","partial/absent/mixed mapping refused","cancel and deadline refused","oversized window refused","byte equality before/after targeted advice"]}
(O/"frozen-policy.json").write_text(json.dumps(policy,indent=2));r["policy"]=policy
try:
 r["preflight"]=snap("before");r["affinity"]=sorted(os.sched_getaffinity(0));assert len(r["affinity"])<=4
 r["meminfo"]=pathlib.Path("/proc/meminfo").read_text();r["mountinfo"]=pathlib.Path("/proc/self/mountinfo").read_text();r["source_jobs"]=[{"path":str(p),"processes":(p/"cgroup.procs").read_text()} for p in C.parent.glob("*source*.service")]
 raw=bytes((i*17+31)%251 for i in range(2*1024**2));a=O/"fixture-original";a.write_bytes(raw);b=O/"fixture-lookalike";b.write_bytes(bytes(reversed(raw)));r["fixture_sha256"]=hashlib.sha256(raw).hexdigest()
 f=m.BoundFile(a,r["fixture_sha256"]);other=m.BoundFile(b,hashlib.sha256(b.read_bytes()).hexdigest());w=f.window(0,4*m.PAGE)
 assert w.read()==raw[:4*m.PAGE];r["checks"].append({"case":"fixture-positive","passed":True,"raw":w.inspect(f.identity)})
 wrong=dict(f.identity,sha256="0"*64);deny("wrong-digest",lambda:w.inspect(wrong));deny("wrong-inode",lambda:w.inspect(dict(f.identity,inode=f.identity["inode"]+1)))
 deny("other-descriptor",lambda:m.assert_descriptor(other.fd,f.identity));deny("unknown-hash",lambda:m.BoundFile(b,"0"*64))
 deny("over-window",lambda:f.window(0,m.MAX_WINDOW+m.PAGE));deny("unaligned",lambda:f.window(1,m.PAGE));deny("outside-file",lambda:f.window(len(raw),m.PAGE))
 count=[0]
 def cancelled():count[0]+=1;return count[0]>1
 wc=f.window(65536,131072);deny("copy-cancel",lambda:wc.read(cancelled));wc.close()
 original_deadline=f.deadline;f.deadline=0;deny("deadline",lambda:w.inspect(f.identity));f.deadline=original_deadline
 m.syscall(m.L.munmap(w.address+m.PAGE,m.PAGE));deny("partial-map",lambda:w.inspect(f.identity));w.close();deny("closed-map",lambda:w.inspect(f.identity))
 mix=f.window(0,4*m.PAGE);mapped=m.L.mmap(mix.address+m.PAGE,m.PAGE,1,0x11,other.fd,0);assert mapped==mix.address+m.PAGE;deny("mixed-map",lambda:mix.inspect(f.identity));mix.close();other.close()
 rename=O/"fixture-renamed";a.rename(rename);deny("renamed-file",lambda:f.verify(f.identity));f.close()
 deleted=O/"fixture-delete-control";deleted.write_bytes(raw);d=m.BoundFile(deleted,r["fixture_sha256"]);deleted.unlink();deny("deleted-file",lambda:d.verify(d.identity));d.close()
 original=O/"fixture-version";original.write_bytes(raw);v=m.BoundFile(original,r["fixture_sha256"])
 with original.open("r+b") as stream:stream.write(b"!")
 deny("changed-version",lambda:v.verify(v.identity));v.close()
 # Same-size sparse distractor has no model payload and is never loaded or whole-file hashed.
 look=O/M.name
 with look.open("xb") as stream:stream.truncate(12290628576);stream.seek(0);stream.write(b"not model")
 r["distractor"]={"logical":look.stat().st_size,"allocated":look.stat().st_blocks*512}
 model=m.BoundFile(M,SHA,observe=lambda:r["hash_samples"].append(snap("full-identity-hash")))
 r["model_identity"]=model.identity;r["model_fdinfo"]=model.fdinfo;r["model_mount"]=model.mount
 fd=os.open(look,os.O_RDONLY)
 try:deny("same-size-model-distractor",lambda:m.assert_descriptor(fd,model.identity))
 finally:os.close(fd)
 for offset in policy["model_offsets"]:
  w=model.window(offset,policy["model_window_bytes"]);row={"offset":offset,"before":w.inspect(model.identity),"cached_pages_before":w.resident_pages()};r["samples"].append(snap("before-window"))
  expected=independent_read(model.fd,offset,w.length);r["model_payload_read_bytes"]+=w.length
  actual=w.read();r["model_payload_read_bytes"]+=w.length;assert actual==expected
  row.update(sample_sha256=hashlib.sha256(actual).hexdigest(),touched=w.inspect(model.identity),cached_pages_touched=w.resident_pages());r["samples"].append(snap("touched"))
  w.evict();row.update(after_advice=w.inspect(model.identity),cached_pages_after_advice=w.resident_pages());r["samples"].append(snap("after-advice"))
  again=w.read();r["model_payload_read_bytes"]+=w.length;assert again==expected;row["reread_sha256"]=hashlib.sha256(again).hexdigest();w.evict();w.close();r["checks"].append({"case":"actual-model-window","passed":True,"raw":row})
 assert r["model_payload_read_bytes"]<=policy["max_payload_reads"];model.verify(model.identity);r["final_model_identity"]=m.state(model.fd);model.close();assert m.Window.total==0
 r["final"]=snap("after-close")
except Exception as e:r["errors"].append({"type":type(e).__name__,"message":str(e),"traceback":traceback.format_exc()})
finally:
 r["ended"]=time.time();r["exit"]=int(bool(r["errors"]));(O/"receipt.json").write_text(json.dumps(r,indent=2)+"\n")
print(json.dumps({"path":str(O),"exit":r["exit"],"checks":len(r["checks"]),"errors":r["errors"]}));sys.exit(r["exit"])
