"""Complete fixed-root retained accounting; no parser, JVM or external writes."""
import pathlib,os,json
ROOT=pathlib.Path(__file__).resolve().parents[3];BASE=pathlib.Path(__file__).resolve().parent
CONTROL_ROOTS=(pathlib.Path('/home/isa/PocketLore-control/continue-20261006/document-source-recovery'),pathlib.Path('/home/isa/PocketLore-control/continue-20261006/document-source-accounting'),pathlib.Path('/home/isa/PocketLore-control/continue-20261006/document-inmemory-central-directory'),pathlib.Path('/home/isa/PocketLore-control/continue-20261006/document-nullable-refusal-receipts'))
def need(ok,guard):
 if not ok:raise ValueError(guard)
def scan(roots,required):
 need(tuple(roots)==tuple(required),'required-root-roster');entries={}
 for root in roots:
  need(root.is_absolute() and root.exists() and root.is_dir(),'required-root-missing')
  need(not root.is_symlink() and root.resolve()==root,'root-symlink')
  for p in sorted(root.rglob('*')):
   need(not p.is_symlink(),'entry-symlink')
   if p.is_file():
    s=p.stat();entries[str(p)]={'bytes':s.st_size,'version':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]}
 return entries
def controls(roots=CONTROL_ROOTS):return scan(roots,CONTROL_ROOTS)
def inventory_detail():
 entries=controls();roots=[ROOT/'downloads/document-format-source-recovery-551',ROOT/'downloads/document-format-source-recovery-552',ROOT/'downloads/document-format-source-recovery-553',ROOT/'downloads/document-format-source-recovery-554',BASE]
 entries.update(scan(roots,roots))
 recovered=json.loads((BASE/'recovery552.json').read_text());paths={ROOT/p for p in recovered['files']}
 paths.add(ROOT/'android/app/src/main/java/org/pocketlore/app/DocumentZip.java')
 paths.update(ROOT/p for p in ['FINDINGS.md','docs/RELEASE_GAPS.md','THIRD_PARTY_NOTICES','docs/evidence/document-format-source-recovery.md','docs/evidence/document-format-source-recovery-review.json'])
 runtime=pathlib.Path('/home/isa/PocketLore-control/runtime')
 for n in ['551-documents-host-run-request.json','551-documents-host-run-result.json','552-documents-host-run-request.json','552-documents-host-run-result.json','553-documents-host-run-request.json','553-documents-host-run-result.json']:
  p=runtime/n;need(p.is_file() and not p.is_symlink(),'retained-runtime-missing');paths.add(p)
 for n in ['554-documents-host-run-request.json','554-documents-host-run-result.json']:
  p=runtime/n
  if p.exists():paths.add(p)
 for p in paths:
  if p.exists():
   need(not p.is_symlink() and p.resolve()==p,'inventory-symlink');s=p.stat();entries[str(p)]={'bytes':s.st_size,'version':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]}
 # Old source/docs are separately charged by immutable Git bytes even when a pathname is replaced.
 old=sum(v['bytes'] for v in recovered['old551_git_snapshot'].values())+sum(v['bytes'] for v in json.loads((BASE/'recovery553.json').read_text())['old552_git_snapshot'].values())+sum(v['bytes'] for v in json.loads((BASE/'recovery554.json').read_text())['old553_git_snapshot'].values())
 return {'entries':entries,'retained_files_bytes':sum(v['bytes'] for v in entries.values()),'old551_git_bytes':old,'parent_reserves':131072,'total':sum(v['bytes'] for v in entries.values())+old+131072}

def verify_old_snapshot():
 import subprocess,hashlib
 recovered=json.loads((BASE/'recovery552.json').read_text())
 snapshots=list(recovered['old551_git_snapshot'].items())+list(json.loads((BASE/'recovery553.json').read_text())['old552_git_snapshot'].items())+list(json.loads((BASE/'recovery554.json').read_text())['old553_git_snapshot'].items())
 for path,value in snapshots:
  need(len(value['commit'])==40,'snapshot-commit')
  data=subprocess.check_output(['git','show',value['commit']+':'+path],cwd=ROOT)
  need(len(data)==value['bytes'] and hashlib.sha256(data).hexdigest()==value['sha256'],'snapshot-byte-authority')
 return sum(v['bytes'] for _,v in snapshots)
