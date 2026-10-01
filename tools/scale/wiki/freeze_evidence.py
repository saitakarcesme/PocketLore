#!/usr/bin/env python3
"""Seal completed edition receipts and checks without scanning private control state."""
import argparse
import datetime
import json
import pathlib
import time

from acquire import atomic, digest

p = argparse.ArgumentParser()
p.add_argument('lane')
p.add_argument('output')
a = p.parse_args()
lane = pathlib.Path(a.lane).resolve()
output = pathlib.Path(a.output)
if output.exists():
    raise SystemExit('Refuse to replace sealed evidence')

required = [lane / 'SOURCE_ARTIFACT_INVENTORY.json']
required += [lane / 'receipts' / name for name in [
    'final-verification.json', 'final-source-audit.json',
    'final-queries-80.json', 'final-queries-tail-16.json',
    'final-seal-check.json',
]]
for path in required:
    if not path.is_file():
        raise SystemExit('Missing final evidence: ' + str(path))

paths = set(required)
for pattern in ['*/progress.json', '*/orphan-*.blocks']:
    paths.update((lane / 'edition-v7').glob(pattern))
for pattern in ['edition-v7-*', 'final-*', 'alias-normalization.log',
                'source-and-prototype-seal.log']:
    for path in (lane / 'receipts').glob(pattern):
        if path.is_file() and path.suffix in ['.json', '.jsonl', '.log']:
            paths.add(path)
alias_report = lane / 'redirect-aliases-normalized.sqlite.json'
if alias_report.is_file():
    paths.add(alias_report)
for name in ['redirect-aliases-pre-normalization.sqlite',
             'redirect-aliases-pre-normalization.json']:
    archived_parent = lane / 'receipts' / name
    if archived_parent.is_file():
        paths.add(archived_parent)
start = time.monotonic()
entries = []
for path in sorted(paths):
    before = path.stat()
    sha = digest(path)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise RuntimeError('Evidence changed during sealing: ' + str(path))
    entries.append({'path': str(path), 'bytes': after.st_size, 'sha256': sha})

result = {
    'schema': 1,
    'sealed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'files': entries,
    'files_count': len(entries),
    'bytes': sum(x['bytes'] for x in entries),
    'seconds': time.monotonic() - start,
    'scope': 'Explicit completed encyclopedia build receipts and final checks; no planning history, supervisor state, holdout or private conversations',
    'meaning': 'Hashes preserve successes and failures; inclusion is not an assertion that each recorded check passed',
}
atomic(output, result)
print(json.dumps({k: v for k, v in result.items() if k != 'files'}, indent=2))
