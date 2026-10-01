#!/usr/bin/env python3
"""Execute frozen actual Android JNI cases; quality is assessed from preserved outputs separately."""
from pathlib import Path
import datetime,json,hashlib,subprocess,os,sys,zipfile,copy
R=Path(__file__).resolve().parents[3];F=Path(__file__).resolve().parent

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'downloads/multi-pack-answers'/datetime.datetime.now(datetime.timezone.utc).strftime('run-%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True);print(out,flush=True)
 def run(args,name,input=None,timeout=180):
  p=subprocess.run(list(map(str,args)),input=input,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout);(out/name).write_bytes(p.stdout)
  if p.returncode:raise RuntimeError('Command failed: '+str(out/name))
  return p.stdout
 tc=Path(os.environ.get('POCKETLORE_TOOLCHAIN','/home/isa/Android/atlas-toolchain'));a=[tc/'sdk/platform-tools/adb','-s','emulator-5560'];base='files/multi-pack-answer-tests'
 protocol=json.loads((F/'protocol.json').read_text());assert run(a+['shell','getprop','sys.boot_completed'],'boot.txt').strip()==b'1'
 run(a+['shell','getprop','ro.build.fingerprint'],'fingerprint.txt')
 saved=run(a+['shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf','files/knowledge.plpack'],'saved-before.txt');assert protocol['model']['sha256'].encode() in saved
 catalog=run(a+['exec-out','run-as','org.pocketlore.app','cat','files/pack-library/catalog.json'],'catalog-before.json');entries=json.loads(catalog)['collections'];assert len(entries)==2 and all(e['active'] for e in entries)
 assert {e['sha256'] for e in entries}=={p['sha256'] for p in protocol['packs']}
 for pack in protocol['packs']:
  assert sha(R/pack['path'])==pack['sha256']
  result=run(a+['shell','run-as','org.pocketlore.app','sha256sum','files/pack-library/'+pack['sha256']+'.plpack'],'pack-'+pack['id']+'.txt');assert result.decode().split()[0]==pack['sha256']
 # Deterministic duplicate edition: real licensed passage bytes unchanged; test-only edition ID.
 source=R/protocol['packs'][0]['path']
 with zipfile.ZipFile(source) as z:files={n:z.read(n) for n in z.namelist()}
 manifest=json.loads(files['manifest.json']);manifest['id']='duplicate-reference-test-only';files['manifest.json']=json.dumps(manifest).encode()
 duplicate=out/'duplicate.plpack'
 with zipfile.ZipFile(duplicate,'w',compression=zipfile.ZIP_DEFLATED) as z:
  for n,b in files.items():info=zipfile.ZipInfo(n,(2026,10,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b)
 run(['bash',R/'tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',F/'source.gradle','-PpocketloreTestRunner=org.pocketlore.app.AnswerLibraryInstrumentation'],'build.log')
 artifacts={}
 for name in ['debug/app-debug.apk','androidTest/debug/app-debug-androidTest.apk']:
  p=R/'android/app/build/outputs/apk'/name;artifacts[p.name]={'sha256':sha(p),'bytes':p.stat().st_size};run(a+['install','-r',p],'install-'+p.name+'.txt')
 run(a+['shell','am','force-stop','org.pocketlore.app'],'stop.txt');run(a+['shell','run-as','org.pocketlore.app','mkdir','-p',base],'mkdir.txt')
 for name,p in [('protocol.json',F/'protocol.json'),('link-repair-protocol.json',F/'link-repair-protocol.json'),('duplicate.plpack',duplicate)]:run(a+['exec-in','run-as','org.pocketlore.app','sh','-c','cat > '+base+'/'+name],'provision-'+name+'.txt',p.read_bytes())
 run(a+['shell','settings','put','global','airplane_mode_on','1'],'airplane-set.txt');run(a+['shell','svc','wifi','disable'],'wifi-disable.txt');run(a+['shell','svc','data','disable'],'data-disable.txt');assert run(a+['shell','settings','get','global','airplane_mode_on'],'airplane.txt').strip()==b'1'
 log=run(a+['shell','am','instrument','-w','org.pocketlore.app.test/org.pocketlore.app.AnswerLibraryInstrumentation'],'instrumentation.txt',timeout=900)
 raw=run(a+['exec-out','run-as','org.pocketlore.app','cat',base+'/results.json'],'results.json');r=json.loads(raw)
 saved_after=run(a+['shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf','files/knowledge.plpack'],'saved-after.txt');assert saved==saved_after
 restored=run(a+['exec-out','run-as','org.pocketlore.app','cat','files/pack-library/catalog.json'],'catalog-after.json');assert restored==catalog
 for row in r.get('rows',[]):
  run(a+['exec-out','run-as','org.pocketlore.app','cat',base+'/'+row['id']+'.json'],row['id']+'.json')
 for link in r.get('links',[]):run(a+['exec-out','run-as','org.pocketlore.app','cat',base+'/'+link['case']+'-citation.png'],link['case']+'-citation.png')
 receipt={'classification':'Actual x86_64 Android emulator JNI, production Qwen2.5 0.5B; not host/phone acceptance','protocol_sha256':sha(F/'protocol.json'),'link_repair_protocol_sha256':sha(F/'link-repair-protocol.json'),'model':protocol['model'],'duplicate_sha256':sha(duplicate),'artifacts':artifacts,'sources':{str(p.relative_to(R)):sha(p) for p in list((R/'android/app/src/main/java/org/pocketlore/app').glob('*.java'))+[F/'AnswerLibraryInstrumentation.java',R/'android/app/src/main/cpp/runtime.cpp']},'records':{p.name:sha(p) for p in out.iterdir() if p.is_file()}}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 verify(out,r,protocol,log)
def verify(out,r,protocol,log):
 assert r['catalog_restored'] and r['model']==protocol['model']
 assert 'threads=2' in r['runtime'] and 'context=2048' in r['runtime'] and 'HOST SCREEN' not in r['runtime']
 rows={row['id']:row for row in r['rows']};assert set(rows)=={c['id'] for c in protocol['cases']}|{'cancel-prefill'}|{c['id'] for c in json.loads((F/'link-repair-protocol.json').read_text())['cases']}
 original={ 'p'+s['edition_sha256']+'_'+s['original_id']:s for s in protocol['sources']}
 for row in rows.values():
  assert row['prompt_tokens']+256<=2048 and row['tokens']<=256 and row['native_after'][1]==0
  for h in row['retrieved']:
   # Duplicate aliases use the stable original canonical edition here.
   source=original[h['id']];assert [h[k] for k in ['title','url','date','rights','text']]==source['row'][1:]
   assert source['source_sha256'] in h['provenance'] and source['passage_sha256'] in h['provenance']
   assert h['id'].split('_')[0][1:] in row['active']
  if row['invoked'] and row['route']!='CANCELLED':assert row['tokens']>0 and row['first_token_ms']>0 and row['raw']
 for id in ['disabled-science','absent']:assert rows[id]['route']=='ABSTAINED' and not rows[id]['invoked']
 assert rows['duplicate']['prompt']==rows['reference']['prompt'] and rows['duplicate']['passages']==210 and rows['duplicate']['documents']==18
 assert rows['cancel-prefill']['route']=='CANCELLED' and r['cancellation']['observed_operation'][0]==4
 for id in ['after-cancel','after-reload']:assert rows[id]['invoked'] and rows[id]['route']!='CANCELLED'
 assert all(rows[l['case']]['route']=='GENERATED' and l['citation'] in rows[l['case']]['text'] and l['citation'] in l['visible'] for l in r['links'])
 assert len(r['samples'])>10 and any(s['native'][1]>0 and sum(s['native'][2:])>0 for s in r['samples'])
 summary={'status':r['status'],'routes':{id:row['route'] for id,row in rows.items()},'invoked_requests':sum(row['invoked'] for row in rows.values()),'generated_citation_dialogs':len(r['links']),'cancel_click_to_idle_ms':r['cancellation']['click_to_idle_ms'],'peak_pss_kib':max(s['pss_kib'] for s in r['samples']),'peak_rss_kib':max(s['VmRSS'] for s in r['samples']),'peak_swap_kib':max(s['VmSwap'] for s in r['samples']),'peak_java_used_bytes':max(s['java_used_bytes'] for s in r['samples']),'native_buffer_peak_bytes':max(sum(s['native'][2:]) for s in r['samples']),'limitations':'Behavior/integrity checks only; source-support/completeness/usefulness must be reviewed separately; no phone or OS OOM acceptance.'}
 (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2),flush=True)
 assert r.get('status')=='PASS' and len(r['links'])>0 and b'INSTRUMENTATION_CODE: -1' in log,str(out/'results.json')
if __name__=='__main__':
 if len(sys.argv)==3 and sys.argv[1]=='--verify-recorded':
  out=Path(sys.argv[2]);receipt=json.loads((out/'receipt.json').read_text())
  for name,digest in receipt['records'].items():assert sha(out/name)==digest,name
  for name,digest in receipt['sources'].items():assert sha(R/name)==digest,name
  assert sha(F/'protocol.json')==receipt['protocol_sha256']
  assert sha(F/'link-repair-protocol.json')==receipt['link_repair_protocol_sha256']
  verify(out,json.loads((out/'results.json').read_text()),json.loads((F/'protocol.json').read_text()),(out/'instrumentation.txt').read_bytes())
 else:main()
