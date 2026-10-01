"""Index every GeoNames cities500 row and all supplied aliases, retaining source fields."""
import hashlib,io,json,pathlib,sqlite3,sys,zipfile
from common import norm,atomic_json
def build(src,dest):
 dest=pathlib.Path(dest)
 if dest.exists():raise RuntimeError('Immutable output exists')
 db=sqlite3.connect(dest.with_suffix('.building.sqlite'))
 db.executescript('CREATE TABLE city(id INTEGER PRIMARY KEY,name TEXT,ascii_name TEXT,lat REAL,lon REAL,country TEXT,population INTEGER,modified TEXT,raw TEXT); CREATE TABLE alias(name_key TEXT,city_id INTEGER,alias TEXT,PRIMARY KEY(name_key,city_id)) WITHOUT ROWID; CREATE INDEX city_grid ON city(lat,lon);')
 with zipfile.ZipFile(src) as z:
  with io.TextIOWrapper(z.open('cities500.txt'),encoding='utf-8') as f:
   for line in f:
    r=line.rstrip('\n').split('\t');identity=int(r[0]);db.execute('INSERT INTO city VALUES(?,?,?,?,?,?,?,?,?)',(identity,r[1],r[2],float(r[4]),float(r[5]),r[8],int(r[14]),r[18],line.rstrip('\n')))
    for a in set([r[1],r[2]]+r[3].split(',')):
     if a:db.execute('INSERT OR IGNORE INTO alias VALUES(?,?,?)',(norm(a),identity,a))
 db.commit();report={'cities':db.execute('SELECT count(*) FROM city').fetchone()[0],'aliases':db.execute('SELECT count(*) FROM alias').fetchone()[0],'source_sha256':hashlib.file_digest(open(src,'rb'),'sha256').hexdigest(),'license':'CC-BY-4.0','scope':'cities500; not all populated settlements; nearest city is not municipal membership'};db.close();dest.with_suffix('.building.sqlite').rename(dest);report.update(bytes=dest.stat().st_size,sha256=hashlib.file_digest(dest.open('rb'),'sha256').hexdigest());atomic_json(dest.with_suffix('.report.json'),report);print(report)
if __name__=='__main__':build(*sys.argv[1:])
