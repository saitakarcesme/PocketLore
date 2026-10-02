#!/usr/bin/env python3
"""Fail closed unless the new source edition and actual leased-device evidence agree."""
import copy,hashlib,json,pathlib,sys,tempfile,shutil,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[3];HERE=pathlib.Path(__file__).parent
sha=lambda data:hashlib.sha256(data).hexdigest()
def verify_run(out):
 m=json.loads((out/'manifest.json').read_text());assert m['serial']=='emulator-5564'
 for name,digest in m['files'].items():
  assert pathlib.Path(name).name==name and sha((out/name).read_bytes())==digest,('Missing/changed run artifact',name)
 assert (out/'api.txt').read_text().strip()=='37' and (out/'pages.txt').read_text().strip()=='16384'
 for name in ['boot','font','rotation','retained']:assert (out/(name+'-before.txt')).read_bytes()==(out/(name+'-after.txt')).read_bytes(),name+' changed'
 src=json.loads((out/'source-inputs.json').read_text());assert sha((out/'source-inputs.json').read_bytes())==m['source_hash'];assert src['inputs']==m['inputs_after']
 for name,digest in src['inputs'].items():assert sha((ROOT/name).read_bytes())==digest,('Current source differs from tested source',name)
 for key,info in m['apks'].items():
  assert sha(pathlib.Path(info['path']).read_bytes())==info['sha256'],'Changed built APK'
  for when in ['installed','final']:assert (out/(when+'-'+key+'.txt')).read_text().split()[0]==info['sha256'],'Installed APK mismatch'
 pack=ROOT/'downloads/reference-expansion/reference-expansion.plpack';assert sha(pack.read_bytes())==m['pack_sha256']
 with zipfile.ZipFile(pack) as z:edition=json.loads(z.read('manifest.json'));known={r.split('\t')[0]:r.split('\t') for r in z.read('passages.tsv').decode().splitlines()}
 legacy=ROOT/'downloads/general-research/reviewed-reference.plpack';assert sha(legacy.read_bytes())=='10bb8878270ac7b7aa65036a5fd71007c34b3721bc269ce77544d542f0f27656'
 with zipfile.ZipFile(legacy) as z:legacy_known={r.split('\t')[0]:r.split('\t') for r in z.read('passages.tsv').decode().splitlines()}
 cases=json.loads((HERE/'development.json').read_text())['cases']
 for mode in ['install','restart']:
  r=json.loads((out/(mode+'.json')).read_text());assert r['status']=='PASS' and r['run_id']==m['run_id'] and r['source_hash']==m['source_hash'] and r['pack_sha256']==m['pack_sha256']
  raw=(out/('runtime-'+mode+'.txt')).read_text();command=json.loads((out/('runtime-'+mode+'.txt.command.json')).read_text());assert command['returncode']==0 and 'INSTRUMENTATION_CODE: -1' in raw and 'Process crashed' not in raw
  transport=json.loads(next(x.split('=',1)[1] for x in raw.splitlines() if x.startswith('INSTRUMENTATION_RESULT: receipt=')));assert transport['run_id']==m['run_id'] and transport['source_hash']==m['source_hash'] and transport['report_sha256']==sha((out/(mode+'.json')).read_bytes())
  expected=cases if mode=='install' else cases[:1];assert len(r['outputs'])==len(expected)
  assert any(e['hash']==m['pack_sha256'] and e['active'] for e in r['active_catalog'])
  assert r['documents']>=len(edition['documents'])>=100
  assert r.get('source_inspected') is True,'Actual citation navigation absent'
  for c,row in zip(expected,r['outputs']):
   assert row['id']==c['id'] and row['question']==c['question'] and row['generated'] is False
   if c['absent']:assert row['quotes']==[],'Unavailable fact received quotations'
   rendered=row['rendered'].encode('utf-16-le')
   for q in row['quotes']:
    assert sha(q['text'].encode())==q['sha256'];assert rendered[q['display_start']*2:q['display_end']*2].decode('utf-16-le')==q['text']
    if q['id'].startswith('p'+m['pack_sha256']+'_'):
     original=known[q['id'].split('_',1)[1]];assert [q['title'],q['url'],q['date'],q['rights'],q['text']]==original[1:]
    else:
     assert q['id'].startswith('p10bb8878270ac7b7aa65036a5fd71007c34b3721bc269ce77544d542f0f27656_'),'Unknown active edition'
     original=legacy_known[q['id'].split('_',1)[1]];assert [q['title'],q['url'],q['date'],q['rights'],q['text']]==original[1:]
  for screen in r['screens']:assert (out/(screen+'.png')).read_bytes().startswith(b'\x89PNG') and 'TextView' in (out/(screen+'.txt')).read_text()
 install=json.loads((out/'install.json').read_text());restart=json.loads((out/'restart.json').read_text());assert install['outputs'][0]['rendered']==restart['outputs'][0]['rendered']
 required={'actual provider Activity import completed','portable collection export exact archive','export roundtrip no duplicate collection','cancelled import retains catalog'}|{'real import rollback '+x for x in ['corrupt','rights','offset','identity','license','source-text','fractional-offset','missing-binding','trailing-text']}
 assert required.issubset(install['checks'])
 for suffix in ['before','staged','after']:
  assert int((out/('logical-'+suffix+'.txt')).read_text().split()[0])>0
  assert int((out/('allocated-'+suffix+'.txt')).read_text().split()[0])>0
 for name in ['provider-logical-staged.txt','provider-allocated-staged.txt']:assert int((out/name).read_text().split()[0])>0
 return m

def main():
 from sources import check
 source_result=check()
 from host_audit import check as check_host
 host_result=check_host()
 handoff=ROOT/'docs/evidence/reference-coverage-expansion/HANDOFF.json';h=json.loads(handoff.read_text())
 assert h['status']=='ready_for_supervised_review','New candidate incomplete: '+', '.join(h.get('remaining_gates',[]))
 out=pathlib.Path(h['device_run']);assert sha((out/'manifest.json').read_bytes())==h['device_manifest_sha256'];m=verify_run(out)
 assert m['pack_sha256']==source_result['pack_sha256'] and m['apks']['app']['sha256']==h['apk_sha256']
 assessment=json.loads((ROOT/h['device_source_assessment']).read_text());assert assessment['run_id']==m['run_id']
 outputs=json.loads((out/'install.json').read_text())['outputs']
 for row in outputs:
  a=assessment['cases'][row['id']];assert a['rendered_sha256']==sha(row['rendered'].encode()) and a['unsupported_attributed_claims']==0
  assert isinstance(a['relevant'],bool) and isinstance(a['complete'],bool) and isinstance(a['useful_source_brief'],bool) and a['rationale']
 assert len(assessment['cases'])==len(outputs), 'Incomplete source-level review'
 if '--general-research' in sys.argv:
  assert sum(a['useful_source_brief'] and a['complete'] and a['relevant'] for a in assessment['cases'].values())>=12,'Current Android general-research usefulness gate remains unmet'
  # Original source-packet reconstruction stays independently enforced without
  # changing the historical candidate's app/test/source identities.
  import subprocess
  subprocess.run([sys.executable,str(ROOT/'docs/evidence/general-research/source-packet/verify.py')],cwd=ROOT,check=True)
 seal=json.loads((out/'invocation-seal.json').read_text());assert seal['status']=='PASS'
 for name,digest in seal['files'].items():assert sha((out/name).read_bytes())==digest
 rejected=[]
 for mutation in ['missing-phase','corrupt-stream','stale-run','boot-change','font-change']:
  with tempfile.TemporaryDirectory(prefix='reference480-negative-') as td:
   target=pathlib.Path(td)
   for path in out.iterdir():
    if path.is_file() and path.suffix!='.plpack':shutil.copyfile(path,target/path.name)
   if mutation=='missing-phase':(target/'restart.json').unlink()
   elif mutation=='corrupt-stream':(target/'runtime-install.txt').write_text('changed')
   elif mutation=='stale-run':r=json.loads((target/'install.json').read_text());r['run_id']='stale';(target/'install.json').write_text(json.dumps(r))
   elif mutation=='boot-change':(target/'boot-after.txt').write_text('different')
   else:(target/'font-after.txt').write_text('2.0')
   # Rehash the local file manifest too: reject cross-artifact contradictions,
   # not just an outdated outer hash.
   altered=json.loads((target/'manifest.json').read_text())
   for name in altered['files']:
    if (target/name).is_file():altered['files'][name]=sha((target/name).read_bytes())
   (target/'manifest.json').write_text(json.dumps(altered))
   try:verify_run(target)
   except (AssertionError,ValueError,KeyError,FileNotFoundError,StopIteration):rejected.append(mutation)
   else:raise AssertionError('Bad evidence accepted: '+mutation)
 print(json.dumps({'status':'PASS','scope':'New source-brief edition integrity and leased emulator development behavior; no unseen or generated-quality acceptance','source':source_result,'host':host_result,'device_run':m['run_id'],'negative_controls':rejected}))
if __name__=='__main__':main()
