"""Bounded offline host-JVM execution of production storage/model-copy code."""
import hashlib,json,pathlib,subprocess,time,uuid
root=pathlib.Path(__file__).resolve().parents[3]
out=root/'downloads/storage-reservations'/(time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
fixture=root/'docs/evidence/storage-reservations/fixtures.json'
assert hashlib.sha256(fixture.read_bytes()).hexdigest()=='cc03dad2c6e839fbf4de37d56376fd2e03a3e9d6df7be3eef7de190724f54be5'
sources=[root/'android/app/src/main/java/org/pocketlore/app'/n for n in ['ResourceStorage.java','ModelImport.java']]+[pathlib.Path(__file__).with_name('StorageReservationCheck.java')]
jdk=pathlib.Path('/home/isa/Android/atlas-toolchain/jdk/bin')
def run(args,name):
 p=subprocess.run([str(a) for a in args],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
 (out/name).write_bytes(p.stdout);(out/(name+'.json')).write_text(json.dumps({'command':[str(a) for a in args],'returncode':p.returncode}))
 assert p.returncode==0,(name,p.stdout.decode());return p.stdout
run([jdk/'javac','-d',out/'classes',*sources],'compile.txt')
raw=run([jdk/'java','-Xmx128m','-XX:ActiveProcessorCount=2','-cp',out/'classes','org.pocketlore.app.StorageReservationCheck',out/'fixture-files'],'behavior.jsonl')
records=[json.loads(line) for line in raw.splitlines()]
assert [r['fixture'] for r in records]==[c['id'] for c in json.loads(fixture.read_text())['cases']]
assert all(r['status']=='PASS' for r in records)
# Negative controls compile actual modified production sources in isolated output directories.
# Removing concurrent accounting or release must fail the behavioral fixtures.
original=sources[0].read_text();negatives=[]
for label,old,new in [('omit-outstanding','held=Math.addExact(reserved,peak)','held=peak'),('leak-release','ledger.reserved-=bytes','ledger.reserved-=0')]:
 d=out/label;d.mkdir();altered=d/'ResourceStorage.java';assert old in original;altered.write_text(original.replace(old,new))
 run([jdk/'javac','-d',d/'classes',altered,*sources[1:]],label+'/compile.txt')
 p=subprocess.run([str(jdk/'java'),'-Xmx128m','-XX:ActiveProcessorCount=2','-cp',str(d/'classes'),'org.pocketlore.app.StorageReservationCheck',str(d/'fixture-files')],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
 (d/'negative.txt').write_bytes(p.stdout);assert p.returncode!=0;negatives.append({'mutation':label,'returncode':p.returncode})
identity_sources=sources+[root/'android/app/src/main/java/org/pocketlore/app'/n for n in ['StorageApplication.java','NativePanel.java','PackLibrary.java','PersonalDocuments.java','AttachmentAssets.java']]+[root/'android/app/src/main/AndroidManifest.xml']
receipt={'environment':'LLMRig host JVM; no Android/device execution','configuration':'2 active processors;128MiB Java heap; not measured total RSS','sources':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in identity_sources},'fixtures_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),'records':records,'negative_controls':negatives,'status':'PASS'}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'output':str(out),'status':'PASS'}))
