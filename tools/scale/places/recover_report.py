"""Recover a receipt if interrupted after immutable SQLite promotion; never rebuild it."""
import hashlib,json,pathlib,sqlite3,sys
from common import atomic_json
def recover(path):
 path=pathlib.Path(path);out=path.with_suffix('.report.json')
 if out.exists():return json.loads(out.read_text())
 db=sqlite3.connect('file:'+str(path.resolve())+'?mode=ro',uri=True);assert db.execute('PRAGMA quick_check').fetchone()[0]=='ok'
 meta={k:json.loads(v) for k,v in db.execute('SELECT key,value FROM progress')};assert meta.get('schema_version')==1
 report={**meta,'raw_rows':meta.pop('ordinal'),'unique_ids':db.execute('SELECT count(*) FROM place').fetchone()[0],'exact_entities':db.execute('SELECT count(DISTINCT entity_key) FROM place').fetchone()[0],'rejected':db.execute('SELECT count(*) FROM rejected').fetchone()[0],'id_conflicts':db.execute('SELECT count(*) FROM conflict').fetchone()[0],'fill':dict(db.execute("SELECT 'category',count(category) FROM place UNION ALL SELECT 'city',count(city) FROM place UNION ALL SELECT 'country',count(country) FROM place UNION ALL SELECT 'snapshot_status',count(status) FROM place")),'countries':dict(db.execute("SELECT coalesce(country,'unknown'),count(*) FROM place GROUP BY country")),'recovered_after_promotion':True,'seconds_current_attempt':None,'max_rss_KiB':None,'max_arrow_batch_bytes':None,'bytes':path.stat().st_size,'sha256':hashlib.file_digest(path.open('rb'),'sha256').hexdigest()};db.close();atomic_json(out,report);return report
if __name__=='__main__':print(json.dumps(recover(sys.argv[1]),indent=2))
