"""Synthetic import/geometry regression; never counted as acquired place coverage."""
import hashlib,json,pathlib,sqlite3,tempfile,unittest
from planet import build
from planet_geometry import resolve
from enrich import osm_search
class PlanetTests(unittest.TestCase):
 def test_source_tags_and_complete_way_bounds(self):
  with tempfile.TemporaryDirectory(dir='/home/isa/PocketLore-control/scale-workers/places') as tmp:
   root=pathlib.Path(tmp);src=root/'fixture.osm'
   src.write_text('''<osm version="0.6" generator="PocketLore synthetic test">
<node id="1" lat="1" lon="2" version="1" timestamp="2026-09-01T00:00:00Z" changeset="1"><tag k="name" v="Fixture cafe"/><tag k="diet:vegan" v="yes"/></node>
<node id="2" lat="1.1" lon="2.2" version="1" timestamp="2026-09-01T00:00:00Z" changeset="1"/>
<way id="3" version="1" timestamp="2026-09-01T00:00:00Z" changeset="1"><nd ref="1"/><nd ref="2"/><tag k="name" v="Fixture building"/><tag k="opening_hours" v="Mo 09:00-17:00"/><tag k="diet:vegan" v="no"/></way>
<relation id="4" version="1" timestamp="2026-09-01T00:00:00Z" changeset="1"><member type="way" ref="3" role="outer"/><tag k="diet:vegetarian" v="only"/></relation></osm>''')
   src.with_suffix('.receipt.json').write_text(json.dumps({'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'url':'synthetic fixture','retrieved_utc':'2026-10-01T00:00:00Z'}))
   base=root/'base.sqlite';final=root/'geometry.sqlite';build(src,base);resolve(src,base,final,root/'work.sqlite')
   db=sqlite3.connect(final);self.assertEqual(db.execute('SELECT count(*) FROM osm').fetchone()[0],3)
   lat,lon,hours=db.execute("SELECT lat,lon,hours FROM osm WHERE type='way'").fetchone();self.assertAlmostEqual(lat,1.05);self.assertAlmostEqual(lon,2.1);self.assertEqual(hours,'Mo 09:00-17:00')
   self.assertEqual(db.execute("SELECT lat,lon FROM osm WHERE type='relation'").fetchone(),(None,None));db.close()
   hits=osm_search(final,1,2,50,'vegan');self.assertEqual([(r['type'],r['id']) for r in hits],[('node',1)]);self.assertIsNone(hits[0]['live_status'])
if __name__=='__main__':unittest.main()
