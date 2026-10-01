#!/usr/bin/env python3
"""Create one immutable receipt only after behavioral gates and real UI have passed."""
import importlib.util,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[3];BASE=ROOT/'docs/evidence/full-capacity'
spec=importlib.util.spec_from_file_location('capacity_verify',ROOT/'tools/evaluation/full-capacity/verify.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
summary=v.behavior(BASE/'run');ui=json.loads((BASE/'ui/result.json').read_text());assert ui['status']=='PASS' and ui['actual_source_dialog']
files=set(p for p in (BASE/'run').rglob('*') if p.is_file())|set(p for p in (BASE/'ui').rglob('*') if p.is_file())|set(p for p in (ROOT/'tools/evaluation/full-capacity').rglob('*') if p.is_file() and '__pycache__' not in p.parts)
files.add(ROOT/'tools/evaluation/check_full_scale_android_capacity.sh')
files.update((ROOT/'android/app/src/main').rglob('*.java'));files.update((ROOT/'android/app/src/main').rglob('*.cpp'));files.add(ROOT/'android/app/src/androidTest/java/org/pocketlore/app/FullCapacityInstrumentation.java')
files.update(p for p in (BASE/'failures').rglob('*') if p.is_file());files.add(BASE/'build-sampler-repair.log');files.add(BASE/'build.log');files.add(BASE/'required-build.log');files.update(BASE.glob('package-storage-*.json'));files.update(BASE.glob('seed-assets*.json'));files.add(ROOT/'tools/answers/model.env')
for name in ['lane-identities.json','wiki-actual-review.json','places-actual-review.json','android-actual-review.json']:files.add(ROOT/'docs/evidence/scale-integration'/name)
files.add(ROOT/'docs/evidence/full-scale/sweep/plan.json')
runtime=json.loads((BASE/'run/runtime.json').read_text());external=[runtime['apk'],runtime['test_apk'],json.loads((BASE/'run/runtime-sampler-repair.json').read_text())['test_apk']]
receipt={'status':'Measured development capacity; not product acceptance','commit_at_freeze':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'files':[{'path':str(p.relative_to(ROOT)),'sha256':v.sha(p),'bytes':p.stat().st_size} for p in sorted(files)],'external':external}
with (BASE/'receipt.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
print(json.dumps(summary,indent=2))
