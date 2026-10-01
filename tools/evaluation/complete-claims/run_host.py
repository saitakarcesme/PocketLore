#!/usr/bin/env python3
from pathlib import Path
import base64,datetime,hashlib,json,os,subprocess,sys
R=Path(__file__).resolve().parents[3];F=Path(__file__).resolve().parent
stage=sys.argv[1];assert stage in ['before','after']
old=json.loads((R/'tools/evaluation/model-capability/protocol.json').read_text());new=json.loads((F/'protocol.json').read_text())
cs=(old['cases'] if stage=='after' else [])+new['cases'];out=R/'downloads/complete-claims'/(stage+'-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'));out.mkdir(parents=True)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
lib=R/'downloads/model-capability/host-v2-build/libpocketlore.so'
if stage=='before':assert sha(lib)==json.loads((R/'docs/evidence/model-capability/run/manifest.json').read_text())['library_sha256']
model=R/'downloads/synthesis/model/Qwen3-1.7B-Q8_0.gguf';assert sha(model)==new['model_sha256']
inputs=out/'inputs';inputs.mkdir();classes=out/'classes';classes.mkdir();enc=lambda s:base64.b64encode(s.encode()).decode()
(inputs/'cases.tsv').write_text(''.join(c['id']+'\t'+enc(c['question'])+'\n' for c in cs))
for c in cs:(inputs/(c['id']+'.tsv')).write_text(''.join('\t'.join(enc(s[k]) for k in ['id','title','url','date','license','text'])+'\n' for s in c['sources']))
tc=Path('/home/isa/Android/atlas-toolchain');src=R/'android/app/src/main/java/org/pocketlore/app'
files=[src/(n+'.java') for n in ['ResearchEngine','EvidencePrompt','AnswerEngine','NativeRuntime']]+[R/'tools/evaluation/model-capability/CapabilityHarness.java']
subprocess.run([str(tc/'jdk/bin/javac'),'-d',str(classes),*map(str,files)],check=True)
results=out/'results';results.mkdir();cmd=[str(tc/'jdk/bin/java'),'-Xmx512m','-Djava.library.path='+str(lib.parent),'-cp',str(classes),'org.pocketlore.app.CapabilityHarness',str(inputs),str(model),str(results)]
m={'stage':stage,'environment':'LLMRig CPU native ISA host, six threads; not Android','model_sha256':sha(model),'library_sha256':sha(lib),'protocol_sha256':sha(F/'protocol.json'),'sources':{str(p.relative_to(R)):sha(p) for p in files+[R/'android/app/src/main/cpp/runtime.cpp']},'case_ids':[c['id'] for c in cs],'command':cmd,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(out,flush=True)
with (out/'stdout.txt').open('wb') as stdout,(out/'stderr.txt').open('wb') as stderr:
 try:m['exit_code']=subprocess.run(cmd,env=dict(os.environ,POCKETLORE_HOST_THREADS='6'),stdout=stdout,stderr=stderr,timeout=1200).returncode
 except subprocess.TimeoutExpired:m['exit_code']=124
m['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();m['artifacts']={str(p.relative_to(out)):sha(p) for p in results.glob('*')}
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(m['exit_code'],flush=True);sys.exit(m['exit_code'])
