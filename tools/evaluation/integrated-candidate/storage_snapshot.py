import subprocess,json,pathlib,time,hashlib
root=pathlib.Path(__file__).resolve().parents[3]
out=root/'downloads'/('integrated-storage-'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime()));out.mkdir();adb='/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb'
for serial in ['emulator-5560','emulator-5562']:
 def run(args,name):
  r=subprocess.run([adb,'-s',serial]+args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(out/(serial+'-'+name)).write_bytes(r.stdout);assert r.returncode==0,(serial,name,r.stdout);return r
 run(['shell','run-as','org.pocketlore.app','sha256sum','files/attachment-assets/tessdata/eng.traineddata','files/attachment-assets/ggml-tiny.en.bin'],'recognition-hashes.txt')
 p=run(['shell','pm','path','org.pocketlore.app'],'apk-path.txt').stdout.decode().strip().removeprefix('package:')
 run(['shell','stat','-c','%s,%b',p],'apk-size-blocks.txt');run(['shell','du','-sk',str(pathlib.Path(p).parent)],'package-allocated.txt')
print(out)
