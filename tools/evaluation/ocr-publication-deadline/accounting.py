"""Exact mandatory-root accounting; reserves never replace actual retained bytes."""
import os,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[3]
MANDATORY_ROOTS=(ROOT/'downloads/ocr-publication-deadline-557',pathlib.Path(__file__).resolve().parent,pathlib.Path('/home/isa/PocketLore-control/continue-20261007/ocr-publication-deadline'))
CAP=8388608;FILE_CAP=262144;RESERVES=131072
def scan_roots(roots,expected):
 roots=tuple(pathlib.Path(p) for p in roots);expected=tuple(pathlib.Path(p) for p in expected)
 if roots!=expected or len(set(roots))!=len(roots):raise ValueError('mandatory-root-roster')
 files={}
 for root in roots:
  if not root.is_dir() or root.is_symlink():raise ValueError('mandatory-root-missing')
  for p in sorted(root.rglob('*')):
   if p.is_symlink():raise ValueError('inventory-symlink')
   if p.is_file():
    s=p.stat()
    if s.st_size>FILE_CAP:raise ValueError('per-file-cap')
    files[str(p)]={'bytes':s.st_size,'version':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]}
 return files
