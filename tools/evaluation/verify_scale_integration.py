#!/usr/bin/env python3
"""Verify the measured browse/JNI milestone; never clears full-product quality or rights gates."""
import hashlib,json,pathlib,subprocess,tempfile,shutil,datetime,sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
E=ROOT/'docs/evidence/scale-integration'
ADB=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5560']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def checked(p,spec):
 if not p.is_file() or p.stat().st_size!=spec['bytes'] or sha(p)!=spec['sha256']:raise ValueError('Missing/changed artifact: '+str(p))
def require(ok,why):
 if not ok:raise ValueError(why)
def behavior(directory):
 n=json.loads((directory/'negative.json').read_text());i=json.loads((directory/'inspect.json').read_text());u=json.loads((directory/'ui.json').read_text());g=json.loads((directory/'native.json').read_text())
 require(all(x['status']=='PASS' for x in (n,i,u,g)),'Android behavior failed')
 require({x['case'] for x in n['checks']}=={'corrupt','cancel-before','cancel-during','over-budget'},'Import negative population changed')
 require(n['same_process_retry'] and n['changed_source_block_rejected'] and n['retained_collections']==2,'Import rollback/retry')
 require(i['active_restart_count']==2 and i['oversized']['raw_block_bytes']==23473862,'Actual installed shard/oversized record missing')
 require(i['oversized_sampled_peak']['samples']>0 and i['oversized_sampled_peak']['java_used_bytes']<64*1024*1024,'Source reader Java allocation regression')
 require(i['large_read_cancel_ms']<2000 and i['readonly_rejection'],'Cancellation/read-only failure')
 protocol=json.loads((ROOT/'tools/evaluation/scale-integration/protocol.json').read_text())
 require([x['query'] for x in i['wiki_queries']]==protocol['wiki_queries'] and [x['query'] for x in i['cities']]==protocol['cities'],'Frozen query population changed')
 require([x['question'] for x in i['absent_controls']]==protocol['absent_controls'][:3] and all(not x['generation_allowed'] for x in i['absent_controls']),'Absent generation gate failed')
 require(i['oversized_metadata_rejected'] and i['running_index_cancel_ms']<2000,'Allocation/index cancellation gate')
 require(i['absent_category'].startswith('withheld'),'Absent category leak')
 require(u['active_selection_ui_persisted'] and 'Citation identity:' in u['wiki_dialog'] and 'not cleared' in u['wiki_dialog'],'Actual source/active controls failed')
 require('Routing unavailable' in u['place_dialog'] and 'unknown' in u['place_dialog'],'Fabricated live availability')
 require(g['model_sha256']=='74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db' and g['reload'] and g['cancel_reset'],'Production identity/lifecycle drift')
 require(g['answer']['invoked'] and g['answer']['draft'] and g['bulk_hits_while_model_loaded']>0,'Actual JNI/bulk coexistence missing')
 # These are structural/lifecycle checks; the builder source assessment remains separate.
 require(g['answer']['route'] in {'GENERATED','FALLBACK','ABSTAINED'},'Invalid production route')
def main():
 seal=json.loads((E/'candidate.json').read_text())
 for path,spec in seal['artifacts'].items():checked(ROOT/path,spec)
 for kind in ('wiki','places'):
  receipt=json.loads((E/(kind+'-receipt.json')).read_text())
  checked(ROOT/'downloads/scale-integration'/ (kind+'-first.plscale'),{'bytes':receipt['archive_bytes'],'sha256':receipt['archive_sha256']})
  require(receipt['manifest']['generation_allowed'] is False,'Unreviewed generation enabled')
  for f in receipt['manifest']['files']:
   remote='files/scale-library/'+receipt['manifest_sha256']+'/'+f['path']
   got=subprocess.check_output(ADB+['shell','run-as','org.pocketlore.app','sha256sum',remote],text=True).split()[0]
   require(got==f['sha256'],'Installed asset changed: '+remote)
 behavior(E/'final-run-5')
 require(json.loads((E/'final-run-5/run.json').read_text())['packages']['org.pocketlore.app']==seal['artifacts']['android/app/build/outputs/apk/debug/app-debug.apk']['sha256'],'Sealed execution APK mismatch')
 # Real copied artifacts, not injected boolean successes. Original evidence/weights stay intact.
 with tempfile.TemporaryDirectory(prefix='pocketlore-scale-integrity-') as d:
  for relative in ('docs/evidence/scale-integration/final-run-5/native.json','downloads/answers/model/qwen2.5-0.5b-instruct-q4_k_m.gguf'):
   spec=seal['artifacts'][relative];copy=pathlib.Path(d)/pathlib.Path(relative).name;shutil.copyfile(ROOT/relative,copy);checked(copy,spec)
   with copy.open('r+b') as f:f.seek(copy.stat().st_size//2);v=f.read(1);f.seek(-1,1);f.write(bytes([v[0]^1]))
   try:checked(copy,spec)
   except ValueError:pass
   else:raise ValueError('Changed actual artifact accepted')
   copy.unlink()
   try:checked(copy,spec)
   except ValueError:pass
   else:raise ValueError('Missing actual artifact accepted')
 apk='android/app/build/outputs/apk/debug/app-debug.apk'
 path=subprocess.check_output(ADB+['shell','pm','path','org.pocketlore.app'],text=True).strip().removeprefix('package:')
 actual=subprocess.check_output(ADB+['shell','sha256sum',path],text=True).split()[0]
 require(actual==seal['artifacts'][apk]['sha256'],'Installed APK differs from tested build')
 require(subprocess.check_output(ADB+['shell','settings','get','global','airplane_mode_on'],text=True).strip()=='1','Offline fixture airplane mode changed')
 out=ROOT/'downloads/scale-integration'/('verification-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
 subprocess.run([sys.executable,str(ROOT/'tools/evaluation/scale-integration/run_android.py'),'negative','inspect','ui','native','--output',str(out)],check=True,cwd=ROOT)
 behavior(out)
 print('PASS: measured first-shard offline browse/import/recovery and production JNI coexistence. Full inventory, rights clearance, bulk generated-answer support, physical and unseen competitive gates remain OPEN.')
 print('Fresh observations:',out)
if __name__=='__main__':
 try:main()
 except Exception as e:print('FAIL:',e,file=sys.stderr);sys.exit(1)
