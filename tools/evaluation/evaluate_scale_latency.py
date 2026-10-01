#!/usr/bin/env python3
"""Real Android imports and serial JNI measurements; immutable public protocol."""
import datetime,hashlib,json,math,os,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/evaluation/scale-latency'))
from make_fixtures import make
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def percentiles(values):
 s=sorted(values);return {'n':len(s),'p50':s[math.ceil(.5*len(s))-1],'p95':s[math.ceil(.95*len(s))-1],'min':s[0],'max':s[-1]}
def main():
 out=ROOT/'downloads/scale-latency'/datetime.datetime.now(datetime.timezone.utc).strftime('run-%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True);print(out,flush=True)
 def run(args,name,input=None,timeout=180):
  p=subprocess.run(list(map(str,args)),input=input,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout);(out/name).write_bytes(p.stdout)
  if p.returncode:raise RuntimeError('Command failed: '+str(out/name))
  return p.stdout
 protocol=ROOT/'tools/evaluation/scale-latency/protocol.json';assert sha(protocol)=='1b656778fcdbb093b7be044789aef4e8a0950d092e5c1ada982065ae68aeccb5';spec=json.loads(protocol.read_text());assert make(out/'fixtures')==spec['fixtures']
 tc=Path(os.environ.get('POCKETLORE_TOOLCHAIN','/home/isa/Android/atlas-toolchain'));adb=[tc/'sdk/platform-tools/adb','-s','emulator-5560']
 assert run(adb+['shell','getprop','sys.boot_completed'],'boot.txt').strip()==b'1'
 run(adb+['shell','getprop','ro.build.fingerprint'],'fingerprint.txt');run(adb+['shell','cat','/proc/meminfo'],'emulator-meminfo-before.txt');(out/'host-meminfo.txt').write_bytes(Path('/proc/meminfo').read_bytes())
 before=run(adb+['shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf','files/knowledge.plpack'],'saved-before.txt');assert before.decode().split()[0]==spec['model_sha256']
 run(['bash',ROOT/'tools/android-build.sh','assembleDebug','assembleDebugAndroidTest','-I',ROOT/'tools/evaluation/scale-latency/source.gradle','-PpocketloreTestRunner=org.pocketlore.app.ScaleLatencyInstrumentation'],'build.log')
 artifacts={}
 for sub in ['debug/app-debug.apk','androidTest/debug/app-debug-androidTest.apk']:
  p=ROOT/'android/app/build/outputs/apk'/sub;artifacts[p.name]={'sha256':sha(p),'bytes':p.stat().st_size};shutil.copyfile(p,out/p.name);run(adb+['install','-r',p],'install-'+p.name+'.txt')
 run(adb+['shell','am','force-stop','org.pocketlore.app'],'stop.txt')
 run(adb+['shell','run-as','org.pocketlore.app','mkdir','-p','files/scale-latency-tests'],'mkdir.txt')
 for name,p in [('protocol.json',protocol),('reference.plpack',ROOT/'downloads/packs/english-reference.plpack')]+[(x['file'],out/'fixtures'/x['file']) for x in spec['fixtures']]:
  run(adb+['shell','run-as','org.pocketlore.app','sh','-c',"'cat > files/scale-latency-tests/"+name+"'"],'provision-'+name+'.txt',p.read_bytes())
 all_records=[];wall={}
 for mode,index in [('scale',i) for i in range(len(spec['fixtures']))]+[('warm',0)]+[('cold',i) for i in range(5)]:
  key=mode+'-'+str(index);print('Starting '+key,flush=True)
  run(adb+['shell','am','force-stop','org.pocketlore.app'],key+'-stop.txt')
  run(adb+['shell','run-as','org.pocketlore.app','rm','-f','files/scale-latency-tests/'+key+'.json'],key+'-clear.txt')
  begin=time.monotonic();log=run(adb+['shell','am','instrument','-w','-e','mode',mode,'-e','index',str(index),'org.pocketlore.app.test/org.pocketlore.app.ScaleLatencyInstrumentation'],key+'-instrumentation.txt',timeout=900);wall[key]=(time.monotonic()-begin)*1000
  raw=run(adb+['exec-out','run-as','org.pocketlore.app','cat','files/scale-latency-tests/'+key+'.json'],key+'.json');r=json.loads(raw)
  run(adb+['shell','dumpsys','meminfo','org.pocketlore.app'],key+'-post-dumpsys.txt')
  assert b'INSTRUMENTATION_CODE: -1' in log and r.get('status')=='PASS',str(out/(key+'.json'))
  assert r['final_native'][:2]==[0,0] and r['samples'] and all(x['pss_kib']>0 and x['VmRSS_kib']>0 and 'VmSwap_kib' in x for x in r['samples'])
  all_records.append(r);print('Finished '+key,flush=True)
 after=run(adb+['shell','run-as','org.pocketlore.app','sha256sum','files/model.gguf','files/knowledge.plpack'],'saved-after.txt');assert before==after
 run(adb+['shell','cat','/proc/meminfo'],'emulator-meminfo-after.txt')
 scale=[r for r in all_records if r['mode']=='scale'];warm=next(r for r in all_records if r['mode']=='warm');cold=[r for r in all_records if r['mode']=='cold']
 assert len(set(r['pid'] for r in all_records))==len(all_records),'Not distinct processes'
 assert len(warm['rows'])==11 and warm['rows'][0]['warmup'] and len(cold)==5 and all(len(r['rows'])==1 for r in cold)
 for r in scale:
  f=spec['fixtures'][r['index']];assert r['accepted']==(f['expected']=='accept') and r['stage_cleanup'] and r['old_index_survived']
  if r['accepted']:assert r['new_index_counts'][0]==f['passages'] and r['candidates_scored']>0
  else:assert 'size limit' in r['failure']
 for r in [warm,*cold]:
  for row in r['rows']:
   assert row['invoked'] and row['tokens']>0 and row['raw_draft'] and 0<row['request_first_token_ms']<=row['request_total_ms'] and row['retrieval_ms']>=0
 groups={'warm':[x for x in warm['rows'] if not x['warmup']],'process_cold':[r['rows'][0] for r in cold]}
 stats={name:{k:percentiles([x[k] for x in rows]) for k in ['retrieval_ms','request_first_token_ms','request_total_ms']} for name,rows in groups.items()}
 stats['process_cold']['model_load_ms']=percentiles([r['model_load_ms'] for r in cold]);stats['process_cold']['pack_load_ms']=percentiles([r['pack_load_ms'] for r in cold]);stats['process_cold']['ready_to_result_ms']=percentiles([r['rows'][0]['since_process_ready_ms'] for r in cold])
 metrics=[]
 for r in scale:
  def last(phase):return [s for s in r['samples'] if s['phase']==phase][-1]
  before=last('before-import');after=last('old-and-new-index-retained' if r['accepted'] else 'after-rejection')
  metrics.append({'copies':r['fixture']['copies'],'passages':r['fixture']['passages'],'accepted':r['accepted'],'import_ms':r['import_ms'],'pss_before_kib':before['pss_kib'],'pss_after_kib':after['pss_kib'],'java_delta_bytes':after['java_used_bytes']-before['java_used_bytes'],'sampled_peak_pss_kib':max(s['pss_kib'] for s in r['samples']),'sampled_peak_rss_kib':max(s['VmRSS_kib'] for s in r['samples']),'sampled_peak_swap_kib':max(s['VmSwap_kib'] for s in r['samples']),'sampled_stage_bytes':max(s['stage_bytes'] for s in r['samples'])})
 summary={'status':'PASS','environment':'CPU API35 x86_64 emulator, not phone/thermal acceptance','artifacts':artifacts,'protocol_sha256':sha(protocol),'model_sha256':spec['model_sha256'],'percentile_definition':spec['definitions']['percentile'],'latency_ms':stats,'scale':metrics,'routes':{g:[x['kind'] for x in rows] for g,rows in groups.items()},'instrumentation_wall_ms':wall,'record_sha256':{r['mode']+'-'+str(r['index']):sha(out/(r['mode']+'-'+str(r['index'])+'.json')) for r in all_records}}
 (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':main()
