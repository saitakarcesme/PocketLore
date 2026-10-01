"""Stream derived identity keys into Arrow and audit exact global counts in DuckDB."""
import hashlib,json,pathlib,sqlite3,sys,time
import duckdb,pyarrow as pa,pyarrow.parquet as pq
from common import atomic_json
pa.set_cpu_count(1);pa.set_io_thread_count(1)
def audit(paths,out):
 start=time.time();keys=[]
 for path in paths:
  path=pathlib.Path(path);keypath=path.with_suffix('.keys.parquet');keys.append(str(keypath))
  if keypath.exists():continue
  db=sqlite3.connect(path);cursor=db.execute('SELECT id,entity_key,category,city,country,status FROM place');stage=keypath.with_suffix('.building.parquet')
  schema=pa.schema([('id',pa.binary(16)),('entity_key',pa.binary(16)),('category',pa.string()),('city',pa.string()),('country',pa.string()),('status',pa.string())])
  with pq.ParquetWriter(stage,schema,compression='zstd') as writer:
   while rows:=cursor.fetchmany(8192):writer.write_table(pa.Table.from_pylist([dict(zip(schema.names,r)) for r in rows],schema=schema))
  db.close();stage.rename(keypath)
 db=duckdb.connect(config={'threads':1,'memory_limit':'1GB','temp_directory':'/home/isa/PocketLore-control/scale-workers/places/duckdb-audit-temp'})
 rel=db.read_parquet(keys);rel.create_view('records')
 row=db.execute('SELECT count(*),count(DISTINCT id),count(DISTINCT entity_key),count(category),count(city),count(country),count(status) FROM records').fetchone()
 report=dict(zip(['records','global_unique_ids','global_exact_entities','category_filled','city_filled','country_filled','snapshot_status_filled'],row))
 report.update(shards=len(paths),bytes=sum(pathlib.Path(p).stat().st_size for p in paths),budget_bytes=4000000000,within_budget=sum(pathlib.Path(p).stat().st_size for p in paths)<=4000000000,androidlm_claimed_unique_places=21100000,androidlm_basis='user-provided 21.1M count; no comparable asset, release, coverage or field-fill measurement available',count_ratio_to_unverified_claim=row[2]/21100000,competitive_acceptance=False,global_coverage_complete=len(paths)==16,seconds=time.time()-start,duckdb_version=duckdb.__version__,arrow_version=pa.__version__,resources={'duckdb_threads':1,'arrow_threads':1,'duckdb_memory_limit':'1GB','batch_rows':8192},countries=dict(db.execute("SELECT coalesce(country,'unknown'),count(*) FROM records GROUP BY country").fetchall()),duplicate_id_examples=[r[0].hex() for r in db.execute('SELECT id FROM records GROUP BY id HAVING count(*)>1 LIMIT 20').fetchall()])
 atomic_json(out,report);print(json.dumps(report,indent=2));db.close()
if __name__=='__main__':audit(sys.argv[2:],sys.argv[1])
