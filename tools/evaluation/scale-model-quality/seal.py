#!/usr/bin/env python3
"""Archive finished measurement attempts, including failures; exclude classes and weights."""
from pathlib import Path
import hashlib,json,shutil,sys
R=Path(__file__).resolve().parents[3];E=R/'docs/evidence/scale-model-quality/runs'
for stage,source in [('initial','matrix-20261001T092716Z'),('buffer-v2','buffer-v2-20261001T094434Z')]:
 if len(sys.argv)>1 and stage!=sys.argv[1]:continue
 src=R/'downloads/scale-model-quality'/source;manifest=json.loads((src/'manifest.json').read_text())
 expected={'baseline','qwen3-4b','qwen25-7b','qwen15-moe'} if stage=='initial' else {'qwen25-7b','qwen15-moe'}
 if {r['id'] for r in manifest['receipts']}!=expected:raise ValueError('Partial attempt, do not seal: '+source)
 for receipt in manifest['receipts']:
  for path,h in receipt['artifact_hashes'].items():
   if hashlib.sha256((src/receipt['id']/path).read_bytes()).hexdigest()!=h:raise ValueError('Drift before seal: '+path)
 dest=E/stage
 if dest.exists():
  expected={p.relative_to(src) for p in src.rglob('*') if p.is_file() and 'classes' not in p.relative_to(src).parts}
  if {p.relative_to(dest) for p in dest.rglob('*') if p.is_file()}!=expected:raise ValueError('Archive file set differs')
  for p in expected:
   if hashlib.sha256((src/p).read_bytes()).digest()!=hashlib.sha256((dest/p).read_bytes()).digest():raise ValueError('Archive differs: '+str(p))
 else:shutil.copytree(src,dest,ignore=shutil.ignore_patterns('classes'))
 print(dest)
