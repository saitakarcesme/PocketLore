"""Host source preservation and corruption checks on a synthetic Parquet fixture."""
import hashlib,json,pathlib,sqlite3,struct,tempfile,unittest,uuid,zlib
import pyarrow as pa,pyarrow.parquet as pq
from compact import build
from compact_search import search,source,group_sources
class CompactTests(unittest.TestCase):
 def test_source_and_boundaries(self):
  with tempfile.TemporaryDirectory(dir='/home/isa/PocketLore-control/scale-workers/places') as tmp:
   root=pathlib.Path(tmp);src=root/'fixture.parquet';records=[]
   for i,lon in enumerate([179.99,-179.99,170],1):
    records.append({'id':str(uuid.UUID(int=i)),'geometry':struct.pack('<BIdd',1,1,lon,0),'names':{'primary':'Fixture Café'},'basic_category':'cafe','taxonomy':{'primary':'cafe','hierarchy':['food_and_drink','cafe'],'alternates':[]},'addresses':[{'locality':'Fixture City','country':'ZZ'}],'confidence':.5,'operating_status':None,'sources':[{'dataset':'synthetic fixture','license':'test only','record_id':str(i)}]})
   conflict=json.loads(json.dumps(records[0],default=lambda v:v.hex()))
   conflict['id']=str(uuid.UUID(int=4));conflict['geometry']=records[0]['geometry'];conflict['confidence']=.7;conflict['sources'][0]['record_id']='4';records.append(conflict)
   pq.write_table(pa.Table.from_pylist(records),src);src.with_suffix('.parquet.receipt.json').write_text(json.dumps({'sha256':hashlib.sha256(src.read_bytes()).hexdigest()}));dest=root/'compact.sqlite';build(src,dest)
   hits=search([dest],0,180,3,category='food_and_drink');self.assertEqual(len(hits),2);self.assertEqual(search([dest],0,180,3,diet='vegan'),[])
   for hit in hits:
    info=source(dest,hit['block_id'],hit['source_ordinal'],hit['id']);expected=dict(records[int(hit['id'][-1])-1]);del expected['geometry'];self.assertEqual(info['record'],expected);self.assertIsNone(hit['live_status'])
   variants=list(group_sources([dest],'Fixture Café',0,179.99,'cafe'));self.assertEqual({r['id'] for r in variants},{str(uuid.UUID(int=1)),str(uuid.UUID(int=4))});self.assertEqual({r['record']['confidence'] for r in variants},{.5,.7})
   self.assertEqual(search([dest],0,180,3,name='Absent'),[])
   db=sqlite3.connect(dest);blob=db.execute('SELECT payload FROM block LIMIT 1').fetchone()[0];bad=bytearray(blob);bad[len(bad)//2]^=1;db.execute('UPDATE block SET payload=?',(bytes(bad),));db.commit();db.close()
   with self.assertRaises((ValueError,zlib.error)):search([dest],0,180,3)
if __name__=='__main__':unittest.main()
