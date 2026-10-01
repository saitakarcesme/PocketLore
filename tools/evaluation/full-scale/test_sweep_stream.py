#!/usr/bin/env python3
"""Real FIFO EOF and invalid metadata-only admission; no full-install claim."""
import pathlib,subprocess,time,zipfile,json,io,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[3];OUT=ROOT/'downloads/full-scale/sweep/stream-negatives';ADB=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5560']
def run():
 OUT.mkdir(exist_ok=False)
 original=(ROOT/'downloads/full-scale/fixtures/base.plscale').read_bytes();cases={'truncated-payload':original[:len(original)//2]}
 with zipfile.ZipFile(io.BytesIO(original)) as source:
  m=json.loads(source.read('manifest.json'));m.update(shards=[],documents=0,full_articles=0,leads=0,metadata_only=False)
  b=io.BytesIO()
  with zipfile.ZipFile(b,'w') as dest:
   dest.writestr('manifest.json',json.dumps(m,sort_keys=True));
   for name in source.namelist()[1:]:dest.writestr(name,source.read(name))
  cases['unmarked-empty-shards']=b.getvalue()
 receipt=[]
 for label,data in cases.items():
  with (OUT/(label+'.log')).open('w') as log:
   p=subprocess.Popen(ADB+['shell','am','instrument','-w','-e','label',label,'-e','smoke','true','org.pocketlore.app.test/org.pocketlore.app.ShardSweepInstrumentation'],stdout=log,stderr=subprocess.STDOUT)
   for _ in range(120):
    if subprocess.run(ADB+['shell','run-as','org.pocketlore.app','test','-p','files/sweep-input'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:break
    if p.poll() is not None:raise RuntimeError('No FIFO')
    time.sleep(.25)
   else:raise RuntimeError('FIFO timeout')
   start=time.monotonic();writer=subprocess.run(ADB+['shell',"run-as org.pocketlore.app sh -c 'cat > files/sweep-input'"],input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30);p.wait(timeout=30)
  text=(OUT/(label+'.log')).read_text();assert 'INSTRUMENTATION_CODE: 1' in text and 'failure=' in text
  assert ('EOF' in text.upper()) if label=='truncated-payload' else ('Shard admission' in text)
  listing=subprocess.check_output(ADB+['shell','run-as','org.pocketlore.app','find','files/sweep-owned','-type','f'],text=True);assert not listing.strip(),listing
  receipt.append(dict(case=label,expected='reject and retain empty owned catalog',status='PASS',input_bytes=len(data),input_sha256=hashlib.sha256(data).hexdigest(),writer_exit=writer.returncode,ms=(time.monotonic()-start)*1000,remaining_files=listing))
 (OUT/'results.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print('PASS: actual FIFO premature EOF and unmarked empty-shard rejection; no committed sweep files')
if __name__=='__main__':run()
