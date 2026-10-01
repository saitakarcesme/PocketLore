"""Host boundary and source-safety regressions; not Android device acceptance."""
import json,pathlib,sqlite3,tempfile,unittest,uuid,zlib
from search import search
from enrich import osm_search
from wikivoyage_xml import listings
class ReaderTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=pathlib.Path(self.tmp.name)/'places.sqlite';d=sqlite3.connect(self.path)
  d.executescript('CREATE TABLE place(id BLOB,name TEXT,name_key TEXT,lat REAL,lon REAL,gx INTEGER,gy INTEGER,category TEXT,city TEXT,country TEXT,confidence REAL,status TEXT,entity_key BLOB); CREATE TABLE category(place_id BLOB,category TEXT);')
  import math
  # Equidistant antimeridian neighbors plus a false grid candidate outside the circle.
  for i,lat,lon,entity in [(1,0,179.99,1),(2,0,-179.99,2),(3,0,179.8,3),(4,0,179.99,1),(5,89.99,90,5),(6,89.99,-90,6)]:
   identity=uuid.UUID(int=i).bytes;d.execute('INSERT INTO place VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(identity,'Cafe','cafe',lat,lon,math.floor((lon+180)*100),math.floor((lat+90)*100),'cafe','Test','ZZ',.9,'open',uuid.UUID(int=entity).bytes));d.execute('INSERT INTO category VALUES(?,?)',(identity,'food_and_drink'))
  d.commit();d.close()
 def tearDown(self):self.tmp.cleanup()
 def test_antimeridian_and_dedup(self):
  r=search([self.path],0,180,3);self.assertEqual(len(r),2);self.assertTrue(all(x['live_status'] is None for x in r))
 def test_pole(self):self.assertEqual(len(search([self.path],90,0,3)),2)
 def test_category_ancestor(self):self.assertEqual(len(search([self.path],0,180,3,category='food_and_drink')),2)
 def test_unknown_diet(self):self.assertEqual(search([self.path],0,180,3,diet='vegan'),[])
 def test_absence(self):self.assertEqual(search([self.path],0,180,3,name='Absent'),[])
 def test_radius(self):self.assertEqual(search([self.path],0,180,.1),[])
 def test_limit(self):self.assertEqual(len(search([self.path],0,180,3,limit=1)),1)
 def test_invalid(self):
  for lat,lon,rad in [(91,0,1),(0,181,1),(0,0,101),(float('nan'),0,1)]:
   with self.assertRaises(ValueError):search([self.path],lat,lon,rad)
 def test_nested_listing_templates(self):
  a=list(listings('{{eat|name=A {{lang|en|Cafe}}|content=[[A|B]]|hours=Unknown|lat=1|long=2}}'))
  self.assertEqual(len(a),1);self.assertEqual(a[0][1]['name'],'A {{lang|en|Cafe}}');self.assertEqual(a[0][1]['content'],'[[A|B]]')
if __name__=='__main__':unittest.main()
