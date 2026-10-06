#!/usr/bin/env python3
"""Offline cross-artifact check. Engineering pass never authorizes admission/launch."""
import copy,hashlib,json,sqlite3,sys
from pathlib import Path
from audit_complete_source_safety import inspect,ROOT
PACKET=ROOT/'docs/evidence/complete-source-production-safety'
def sha(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def validate(report):
 assert report['classification']=='ENGINEERING_PASS_EXTERNAL_LAUNCH_BLOCKED'
 assert report['source_admission_established'] is False and report['long_job_launched'] is False
 for name,d in report['files'].items():
  p=PACKET/name;assert p.is_file() and p.stat().st_size==d['bytes'] and sha(p)==d['sha256'],name
 for name,d in report['executed_sources'].items():assert sha(ROOT/name)==d,name
 inv=json.loads((PACKET/'actual-lock/invocations.json').read_text());assert len(inv)==3
 for r in inv:
  s=r['status'];assert s['source_admission_established'] is False and s['distribution_ready'] is False
  assert s['code']['production.py']==report['executed_sources']['tools/packs/complete-source/production.py']
  assert r['end']>=r['start'] and s['workers']==1 and s['process_limits']['address_space_limit_bytes']<=384*1024**2
 assert [r['exit'] for r in inv]==[1,0,1]
 for r,sig in [(inv[0],'SIGTERM'),(inv[2],'SIGXCPU')]:
  assert r['signal']==sig and r['signal_delivered'] and sig in r['status']['error']
  assert r['status']['committed_through']>=63 and r['status']['resume_ingest_allowed']
 lock=json.loads((PACKET/'actual-lock/concurrent-resume.json').read_text());assert lock['exit']==1 and lock['owner_still_running'] and 'already active' in lock['error']
 done=inv[1]['status'];assert done['previous_run']==inv[0]['status']['run_id']
 assert done['status']=='PROVISIONAL_COMPLETE' and done['committed_through']==5999
 assert done['all_record_bindings_rechecked']==6000 and done['counts']['articles']==5944
 assert not done['whole_original_identity_matched'] and not done['full_source_admission_established']
 assert done['storage']['free_host_bytes']>=100*1024**3 and done['memory']['ru_maxrss_bytes']<512*1024**2
 index=Path(report['immutable_index']['path']);assert sha(index)==done['index_sha256']==report['immutable_index']['sha256']
 db=sqlite3.connect('file:'+str(index)+'?mode=ro',uri=True)
 try:
  assert not db.execute("SELECT 1 FROM sqlite_master WHERE name='candidates'").fetchone()
  assert db.execute('SELECT count(*) FROM original_bindings').fetchone()[0]==6000
  rows=db.execute('SELECT page,revision,sequence,title,license,raw_sha256,capsule_sha256 FROM articles ORDER BY page').fetchall()
  oracle=json.loads((PACKET/'oracle.json').read_text())
  assert hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()==oracle['ordered_identity_sha256']
 finally:db.close()
 samples=json.loads((PACKET/'original-roundtrips.json').read_text());assert [inspect(s) for s in samples['samples']]==samples['observations']
 assert len(samples['samples'])==35 and max(s['sequence'] for s in samples['observations'][:32])>5000
 assert set(s['license'] for s in samples['observations'])=={'CC-BY-SA-3.0','CC-BY-SA-4.0'}
 storage=json.loads((PACKET/'storage-measurements.json').read_text());samples=json.loads((PACKET/'actual-lock/manual-resume-storage-samples.json').read_text())
 assert len(samples)==storage['sample_count'] and storage['max_journal_logical_bytes']>0
 assert max(sum(v['allocated'] for v in x['files'].values()) for x in samples)==storage['max_sampled_allocated_bytes']
 assert storage['final_index_bytes']==index.stat().st_size
 assert storage['peak_process_rss_bytes']==done['memory']['ru_maxrss_bytes']
 assert report['launch']['blocked_reason']=='User DBus unavailable; no enforced child cgroup launch'
 assert (PACKET/'user-bus-preflight.exit').read_text().strip()=='1'
 assert 'No data available' in (PACKET/'user-bus-preflight.log').read_text()
 spec=json.loads((PACKET/'launch-spec.json').read_text());assert spec['automatic_restart'] is False and spec['workers']==1
 assert spec['cutoff_epoch']==1791269964 and spec['requires_fresh_preflight'] and not spec['launched']
 return True
if __name__=='__main__':
 report=json.loads((ROOT/'docs/evidence/complete-source-production-safety-review.json').read_text());validate(report)
 rejected=[]
 for label,mutate in [('changed-hash',lambda x:x['files'][next(iter(x['files']))].update(sha256='0'*64)),('missing-artifact',lambda x:x['files'].update({'missing-required-phase.json':{'bytes':0,'sha256':'0'*64}})),('false-admission',lambda x:x.update(source_admission_established=True)),('stale-code',lambda x:x['executed_sources'].update({'tools/packs/complete-source/production.py':'0'*64})),('wrong-index',lambda x:x['immutable_index'].update(sha256='0'*64))]:
  changed=copy.deepcopy(report);mutate(changed)
  try:validate(changed)
  except (AssertionError,OSError,ValueError):rejected.append(label)
  else:raise AssertionError('negative control accepted '+label)
 samples=json.loads((PACKET/'original-roundtrips.json').read_text());bad=copy.deepcopy(samples['samples'][0]);bad['identity']['raw_sha256']='0'*64
 try:inspect(bad)
 except AssertionError:rejected.append('corrupt-original-binding')
 else:raise AssertionError('corrupt original accepted')
 print(json.dumps({'result':'PASS','classification':report['classification'],'negative_controls':rejected,'source_admission_established':False,'long_job_launched':False}))
