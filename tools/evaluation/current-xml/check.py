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

def validate_packet(p,current=True):
 need(set(p['sources_before'])==set(INPUTS) and p['sources_before']==p['sources_after'],'source-set')
 if current:need(p['sources_before']==freeze(),'current-source')
 for name,e in p['raw'].items():verify_envelope(e)
 s=json.loads(verify_envelope(p['raw']['synthetic.json']));need(s['status']=='PASS' and len(s['controls'])>=20,'synthetic')
 r=json.loads(verify_envelope(p['raw']['prefix/receipt.json']));rawcheck(r,'3fd026adce2a54ec7a2583c9047bcd8e632e67bad62b0b46ea4b685657d18f31')
 need(r['source_before']['size']==26899580121 and r['source_before']['inode']==4272766 and r['source_before']['device']==57 and r['status']=='PROVISIONAL_PREFIX','actual-archive')
 need(p['build']['exit']==0 and p['build']['apk_sha256']==A.filehash(ROOT/p['build']['apk']),'build')
 reader=A.Reader(ROOT/p['prefix_path'],r['source_id'])
 try:
  for hit in p['prefix_flow']['hits']:reader.resolve(hit)
  need(p['prefix_flow']['hits'] and p['prefix_flow']['export']['sha256']==p['prefix_flow']['inspection']['text_sha256'],'flow')
 finally:reader.close()
 return True

def main():
 pth=ROOT/'docs/evidence/current-xml-source-review.json';p=json.loads(pth.read_text());error=None
 try:validate_packet(p)
 except Exception as e:error=type(e).__name__+': '+str(e)
 print(json.dumps({'status':'PASS_HOST_PROVISIONAL_ONLY' if error is None else 'FAIL','error':error,'review_sha256':A.filehash(pth)}));return int(error is not None)
if __name__=='__main__':sys.exit(main())
