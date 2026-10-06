#!/usr/bin/env python3
"""Offline current-source validation; never opens the original XML archive."""
import base64,copy,importlib.util,json,pathlib,sys,zlib
ROOT=pathlib.Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('indexed',ROOT/'tools/packs/current-xml/indexed.py');I=importlib.util.module_from_spec(spec);spec.loader.exec_module(I);A=I.A
INPUTS=['tools/packs/current-xml/adapter.py','tools/packs/current-xml/indexed.py','tools/packs/current-xml/FORMAT.md','tools/evaluation/indexed-xml/fixtures.py','tools/evaluation/indexed-xml/run.py','tools/evaluation/indexed-xml/check.py','tools/evaluation/check_indexed_xml_search.sh','docs/evidence/indexed-xml-inputs/policy.json']
def need(ok,guard):
 if not ok:raise ValueError(guard)
def freeze():return {p:A.filehash(ROOT/p) for p in INPUTS}
def envelope(p):
 b=pathlib.Path(p).read_bytes();return {'sha256':A.sha(b),'bytes':len(b),'zlib_base64':base64.b64encode(zlib.compress(b)).decode()}
def unpack(e):
 b=zlib.decompress(base64.b64decode(e['zlib_base64']));need(len(b)==e['bytes'] and A.sha(b)==e['sha256'],'envelope');return b

def validate_query(r):
 need(r['query']==r['frozen_query'],'query-literal');need(r['result']['hits']==r['oracle']==r['legacy'],'exact-results');st=r['result']['stats'];need(st['full_scan'] is False,'full-scan');need(st['decompressions']==st['verified_candidates']==r['observed_inspections'] and st['decompressions']<=st['seed_candidates']<=256,'candidate-count');need(st['lexical_bytes']==r['observed_text_bytes'],'decompression-bytes')
 for h in r['result']['hits']:
  need(h['quote']==r['query'] and h['quote_sha256']==A.sha(r['query'].encode()) and h['admission'] is False,'quote');need(h['end_utf16']-h['start_utf16']==A.units(r['query']),'UTF16')
 if r['query']=='LateNeedleZXQ':need(st['decompressions']<820,'rare-index')
 if r['query']=='AbsentNeedleZZZ':need(st['decompressions']==0,'absent-index')
 need(r['indexed_ns']>=0 and r['legacy_ns']>=0,'timing');return True

def validate_samples(samples):
 need(len(samples)>=2,'samples');first=samples[0];previous=None
 for s in samples:
  pid=int(s['stat'].split(' (')[0]);ticks=s['stat'].rsplit(')',1)[1].split()[19];status=dict(x.split(':',1) for x in s['status'].splitlines() if ':' in x)
  need(pid==s['pid']==first['pid']==int(status['Pid']),'PID');need(ticks==first['stat'].rsplit(')',1)[1].split()[19],'startticks');need(s['namespaces']==first['namespaces'] and s['group_identity']==first['group_identity'],'namespace');need(int(s['kernel']['memory.current'])<9*1024**3 and int(s['kernel']['memory.swap.current'])==0,'resource')
  event={k:int(v) for k,v in (line.split() for line in s['kernel']['memory.events'].splitlines())};base={k:int(v) for k,v in (line.split() for line in first['kernel']['memory.events'].splitlines())};need(all(event[k]==base[k] for k in ['max','oom','oom_kill']) and all(v>=0 for v in event.values()),'kernel-events')
  if previous is not None:need(previous<s['monotonic_ns'],'chronology')
  previous=s['monotonic_ns']
 return True

def validate(p):
 need(p['sources_before']==p['sources_after']==freeze() and set(p['source_content'])==set(INPUTS),'source-binding')
 for n,e in p['source_content'].items():need(A.sha(unpack(e))==p['sources_before'][n],'source-content')
 for e in p['raw'].values():unpack(e)
 s=json.loads(unpack(p['raw']['synthetic.json']));need(s['status']=='PASS' and s['sources']==freeze(),'synthetic-source');need(len(s['trials'])==50,'trials')
 policy=json.loads((ROOT/'docs/evidence/indexed-xml-inputs/policy.json').read_text());need([x['query'] for x in s['trials']]==policy['queries']*10,'trial-order')
 for r in s['trials']:validate_query(r)
 validate_samples(s['samples']);need(s['controls']['short']=='indexed-query-length' and s['controls']['cancel']=='cancelled' and s['controls']['deadline']=='FAILED' and s['controls']['rollback'] is True and s['controls']['pagination'] is True,'controls')
 expected={'schema','tokenizer','source','record-count','index-digest','index-hash'};need({m['name'] for m in s['database_mutations']}==expected,'db-mutations')
 for m in s['database_mutations']:
  good=I.Reader(ROOT/s['functional_index']);good.close()
  try:bad=I.Reader(ROOT/m['path']);bad.close()
  except A.Refused as e:need(str(e)==m['guard'],'database-guard')
  else:raise ValueError('database-mutation-accepted')
 for m in s['receipt_mutations']:
  validate_query(s['trials'][0]);changed=json.loads(unpack(p['raw'][m['file']]))
  try:validate_query(changed)
  except ValueError as e:need(str(e)==m['guard'],'receipt-guard')
  else:raise ValueError('receipt-mutation-accepted')
 d=json.loads(unpack(p['raw']['derived.json']));need(d['status']=='PASS' and d['sources']==freeze(),'derived-source');need(d['input_sha256']=='1c58d27e72af460b549f868a1d2ce72401281400e322c4825aaf44aa20629daf' and d['records']==256 and d['all_original_fields_equal'] is True,'derivation');need(d['before']==d['after'],'input-version');validate_samples(d['samples'])
 reader=I.Reader(ROOT/d['output'])
 try:
  for q in d['queries']:
   need(reader.search(q['query'])==q['result'] and q['result']['hits']==q['legacy'],'derived-query')
   for h in q['result']['hits']:reader.resolve(h)
  need(A.filehash(ROOT/d['export_path'])==d['export_sha256'],'export')
 finally:reader.close()
 need(p['build']['exit']==0 and A.filehash(ROOT/p['build']['apk'])==p['build']['sha256'],'APK')
 return True

def main():
 p=json.loads((ROOT/'docs/evidence/indexed-xml-search-review.json').read_text())
 try:validate(p);print('PASS_HOST_INDEXED_ENGINEERING_ONLY');return 0
 except Exception as e:print(type(e).__name__+': '+str(e));return 1
if __name__=='__main__':sys.exit(main())
