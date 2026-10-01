"""Measure stored SQLite blob bounds without inflating the complete global corpus."""
import fcntl,json,pathlib,sqlite3
from common import atomic_json
D=pathlib.Path('/home/isa/PocketLore-control/scale-workers/places/data');slot=(D.parent/'second-compute.lock').open('a');fcntl.flock(slot,fcntl.LOCK_EX);reports=[]
for i in range(16):
 p=D/f'compact-{i:02}.sqlite';db=sqlite3.connect('file:'+str(p)+'?mode=ro',uri=True);count,rows,size=db.execute('SELECT count(*),sum(records),max(length(payload)) FROM block').fetchone();expected=json.loads(p.with_suffix('.report.json').read_text());assert rows==expected['eligible_records'] and size<=1048576;assert db.execute('SELECT count(*) FROM block WHERE length(sha256)<>64').fetchone()[0]==0;db.close();reports.append({'path':str(p),'blocks':count,'records':rows,'max_stored_compressed_bytes':size})
atomic_json('docs/evidence/scale/places/block-bound-checks.json',{'shards':reports,'passed':True,'maximum_stored_compressed_bytes':max(r['max_stored_compressed_bytes'] for r in reports),'compressed_reader_bound_bytes':1048576,'inflated_bound':'builder recursively enforces 32 MiB and records actual maxima; query reader verifies bounded inflation and SHA-256','android_runtime_acceptance':False});print('all 16 blob-bound checks passed',max(r['max_stored_compressed_bytes'] for r in reports))
