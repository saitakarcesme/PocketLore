"""Derive once from clean pinned public source; never dirty the shared checkout."""
import hashlib,json,pathlib,subprocess,sys,tarfile
ROOT=pathlib.Path(__file__).resolve().parents[3]
def main(out):
 spec=json.loads(pathlib.Path(__file__).with_name('identity.json').read_text());src=ROOT/'downloads/runtime/llama.cpp';patch=pathlib.Path(__file__).with_name('lazy-mmap.patch')
 assert subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD']).decode().strip()==spec['base_revision']
 assert not subprocess.check_output(['git','-C',str(src),'status','--porcelain','--untracked-files=all'])
 assert hashlib.sha256(patch.read_bytes()).hexdigest()==spec['patch_sha256'];out.mkdir(parents=True,exist_ok=False)
 archive=out/'source.tar'
 with archive.open('wb') as f:subprocess.run(['git','-C',str(src),'archive',spec['base_revision']],stdout=f,check=True)
 derived=out/'source';derived.mkdir()
 with tarfile.open(archive) as t:t.extractall(derived,filter='data')
 subprocess.run(['git','apply','--check',str(patch.resolve())],cwd=derived,check=True);subprocess.run(['git','apply',str(patch.resolve())],cwd=derived,check=True)
 files={n:hashlib.sha256((derived/n).read_bytes()).hexdigest() for n in ['include/llama.h','src/llama-model.cpp','src/llama-mmap.cpp','LICENSE']}
 (out/'derivation.json').write_text(json.dumps({'base':spec,'files':files,'source_archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'shared_checkout_unchanged':not bool(subprocess.check_output(['git','-C',str(src),'status','--porcelain']))},indent=2))
 print(derived)
if __name__=='__main__':main(pathlib.Path(sys.argv[1]))
