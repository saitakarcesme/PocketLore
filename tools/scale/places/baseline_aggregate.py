"""Read-only published baseline counts under the spare single-compute slot."""
import fcntl,json,pathlib,sqlite3,time
from common import atomic_json,norm
D=pathlib.Path('/home/isa/PocketLore-control/scale-workers/places/data');E=pathlib.Path('docs/evidence/scale/places');start=time.time()
lock=(D.parent/'second-compute.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX)
db=sqlite3.connect('file:'+str(D/'androidlm-places.db')+'?mode=ro',uri=True);db.execute('PRAGMA cache_size=-65536');db.execute('PRAGMA temp_store=FILE');db.execute('PRAGMA threads=0');db.create_function('name_norm',1,norm,deterministic=True)
kinds={r[0]:{'name':r[1],'parents':r[2].split(',')} for r in db.execute('SELECT * FROM kinds')};metadata=dict(db.execute('SELECT * FROM meta'))
columns=['name','street','locality','phone','website','hours','cuisine','wiki','alt']
fill={name:db.execute('SELECT count(*) FROM places WHERE "'+name+'" IS NOT NULL AND "'+name+'"<>\'\'').fetchone()[0] for name in columns}
base={'rows':db.execute('SELECT count(*) FROM places').fetchone()[0],'distinct_local_primary_ids':db.execute('SELECT count(DISTINCT id) FROM places').fetchone()[0],'exact_normalized_name_quantized_coordinate_kind_groups':db.execute('SELECT count(*) FROM (SELECT name_norm(name),lat5,lon5,kind FROM places GROUP BY 1,2,3,4)').fetchone()[0],'nonempty_field_counts':fill,'nonzero_diet_bitmask':db.execute('SELECT count(*) FROM places WHERE diet<>0').fetchone()[0],'kinds':len(kinds),'cities':db.execute('SELECT count(*) FROM cities').fetchone()[0],'city_names':db.execute('SELECT count(*) FROM city_names').fetchone()[0],'guide_listing_rows':db.execute('SELECT count(*) FROM guide').fetchone()[0],'metadata':metadata,'receipt':json.loads((E/'androidlm-places.receipt.json').read_text())};print('baseline aggregates complete',round(time.time()-start,2),flush=True)

base['seconds']=time.time()-start;atomic_json(E/'androidlm-aggregate.json',base);print(json.dumps(base,indent=2));db.close()
