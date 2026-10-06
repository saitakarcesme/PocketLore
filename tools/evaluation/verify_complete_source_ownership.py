#!/usr/bin/env python3
"""Bind repaired source to real subprocess, boundary and original-corpus evidence."""
import copy,hashlib,json,sqlite3
from pathlib import Path
from audit_complete_source_safety import ROOT,inspect
BASE=ROOT/'docs/evidence/complete-source-ownership'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def validate_current_bindings(report=None):
 r=report or json.loads((ROOT/'docs/evidence/complete-source-ownership-review.json').read_text())
 assert not r['source_admission_established'] and not r['long_job_launched']
 for name,d in r['code'].items():assert sha(ROOT/name)==d,name
 for name,d in r['files'].items():
  p=BASE/name;assert p.is_file() and sha(p)==d['sha256'] and p.stat().st_size==d['bytes'],name
 probes=json.loads((BASE/'probes/receipt.json').read_text());assert probes['success']
 obs=probes['observations'];bound=[x for x in obs if 'boundary_sizes' in x];assert len(bound)==7
 assert [x['actual_compressed_bytes'] for x in bound]==[8388608,8388608,8388607,8388609,16777216,1,8388608]
 assert all(x['checkpoint'][0]==0 for x in bound)
 phases=[x for x in obs if 'concurrent_output_bit_identical' in x];assert len(phases)==6
 assert {'ingest','wait_source','index','hash'}==set(x['phase'] for x in phases)
 assert all(x['concurrent_output_bit_identical'] and x['owner_alive_after_refusal'] for x in phases)
 assert sorted(next(x['two_fresh_exit_codes'] for x in obs if 'two_fresh_exit_codes' in x))==[0,1]
 snapshots=list((BASE/'probes').glob('*/lease-snapshots.json'));assert len(snapshots)==6
 for path in snapshots:
  snap=json.loads(path.read_text());assert snap['before']==snap['after'] and snap['owner_alive'] and snap['before']
 inv=json.loads((BASE/'actual/invocations.json').read_text());assert [x['exit'] for x in inv]==[1,0,1]
 done=inv[1]['status'];assert done['code']['production.py']==r['code']['tools/packs/complete-source/production.py']
 assert done['counts']['articles']==5944 and done['counts']['dispositions']==6000 and done['all_record_bindings_rechecked']==6000
 assert done['status']=='PROVISIONAL_COMPLETE' and not done['source_admission_established'] and not done['whole_original_identity_matched']
 path=Path(r['index']['path']);assert sha(path)==done['index_sha256']==r['index']['sha256']
 db=sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True)
 try:rows=db.execute('SELECT page,revision,sequence,title,license,raw_sha256,capsule_sha256 FROM articles ORDER BY page').fetchall()
 finally:db.close()
 oracle=json.loads((BASE/'oracle.json').read_text());assert hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()==oracle['ordered_identity_sha256']
 samples=json.loads((BASE/'original-roundtrips.json').read_text());assert [inspect(x) for x in samples['samples']]==samples['observations']
 spec=json.loads((BASE/'launch-spec.json').read_text());assert not spec['launched'] and spec['requires_fresh_preflight'] and spec['cutoff_epoch']==1791269964
 assert spec['workers']==1 and spec['cgroup_properties']['MemoryMax']==536870912 and spec['cgroup_properties']['MemorySwapMax']==0 and spec['cgroup_properties']['Restart']=='no'
 assert (BASE/'bus.exit').read_text().strip()=='1'
 return True
if __name__=='__main__':
 r=json.loads((ROOT/'docs/evidence/complete-source-ownership-review.json').read_text());validate_current_bindings(r);negative=[]
 for name,mutate in [('missing-record',lambda x:x['files'].update({'absent.json':{'bytes':0,'sha256':'0'*64}})),('changed-hash',lambda x:x['files'][next(iter(x['files']))].update(sha256='0'*64)),('stale-source',lambda x:x['code'].update({'tools/packs/complete-source/production.py':'0'*64})),('false-admission',lambda x:x.update(source_admission_established=True))]:
  bad=copy.deepcopy(r);mutate(bad)
  try:validate_current_bindings(bad)
  except (AssertionError,OSError):negative.append(name)
  else:raise AssertionError('accepted negative '+name)
 print(json.dumps({'result':'PASS','negative_controls':negative,'source_admission_established':False,'long_job_launched':False}))
