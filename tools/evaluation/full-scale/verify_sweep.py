#!/usr/bin/env python3
"""Verify immutable rolling compatibility evidence; never clears full residency."""
import hashlib,json,pathlib,sys,tempfile,shutil
ROOT=pathlib.Path(__file__).resolve().parents[3];E=ROOT/'docs/evidence/full-scale/sweep'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def check_file(p,s):
 if not p.is_file() or p.stat().st_size!=s['bytes'] or sha(p)!=s['sha256']:raise ValueError('Missing/changed sweep artifact '+str(p))
def behavior(directory):
 plan=json.loads((E/'plan.json').read_text());summary=json.loads((directory/'summary.json').read_text())
 assert len(plan['frozen_rows'])==31 and len(summary['outcomes'])==31
 assert summary['all_pass'] and summary['retained_hashes_unchanged']
 assert (directory/'retained-before.txt').read_bytes()==(directory/'retained-after.txt').read_bytes()
 for kind in ['wiki','places']:
  rows=[x for x in plan['frozen_rows'] if x['kind']==kind]
  for i,row in enumerate(rows):
   label=kind+'-'+str(i).zfill(2);r=json.loads((directory/label/'result.json').read_text());m=json.loads((directory/label/'manifest.json').read_text());retire=json.loads((directory/(label+'-retire')/'result.json').read_text())
   assert r['status']=='PASS' and r['shards']==[row['shard']] and not r['metadata_only']
   assert m['generation_allowed'] is False and m['probe']==row['probe']
   assert r['manifest']==sha(directory/label/'manifest.json')
   key='documents' if kind=='wiki' else 'source_records'
   assert r[key]==row['counts'][key]
   assert retire['status']=='PASS' and retire['metadata_only'] and retire['shards']==[]
   assert r['owned_after']<=m['installed_bytes']+2*1024*1024
   assert r['observed_precommit']<=m['installed_bytes']+2*1024*1024
   if kind=='wiki':assert r['source_sha256'].lower()==row['probe']['source_sha256'].lower() and r['source_preview']
   else:assert r['nearby_count']>0 and 'unknown' in r['source'] and 'Routing unavailable' in r['source']
 return True
def main():
 seal=json.loads((E/'receipt.json').read_text())
 for p,s in seal['artifacts'].items():check_file(ROOT/p,s)
 behavior(E/'run')
 # Mutate actual copies of a source probe receipt, not boolean success inputs.
 relative='docs/evidence/full-scale/sweep/run/wiki-00/result.json';spec=seal['artifacts'][relative]
 with tempfile.TemporaryDirectory(prefix='pocketlore-sweep-integrity-') as t:
  copied=pathlib.Path(t)/'result.json';shutil.copyfile(ROOT/relative,copied);check_file(copied,spec)
  with copied.open('r+b') as f:v=f.read(1);f.seek(0);f.write(bytes([v[0]^1]))
  for changed in [True,False]:
   if not changed:copied.unlink()
   try:check_file(copied,spec)
   except ValueError:pass
   else:raise AssertionError('Changed/missing receipt accepted')
 print('PASS: 31 complete-shard Android rolling compatibility probes, shared metadata retirement, retained assets and real artifact mutation checks; simultaneous full installation/update remains UNMEASURED.')
if __name__=='__main__':main()
