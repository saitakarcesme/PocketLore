"""Explicit full-catalog coexistence measurement on existing emulator-5562; no reset."""
import json,subprocess,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];ADB=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5562'];PKG='org.pocketlore.app'
def main():
 stamp=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime());out=ROOT/'downloads/attachments/budget'/stamp;out.mkdir(parents=True,exist_ok=False)
 def run(args,name,data=None):
  r=subprocess.run([str(x) for x in args],cwd=ROOT,input=data,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180);(out/name).write_bytes(r.stdout);assert r.returncode==0,(name,r.stdout);return r.stdout
 assert run(ADB+['get-state'],'state.txt').strip()==b'device'
 run(ADB+['shell','getprop'],'properties.txt');run(ADB+['shell','df','-k','/data'],'df-before.txt')
 before=run(ADB+['shell','run-as',PKG,'sha256sum','files/model.gguf','files/scale-library/catalog.json','files/pack-library/catalog.json'],'before.txt')
 for apk in ['debug/app-debug.apk','androidTest/debug/app-debug-androidTest.apk']:run(ADB+['install','-r',ROOT/'android/app/build/outputs/apk'/apk],'install-'+Path(apk).name+'.txt')
 run(ADB+['shell','run-as',PKG,'mkdir','-p','files/attachments-budget-input'],'mkdir.txt')
 sources={'eng.traineddata':'eng.traineddata','ggml-tiny.en.bin':'models/ggml-tiny.en.bin','text.png':'fixtures/text.png','speech.wav':'fixtures/speech.wav'}
 for name,relative in sources.items():run(ADB+['shell','run-as',PKG,'sh','-c',"'cat > files/attachments-budget-input/"+name+"'"],'transfer-'+name+'.txt',(ROOT/'downloads/attachments'/relative).read_bytes())
 directory='attachments-budget-'+stamp;log=run(ADB+['shell','am','instrument','-w','-e','mode','budget','-e','directory',directory,PKG+'.test/'+PKG+'.AttachmentsInstrumentation'],'instrumentation.txt')
 result=json.loads(run(ADB+['exec-out','run-as',PKG,'cat','files/'+directory+'/budget.json'],'budget.json'));assert result['status']=='PASS' and b'ATTACHMENTS_BUDGET_PASS' in log
 after=run(ADB+['shell','run-as',PKG,'sha256sum','files/model.gguf','files/scale-library/catalog.json','files/pack-library/catalog.json'],'after.txt');assert before==after
 rows=[]
 for pkg in [PKG,PKG+'.test']:
  paths=run(ADB+['shell','pm','path',pkg],pkg+'-path.txt').decode().splitlines();assert len(paths)==1
  path=paths[0].removeprefix('package:');raw=run(ADB+['shell','du','-sk',str(Path(path).parent)],pkg+'-code.txt');digest=run(ADB+['shell','sha256sum',path],pkg+'-apk-hash.txt').decode().split()[0]
  rows.append({'package':pkg,'apk_sha256':digest,'allocated_code_bytes':int(raw.split()[0])*1024})
 data=int(run(ADB+['shell','run-as',PKG,'du','-sk','.'],'app-data.txt').split()[0])*1024
 run(ADB+['shell','df','-k','/data'],'df-after.txt');run(ADB+['shell','cat','/proc/meminfo'],'guest-memory.txt')
 receipt={'environment':'emulator-5562; current APK, retained full catalog, optional OCR and speech','packages':rows,'app_allocated_bytes':data,'installed_with_test_code_bytes':data+sum(x['allocated_code_bytes'] for x in rows),'result_sha256':hashlib.sha256((out/'budget.json').read_bytes()).hexdigest(),'saved_model_and_catalogs_unchanged':True,'limit':'Observed optional-asset import peak; not a rerun of full shard update or APK update transient peak'}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');assert receipt['installed_with_test_code_bytes']<45_000_000_000;assert result['sampled_import_app_allocated_peak_bytes']+sum(x['allocated_code_bytes'] for x in rows)<50_000_000_000
 print(json.dumps({'output':str(out),**receipt},indent=2))
if __name__=='__main__':main()
