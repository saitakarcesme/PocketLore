#!/usr/bin/env python3
"""Explicit evidence freeze; not a passing test or a rights/quality approval."""
import hashlib,json,pathlib,subprocess,zipfile
root=pathlib.Path(__file__).resolve().parents[3];out=root/'docs/evidence/scale-integration/candidate.json'
if out.exists():raise SystemExit('Existing candidate freeze must not be silently replaced')
def spec(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return {'bytes':p.stat().st_size,'sha256':h.hexdigest()}
paths=set(subprocess.check_output(['git','ls-files','android','tools/answers/model.env','tools/runtime/sqlite-pin.json','tools/runtime/build-index.sh','tools/runtime/fetch-index.py','tools/evaluation/scale-integration','tools/evaluation/verify_scale_integration.py'],cwd=root,text=True).splitlines())
paths.update(str(p.relative_to(root)) for p in (root/'docs/evidence/scale-integration/final-run-5').glob('*'))
paths.update(['android/app/build/outputs/apk/debug/app-debug.apk','android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk','downloads/answers/model/qwen2.5-0.5b-instruct-q4_k_m.gguf','downloads/scale-integration/source-fixture.plscale'])
artifacts={p:spec(root/p) for p in sorted(paths) if (root/p).is_file()}
with zipfile.ZipFile(root/'android/app/build/outputs/apk/debug/app-debug.apk') as z:members={n:{'bytes':len(z.read(n)),'sha256':hashlib.sha256(z.read(n)).hexdigest()} for n in z.namelist() if n.endswith('.dex') or n.startswith('lib/')}
r={'scope':'Task300 first-shard development milestone; not full-product/rights/quality/phone acceptance','source_checkpoint':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'artifacts':artifacts,'apk_members':members,'model_role':'Qwen2.5 0.5B remains production; Qwen3 4B remains host-only','evidence_environment':'emulator-5560 x86_64; airplane mode1 wifi0; rig builds only','rights_and_answer_gate':'all new bulk editions browse-only; task221 useful support remains mandatory','full_inventory_installed':False}
out.write_text(json.dumps(r,indent=2)+'\n');print(out)
