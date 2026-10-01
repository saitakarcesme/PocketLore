"""Audit original pinned Parquet field fill and provider license entries, not inferred rights."""
import duckdb,json,pathlib,sys,time
from common import atomic_json
start=time.time();out=pathlib.Path(sys.argv[1]);files=sys.argv[2:]
db=duckdb.connect(config={'threads':1,'memory_limit':'1GB','temp_directory':'/home/isa/PocketLore-control/scale-workers/places/source-audit-temp'})
db.read_parquet(files).create_view('raw')
fields=['id','names.primary','confidence','basic_category','taxonomy.primary','operating_status']
fill={field:db.execute('SELECT count('+field+') FROM raw' if field=='confidence' else "SELECT count(nullif("+field+",'')) FROM raw").fetchone()[0] for field in fields}
list_fill={field:db.execute("SELECT count(*) FROM raw WHERE len(list_filter("+field+", x -> x IS NOT NULL AND x<>''))>0").fetchone()[0] for field in ['websites','phones','emails','socials']}
entries=db.execute('SELECT s.dataset,s.license,count(*) FROM raw,unnest(sources) t(s) GROUP BY s.dataset,s.license ORDER BY s.dataset,s.license').fetchall()
report={'source_objects':len(files),'raw_records':db.execute('SELECT count(*) FROM raw').fetchone()[0],'field_fill':fill,'nonempty_list_fields':list_fill,'field_fill_definition':'non-null confidence; non-null and nonempty strings; source validity not inferred','provider_license_entries':[{'dataset':d,'license':l,'source_entries':n} for d,l,n in entries],'records_with_no_sources':db.execute('SELECT count(*) FROM raw WHERE sources IS NULL OR len(sources)=0').fetchone()[0],'records_with_unknown_source_license':db.execute('SELECT count(*) FROM raw WHERE len(list_filter(sources,x -> x.license IS NULL OR x.license=\'\'))>0').fetchone()[0],'max_original_record_json_utf8_bytes':db.execute('SELECT max(octet_length(encode(to_json(raw)))) FROM raw').fetchone()[0],'license_interpretation':'literal upstream values; unknown rights remain unknown; not distribution clearance','seconds':time.time()-start};atomic_json(out,report);print(json.dumps(report,indent=2))
