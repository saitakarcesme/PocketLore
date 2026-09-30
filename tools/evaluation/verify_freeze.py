#!/usr/bin/env python3
"""Verify the public frozen suite without opening the private holdout."""
import hashlib
import json
import pathlib
from validate_cases import validate

root = pathlib.Path(__file__).resolve().parents[2]
manifest = json.loads((root / 'evaluation/manifest.json').read_text())
entry = manifest['development']
raw = (root / entry['path']).read_bytes()
assert hashlib.sha256(raw).hexdigest() == entry['sha256'], 'Frozen development hash mismatch'
checks = validate(json.loads(raw))
assert checks['case_count'] == entry['case_count'], 'Development count mismatch'
assert set(manifest['holdout']) == {'visibility', 'case_count', 'sha256'}, 'Public holdout metadata must not expose content'
assert len(manifest['holdout']['sha256']) == 64, 'Invalid holdout hash'
print(json.dumps({'status': 'passed', 'development': checks, 'holdout': 'Content deliberately not inspected; public metadata checked only.'}, indent=2))
