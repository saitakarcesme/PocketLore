#!/usr/bin/env python3
"""Offline raw receipt validation; never opens the Wikipedia archive."""
import base64,copy,hashlib,importlib.util,json,os,pathlib,re,sys,zlib
ROOT=pathlib.Path(__file__).resolve().parents[3]
def load():
 s=importlib.util.spec_from_file_location('xml_adapter',ROOT/'tools/packs/current-xml/adapter.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
A=load()
INPUTS=['tools/packs/current-xml/adapter.py','tools/packs/current-xml/FORMAT.md','tools/evaluation/current-xml/fixtures.py','tools/evaluation/current-xml/run.py','tools/evaluation/current-xml/check.py','tools/evaluation/check_current_xml_source.sh','docs/evidence/current-xml-inputs/policy.json']
def need(ok,guard):
 if not ok:raise ValueError(guard)
def freeze():return {p:A.filehash(ROOT/p) for p in INPUTS}
def rawcheck(r,source=None):
 need(r['format']==A.FORMAT and r['source_format']=='mediawiki-xml-wikitext','source-format')
 need(r['admission'] is False and r['rights']=='unknown-unreviewed','license-promotion')
 need(r['status'] in ['COMPLETE_ENGINEERING_INPUT','PROVISIONAL_PREFIX'] and not r['errors'],'outcome')
 need(re.fullmatch('[0-9a-f]{64}',r['source_id']) is not None and (source is None or r['source_id']==source),'archive-input')
 need(r['source_before']==r['fd_before']==r['source_after']==r['fd_after'],'archive-version')
 need(0<r['records']<=r['ledger'] and 0<r['pages']<=256,'record-count')
 need(0<r['compressed_read_bytes']<=16777216 and 0<r['decoded_bytes']<=67108864 and 0<=r['last_complete_xml_end']<=r['xml_parsed_bytes']<=r['decoded_bytes'],'byte-offset')
 need(0<=r['discarded_incomplete_pages']<=1 and r['end_ns']-r['start_ns']<=90*10**9,'time-bound')
 samples=r['samples'];phases=[s['phase'] for s in samples]
 need(phases[0:2]==['preflight','opened'] and phases[-3:]==['parsed','committed','closed'],'phase')
 first=samples[0];lasttime=-1;initial=None;prev=None
 for s in samples:
  pid=int(s['stat'].split(' (',1)[0]);st=s['stat'].rsplit(')',1)[1].split();status=dict(line.split(':',1) for line in s['status'].splitlines() if ':' in line)
  need(pid==s['pid']==first['pid']==int(status['Pid']),'pid')
  need(st[19]==first['stat'].rsplit(')',1)[1].split()[19],'startticks')
  need(s['namespaces']==first['namespaces'] and s['cgroup']==first['cgroup'] and s['group_identity']==first['group_identity'],'namespace-cgroup')
  need(lasttime<s['monotonic_ns'] and s['cpu_seconds']>=0,'chronology');lasttime=s['monotonic_ns']
  k=s['kernel'];need(0<int(k['memory.current'])<9*1024**3 and int(k['memory.swap.current'])==0,'resource')
  events={a:int(b) for a,b in (line.split() for line in k['memory.events'].splitlines())};need({'low','high','max','oom','oom_kill'}<=events.keys() and all(v>=0 for v in events.values()),'kernel-events')
  if initial is None:initial=events
  if prev:need(all(events[n]>=prev[n] for n in prev),'kernel-events')
  need(all(events[n]==initial[n] for n in ['max','oom','oom_kill']),'kernel-events');prev=events
  need(re.search(r'^Rss:\s+\d+ kB$',s['smaps_rollup'],re.M) is not None,'smaps')
  if s['phase'] not in ['preflight','closed']:
   need(s['fd_stat']==r['source_before'] and int(dict(x.split(':',1) for x in s['fdinfo'].splitlines())['flags'].strip(),8)&3==0,'fd-readonly')
   mid=dict(x.split(':',1) for x in s['fdinfo'].splitlines())['mnt_id'].strip();need(any(line.split()[0]==mid for line in s['mountinfo'].splitlines()),'mount')
 return True

def envelope(path):
 p=pathlib.Path(path);b=p.read_bytes();return {'sha256':A.sha(b),'bytes':len(b),'zlib_base64':base64.b64encode(zlib.compress(b)).decode()}
def verify_envelope(e):
 b=zlib.decompress(base64.b64decode(e['zlib_base64']));need(len(b)==e['bytes'] and A.sha(b)==e['sha256'],'envelope');return b

CONTROL_NAMES={'positive','exact-original','UTF16','query-source','export-bytes','reopen','split','missing-and-model','nested-id','duplicate-contributor','duplicate-redirect','conflict','doctype','malformed','truncated','trailing-truncated-member','namespace','oversized','deep','missing-id','bomb','page-bound','cancel','mid-cancel','deadline','partial','source-collision-rollback','database-schema','database-rights','database-count','database-format','surrogate-boundary'}
MUTATION_NAMES={'wrong-input','wrong-version','wrong-pid','wrong-offset','wrong-format','promotion','wrong-count','wrong-phase','wrong-startticks'}
FLOW_NAMES={'flow-export','flow-inspection','flow-hit','receipt-substitution'}
def coverage(s):
 for key,expected in [('controls',CONTROL_NAMES),('mutations',MUTATION_NAMES),('flow_controls',FLOW_NAMES)]:
  names=[x['name'] for x in s[key]];need(len(names)==len(set(names)) and set(names)==expected,'coverage-'+key)
 required_raw={'positive','split','missing-and-model','nested-id','duplicate-contributor','duplicate-redirect','conflict','doctype','malformed','truncated','trailing-truncated-member','namespace','oversized','deep','missing-id','bomb','page-bound','cancel','mid-cancel','deadline','partial'}
 need(set(s['raw_receipts'])==required_raw,'coverage-raw')
 return True

def validate_synthetic(s,raw):
 need(s['sources_before']==s['sources_after']==freeze(),'synthetic-source')
 need(s['status']=='PASS','synthetic');coverage(s)
 baseline=s['raw_receipts']['positive'];source=s['oracle']['files']['valid']['sha256'];rawcheck(baseline,source)
 for c in s['controls']:
  if c['name'] not in s['raw_receipts']:continue
  r=s['raw_receipts'][c['name']]
  if c.get('expected')=='success':rawcheck(r,r['source_id'])
  else:need(r['status']=='FAILED' and any(c['expected'] in x for x in r['errors']),'negative-outcome')
 for m in s['mutations']:
  rawcheck(baseline,source)
  key=str(pathlib.Path(s['directory']).relative_to('downloads/current-xml-541')/(m['name']+'.mutation.json'))
  changed=json.loads(verify_envelope(raw[key]));need(A.sha(A.canonical(changed))==m['mutated_sha256'] and A.sha(A.canonical(baseline))==m['base_sha256'],'mutation-hash')
  try:rawcheck(changed,source)
  except ValueError as e:need(str(e)==m['expected_guard']==m['actual_guard'],'mutation-guard')
  else:raise ValueError('mutation-accepted')
 for name,identity in s['oracle']['files'].items():
  path=ROOT/s['directory']/'inputs'/(name+'.bz2');need(path.stat().st_size==identity['bytes'] and A.filehash(path)==identity['sha256'],'fixture-input')
 validate_flow(baseline,s['flow'],ROOT/s['directory']/'positive')
 for c in s['flow_controls']:
  validate_flow(baseline,s['flow'],ROOT/s['directory']/'positive')
  try:validate_flow(c.get('mutated_receipt',baseline),c.get('mutated',s['flow']),ROOT/s['directory']/'positive')
  except ValueError as e:need(str(e)==c['expected_guard']==c['actual_guard'],'flow-mutation-guard')
  else:raise ValueError('flow-mutation-accepted')
 need({c['name'] for c in s['coverage_controls']}=={'omitted-control','duplicate-control','omitted-mutations','omitted-flow'},'coverage-controls')
 for c in s['coverage_controls']:
  coverage(s);m=copy.deepcopy(s)
  if c['name']=='omitted-control':m['controls']=m['controls'][1:]
  elif c['name']=='duplicate-control':m['controls'].append(m['controls'][0])
  elif c['name']=='omitted-mutations':m['mutations']=[]
  else:m['flow_controls']=[]
  try:coverage(m)
  except ValueError as e:need(str(e)==c['guard'],'coverage-mutation-guard')
  else:raise ValueError('coverage-mutation-accepted')
 return True

def validate_flow(r,flow,path,raw=None):
 need(json.loads((path/'receipt.json').read_text())==r,'capsule-receipt')
 reader=A.Reader(path,r['source_id'])
 try:
  need(flow is not None and flow['hits'],'flow')
  inspected=reader.inspect(flow['inspection']['id']);need({k:v for k,v in inspected.items() if k!='text'}==flow['inspection'],'inspection-binding')
  need(reader.search(flow['query'])==flow['hits'],'search-binding')
  for hit in flow['hits']:reader.resolve(hit)
  export=path.parent/'prefix-export'/'original.wikitext';actual=export.read_bytes();need(len(actual)<=A.LIMITS['text'] and actual==inspected['text'].encode() and A.sha(actual)==flow['export']['sha256']==inspected['text_sha256'],'export-binding')
  need(json.loads((export.parent/'metadata.json').read_text())==flow['inspection'],'export-metadata')
  if raw is not None:need(verify_envelope(raw['prefix-export/original.wikitext'])==actual,'export-envelope')
 finally:reader.close()
 return True

def validate_packet(p,current=True):
 need(set(p['sources_before'])==set(INPUTS) and p['sources_before']==p['sources_after'],'source-set')
 if current:need(p['sources_before']==freeze(),'current-source')
 need(set(p['source_content'])==set(INPUTS),'source-content')
 for name,e in p['source_content'].items():need(A.sha(verify_envelope(e))==p['sources_before'][name],'source-content')
 for name,e in p['raw'].items():verify_envelope(e)
 s=json.loads(verify_envelope(p['raw']['synthetic.json']));validate_synthetic(s,p['raw'])
 r=json.loads(verify_envelope(p['raw']['prefix/receipt.json']));rawcheck(r,'3fd026adce2a54ec7a2583c9047bcd8e632e67bad62b0b46ea4b685657d18f31')
 need(r['source_before']['size']==26899580121 and r['source_before']['inode']==4272766 and r['source_before']['device']==57 and r['status']=='PROVISIONAL_PREFIX','actual-archive')
 attempt=json.loads(verify_envelope(p['raw']['prefix-attempt.json']));need(attempt['sources']==p['sources_before'] and attempt['archive_stat']==r['source_before'],'attempt-binding')
 need(json.loads(verify_envelope(p['raw']['prefix-sources-after.json']))==p['sources_after'],'post-source')
 after=json.loads(verify_envelope(p['raw']['prefix-runtime-after.json']));need(after['executable']==attempt['executable'] and after['source_versions']==attempt['source_versions'],'runtime-stability')
 need(attempt['executable']['sha256']==A.filehash(sys.executable),'runtime-executable')
 need(p['build']['exit']==0 and p['build']['apk_sha256']==A.filehash(ROOT/p['build']['apk']),'build')
 validate_flow(r,p['prefix_flow'],ROOT/p['prefix_path'],p['raw'])
 return True

def main():
 pth=ROOT/'docs/evidence/current-xml-source-review.json';p=json.loads(pth.read_text());error=None
 try:validate_packet(p)
 except Exception as e:error=type(e).__name__+': '+str(e)
 print(json.dumps({'status':'PASS_HOST_PROVISIONAL_ONLY' if error is None else 'FAIL','error':error,'review_sha256':A.filehash(pth)}));return int(error is not None)
if __name__=='__main__':sys.exit(main())
