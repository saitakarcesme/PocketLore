"""Independent receipt invariants and bounded current sample oracle; no model reload."""
import pathlib,json,hashlib,lzma,base64,time,os,copy,re,subprocess,sys
R=pathlib.Path(__file__).resolve().parents[3];O=R/"downloads/sparse-mapping";A=R/"docs/evidence/sparse-mapping-identity-review.json"
SHA="96b9c0af5c77a4ecaabe3983175112b5ece763261c1ece12b2494b692a70dad7"
def digest(b):return hashlib.sha256(b).hexdigest()
def freeze(p):
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=digest(b),encoding="lzma+base64",data=base64.b64encode(lzma.compress(b,preset=3)).decode())
def require(condition,message):
 if not condition:raise ValueError(message)
def kernel_mappings(raw):
 # Independent parser: reconstruct authoritative rows from the complete stream, not reported fields.
 rows=[];row=None
 for line in raw.splitlines():
  parts=line.split(None,5)
  if len(parts)>=5 and re.fullmatch(r"[0-9a-f]+-[0-9a-f]+",parts[0]):
   if row is not None:rows.append(row)
   a,b=parts[0].split("-");row={"start":int(a,16),"end":int(b,16),"permission":parts[1],"offset":int(parts[2],16),"device":parts[3],"inode":int(parts[4]),"path":parts[5] if len(parts)==6 else None,"raw":[line]}
  elif row is not None:
   row["raw"].append(line)
   fields=line.split()
   if fields and fields[0] in ["Rss:","Pss:","Anonymous:","Private_Clean:","Private_Dirty:","Swap:"]:
    require(len(fields)==3 and fields[1].isdigit() and fields[2]=="kB","Invalid kernel units")
    key=fields[0][:-1];require(key not in row,"Duplicate kernel counter");row[key]=int(fields[1])*1024
 if row is not None:rows.append(row)
 return rows
def validate(r):
 require(r["exit"]==0 and not r["errors"],"Failed real probe")
 require(r["source_sha256"]==digest((R/"tools/runtime/sparse/mapping.py").read_bytes()),"Stale executed implementation")
 require(r["started"]<r["ended"]<=time.time(),"Stale invocation")
 require(r["model_identity"]["sha256"]==SHA and r["model_identity"]["bytes"]==12290628576,"Wrong model")
 require(r["final_model_identity"]=={k:v for k,v in r["model_identity"].items() if k!="sha256"},"Mutated model")
 require(r["model_payload_read_bytes"]==25165824,"Changed payload budget")
 expected={"fixture-positive","wrong-digest","wrong-inode","other-descriptor","unknown-hash","over-window","unaligned","outside-file","copy-cancel","deadline","partial-map","closed-map","mixed-map","renamed-file","deleted-file","changed-version","same-size-model-distractor","actual-model-window"}
 require({c["case"] for c in r["checks"]}==expected and len(r["checks"])==19,"Missing or extra controls")
 for c in r["checks"]:require(c.get("passed") is True or c.get("rejected") is True,"Failed control")
 windows=[c["raw"] for c in r["checks"] if c["case"]=="actual-model-window"]
 require([w["offset"] for w in windows]==[16777216,67108864],"Changed selected windows")
 for w in windows:
  require(w["sample_sha256"]==w["reread_sha256"],"Cache advice changed bytes")
  for phase in ("before","touched","after_advice"):
   s=w[phase];require(s["pid"]==r["preflight"]["pid"] and s["startticks"]==r["preflight"]["startticks"] and s["namespaces"]==r["preflight"]["namespaces"],"Changed process/namespace")
   require(s["fd_identity"]==r["final_model_identity"],"Wrong live descriptor")
   require(s["length"]==4194304 and s["offset"]==w["offset"],"Changed mapping range")
   require(s["mount"]==r["model_mount"] and s["fdinfo"]==r["model_fdinfo"],"Changed mount binding")
   mid=re.search(r"^mnt_id:\s+(\d+)$",s["fdinfo"],re.M)[1];require(s["mount"].split()[0]==mid,"Wrong mount ID")
   actual=[v for v in kernel_mappings(s["raw_smaps"]) if v["start"]<s["address"]+s["length"] and v["end"]>s["address"]]
   require(actual==s["mappings"],"Reported VMA fields contradict kernel stream")
   require(int(re.search(r"^Pid:\s+(\d+)$",s["status"],re.M)[1])==s["pid"],"Status PID contradicts observation")
   require(int(re.search(r"^ino:\s+(\d+)$",s["fdinfo"],re.M)[1])==s["fd_identity"]["inode"],"fdinfo inode mismatch")
   cursor=s["address"];dev=":".join(f"{int(n):02x}" for n in s["mount"].split()[2].split(":"))
   for v in s["mappings"]:
    require(v["start"]==cursor and v["end"]<=s["address"]+s["length"],"Partial/overlapping mapping")
    require(v["permission"]=="r--s" and v["inode"]==r["model_identity"]["inode"] and v["device"]==dev and v["offset"]==w["offset"]+cursor-s["address"],"Wrong VMA identity")
    require("\n".join(v["raw"]) in s["raw_smaps"],"Missing kernel stream")
    cursor=v["end"]
   require(cursor==s["address"]+s["length"],"Absent mapping")
  require(sum(v["Rss"] for v in w["touched"]["mappings"])>0,"Missing actual touched residency")
 for s in [r["preflight"],*r["hash_samples"],*r["samples"],r["final"]]:
  require(s["pid"]==r["preflight"]["pid"] and s["startticks"]==r["preflight"]["startticks"],"Changed sampling process")
  k=s["kernel"];require(int(k["memory.max"])==4294967296 and int(k["memory.swap.max"])==0 and k["cpu.max"].strip()=="200000 100000" and int(k["pids.max"])==512,"Wrong actual kernel limits")
  require(int(k["memory.current"])<=int(3.5*1024**3) and int(k["memory.peak"])<=4294967296,"Exceeded resource containment")
 return windows
report={"checker_payload_bytes_read":0,"run_id":time.strftime("%Y%m%dT%H%M%SZ",time.gmtime()),"errors":[],"files":[],"android_or_generation_acceptance":False}
try:
 p=sorted(O.glob("[0-9]*/receipt.json"))[-1];r=json.loads(p.read_text());report["probe_receipt_sha256"]=digest(p.read_bytes());windows=validate(r)
 report["negative_controls"]=[]
 for name in ["stale","hash","inode","pid","missing","range","mount","no-residency","kernel","reported-rss","raw-offset"]:
  b=copy.deepcopy(r)
  if name=="stale":b["ended"]-=7200
  elif name=="hash":b["model_identity"]["sha256"]="0"*64
  elif name=="inode":b["final_model_identity"]["inode"]+=1
  elif name=="missing":b["checks"].pop()
  elif name=="kernel":b["final"]["kernel"]["memory.max"]="max"
  else:
   w=next(c["raw"] for c in b["checks"] if c["case"]=="actual-model-window")
   if name=="pid":w["before"]["pid"]=-1
   elif name=="range":w["before"]["mappings"][0]["end"]-=4096
   elif name=="mount":w["before"]["mount"]="wrong"
   elif name=="reported-rss":w["touched"]["mappings"][0]["Rss"]+=4096
   elif name=="raw-offset":
    h=w["touched"]["mappings"][0]["raw"][0];w["touched"]["raw_smaps"]=w["touched"]["raw_smaps"].replace(h,h.replace("01000000","01001000"),1)
   else:w["touched"]["mappings"][0]["Rss"]=0
  try:validate(b);denied=False
  except (ValueError,TypeError):denied=True
  require(denied,"Negative accepted: "+name);report["negative_controls"].append({"mutation":name,"rejected":True})
 # Separate process/pread implementation checks exact samples again, within32MiB total payload budget.
 model=pathlib.Path("/home/isa/PocketLore-control/overnight-20261005/strong-model-identity-research/weights-quarantine/Qwen3.6-35B-A3B-UD-Q2_K_XL.gguf")
 history=json.loads(A.read_text()) if A.exists() else {"runs":[]}
 prior_bytes=sum(x.get("checker_payload_bytes_read",sum(v["bytes"] for v in x.get("independent_samples",[]))) for x in history["runs"])
 require(25165824+prior_bytes+8388608<=67108864,"Cumulative task payload budget exhausted")
 with model.open("rb") as f:
  def fs():
   s=os.fstat(f.fileno());return dict(device=s.st_dev,inode=s.st_ino,bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,nlink=s.st_nlink)
  require(fs()==r["final_model_identity"],"Changed current original")
  report["independent_samples"]=[]
  for w in windows:
   b=os.pread(f.fileno(),4194304,w["offset"]);report["checker_payload_bytes_read"]+=len(b);require(len(b)==4194304 and digest(b)==w["sample_sha256"],"Independent original sample mismatch");os.posix_fadvise(f.fileno(),w["offset"],4194304,os.POSIX_FADV_DONTNEED);report["independent_samples"].append({"offset":w["offset"],"bytes":len(b),"sha256":digest(b)})
  require(fs()==r["final_model_identity"],"Changed current file during oracle")
 report["model_payload_bytes_including_checker"]=25165824+prior_bytes+report["checker_payload_bytes_read"]
except Exception as e:report["errors"].append(type(e).__name__+": "+str(e))
finally:
 for p in sorted(O.glob("*/receipt.json")):report["files"].append(freeze(p))
 for p in sorted((O/"validator-red").glob("*.py")):report["files"].append(freeze(p))
 for folder in ("tools/runtime/sparse","tools/evaluation/sparse-mapping","docs/evidence/sparse-mapping-inputs"):
  for p in sorted((R/folder).glob("*")):
   if p.is_file():report["files"].append(freeze(p))
 old=pathlib.Path("/home/isa/PocketLore-control/continue-20261006/strong-native/first-execution-failure-20261006T1016Z")
 for p in sorted(old.glob("*.json")):report["files"].append(freeze(p))
 report["exit"]=int(bool(report["errors"]));report["classification"]="BOUNDED_OWNED_MAPPING_CONTROLS_PASS" if not report["errors"] else "MAPPING_CONTROLS_INCOMPLETE"
 prior=json.loads(A.read_text()) if A.exists() else {"runs":[]};prior["runs"].append(report);A.write_text(json.dumps(prior,indent=2)+"\n")
print(json.dumps({k:report[k] for k in ("run_id","classification","errors","exit")},indent=2));sys.exit(report["exit"])
