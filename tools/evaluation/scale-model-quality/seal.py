#!/usr/bin/env python3
"""Archive finished measurement attempts, including failures; exclude classes and weights."""
from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parents[3];E=R/'docs/evidence/scale-model-quality/runs'
for stage,source in [('initial','matrix-20261001T092716Z'),('buffer-v2','buffer-v2-20261001T094434Z')]:
 src=R/'downloads/scale-model-quality'/source;manifest=json.loads((src/'manifest.json').read_text())
 expected={'baseline','qwen3-4b','qwen25-7b','qwen15-moe'} if stage=='initial' else {'qwen25-7b','qwen15-moe'}
 if {r['id'] for r in manifest['receipts']}!=expected:raise ValueError('Partial attempt, do not seal: '+source)
 for receipt in manifest['receipts']:
  for path,h in receipt['artifact_hashes'].items():
   if hashlib.sha256((src/receipt['id']/path).read_bytes()).hexdigest()!=h:raise ValueError('Drift before seal: '+path)
 dest=E/stage
 if dest.exists():raise ValueError('Evidence archive already exists, refusing overwrite: '+str(dest))
 shutil.copytree(src,dest,ignore=shutil.ignore_patterns('classes'))
 print(dest)
