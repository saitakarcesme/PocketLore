"""Exact full-release ID-set audit using bounded deterministic disk partitions."""
import json,pathlib,time,duckdb,resource
from common import atomic_json
ROOT=pathlib.Path('/home/isa/PocketLore-control/scale-workers/places');D=ROOT/'data';E=pathlib.Path('docs/evidence/scale/places');start=time.time();partitions=ROOT/'audit-identity-partitions-v2'
objects=json.loads((E/'overture-objects.json').read_text());raw=[str(D/pathlib.Path(o['Key']).name) for o in objects];keys=[str(D/f'compact-{i:02}.keys.parquet') for i in range(16)];reports=[json.loads((D/f'compact-{i:02}.report.json').read_text()) for i in range(16)]
db=duckdb.connect(config={'threads':1,'memory_limit':'1GB','preserve_insertion_order':False,'temp_directory':str(ROOT/'compact-audit-temp'),'partitioned_write_max_open_files':128,'partitioned_write_flush_threshold':8192});db.read_parquet(raw).create_view('raw');db.read_parquet(keys).create_view('records')
counts=db.execute("SELECT count(*),count(nullif(category,'')),count(nullif(city,'')),count(nullif(country,'')),count(nullif(status,'')) FROM records").fetchone()
if not (partitions/'complete.json').exists():
 if partitions.exists():raise RuntimeError('Incomplete partitions preserved; explicitly version a changed retry')
 sql="COPY (SELECT id,kind,hash(id)%128 AS bucket FROM (SELECT unhex(replace(id,'-','')) AS id,0 AS kind FROM raw UNION ALL SELECT id,1 AS kind FROM records UNION ALL SELECT entity_key AS id,2 AS kind FROM records)) TO '"+str(partitions)+"' (FORMAT PARQUET, PARTITION_BY(bucket), COMPRESSION ZSTD, ROW_GROUP_SIZE 8192)"
 db.execute(sql);atomic_json(partitions/'complete.json',{'raw':raw,'keys':keys,'buckets':128});print('disk partitions complete',round(time.time()-start,2),flush=True)
totals=[0]*8
for i in range(128):
 files=[str(p) for p in (partitions/f'bucket={i}').glob('*.parquet')]
 if not files:continue
 row=db.execute('''WITH groups AS (SELECT id,count(*) FILTER(WHERE kind=0) nr,count(*) FILTER(WHERE kind=1) nk,count(*) FILTER(WHERE kind=2) ne FROM read_parquet(?) GROUP BY id)
 SELECT sum(nr),sum(nk),count(*) FILTER(WHERE nr>0),count(*) FILTER(WHERE nk>0),count(*) FILTER(WHERE ne>0),count(*) FILTER(WHERE nr>0 AND nk=0),count(*) FILTER(WHERE nk>0 AND nr=0),sum(ne) FROM groups''',[files]).fetchone()
 totals=[a+b for a,b in zip(totals,row)];print('bucket',i,round(time.time()-start,2),flush=True)
report=dict(zip(['raw_records','eligible_records','raw_unique_ids','global_unique_ids','global_exact_entities','raw_ids_missing_from_compact','compact_ids_not_in_raw','entity_rows'],totals));report.update(dict(zip(['category_filled','city_filled','country_filled','snapshot_status_filled'],counts[1:])))
report.update(extra_rows_over_unique_ids=totals[1]-totals[3],extra_ids_over_exact_entities=totals[3]-totals[4],field_fill_definition='non-null and nonempty string; whitespace and source validity not inferred',rejected=sum(r['rejected'] for r in reports),shards=16,bytes=sum(r['bytes'] for r in reports),budget_bytes=4000000000,within_budget=sum(r['bytes'] for r in reports)<=4000000000,countries=dict(db.execute("SELECT coalesce(country,'unknown'),count(*) FROM records GROUP BY country").fetchall()),country_basis='source address country labels, not coordinate containment',androidlm_claimed_places=21100000,comparison_basis='user-provided unverified count; comparable release, coverage and field-fill evidence unavailable',count_ratio_to_unverified_claim=totals[4]/21100000,competitive_acceptance=False,semantic_unique_real_world_places=None,seconds=time.time()-start,method='128 deterministic hash partitions; exact per-partition ID grouping and raw/compact set equality; no probabilistic counting',memory_limit_bytes=1000000000,max_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
assert report['eligible_records']==counts[0]==report['entity_rows'];assert report['eligible_records']+report['rejected']==report['raw_records'];assert report['compact_ids_not_in_raw']==0
if report['rejected']==0:assert report['raw_ids_missing_from_compact']==0
atomic_json(E/'global-audit.json',report);print(json.dumps(report,indent=2));db.close()
