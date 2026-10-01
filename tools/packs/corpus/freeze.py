#!/usr/bin/env python3
"""Seal a validated private stage with a SHA256 inventory; never publish bulk data."""
import argparse, json, pathlib
from acquire import filehash, now, save

def freeze(stage):
 if (stage/'ARTIFACTS.json').exists(): raise ValueError('Snapshot already sealed')
 tests=json.loads((stage/'tests.json').read_text())
 if not tests['success'] or tests['skipped']: raise ValueError('Passing, unskipped mutation tests required')
 if not (stage/'license-provenance.json').is_file(): raise ValueError('License manifest required')
 validation=json.loads((stage/'validation.json').read_text())
 if not validation.get('all_source_texts_match_pinned_upstream'): raise ValueError('Full upstream validation required')
 files={str(p.relative_to(stage)):{'sha256':filehash(p),'bytes':p.stat().st_size} for p in sorted(stage.rglob('*')) if p.is_file()}
 save(stage/'ARTIFACTS.json',{'sealed_at':now(),'files':files})
 result={'path':str(stage.resolve()),'inventory_sha256':filehash(stage/'ARTIFACTS.json'),'files':len(files),'bytes':sum(v['bytes'] for v in files.values())}
 for p in stage.rglob('*'):
  if p.is_file(): p.chmod(0o444)
 for p in sorted(stage.rglob('*'),reverse=True):
  if p.is_dir(): p.chmod(0o555)
 stage.chmod(0o555)
 print(json.dumps(result,indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__); p.add_argument('stage',type=pathlib.Path); args=p.parse_args(); freeze(args.stage)
