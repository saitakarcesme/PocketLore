"""Focused corruption and fidelity regressions against actual acquired rows."""
import collections,hashlib,json,pathlib,sqlite3,tempfile,unittest,zlib
from build import eligibility,lead,notice_candidate
from redirects import sql_tuple
from supplements import extract as extract_supplement
from reader import Reader,STOP as READER_STOP
from index_text import body as index_body,STOP as INDEX_STOP
LANE=pathlib.Path('/home/isa/PocketLore-control/scale-workers/wiki')
class Contract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows=json.loads((LANE/'receipts/counterexample-source.json').read_text())
 def test_real_math_survives(self):
  r=next(x for x in self.rows if x['title']=='(+)-Menthofuran synthase')
  self.assertIn('NADPH + H+ + O2',r['text']);self.assertIn('rightleftharpoons',r['text'])
  payload=json.dumps({'text':r['text'],'wikitext':r['wikitext']},ensure_ascii=False).encode()
  self.assertEqual(zlib.decompress(zlib.compress(payload)),payload)
 def test_real_revision_and_units(self):
  r=self.rows[0];self.assertEqual(r['version'],1167219203);self.assertEqual(r['date_modified'],'2023-07-26T12:32:03Z');self.assertIn('1938',r['text'])
 def test_unresolved_rights_fail_closed(self):
  for marker in ['{{copyvio|url=x}}','{{Permission pending}}','{{close paraphrasing|date=2025}}']:
   r=dict(self.rows[0]);r['wikitext']+=marker;self.assertTrue(eligibility(r).startswith('unresolved_rights_marker'))
 def test_missing_facts_not_invented(self):
  for field in ['version','wikitext','date_modified','url']:
   r=dict(self.rows[0]);r[field]=None;self.assertIn(field,eligibility(r))
 def test_lead_is_explicit_prefix(self):
  r=self.rows[0];x=lead(r['text']);self.assertTrue(r['text'].startswith(x.rstrip()));self.assertNotIn('## First Formation',x)
 def test_raw_notice_not_lost(self):
  r=self.rows[0];self.assertIn('{{Cite web',r['wikitext']);self.assertIn('Niehorster',r['wikitext'])
 def test_primary_redirect_sql_parser(self):
  self.assertEqual(sql_tuple("(10,0,'Computer_accessibility','',''),"),['10','0','Computer_accessibility','',''])
  self.assertEqual(sql_tuple("(12,0,'Newton\\'s_laws','','Motion'),"),['12','0',"Newton's_laws",'', 'Motion'])
 def test_real_cia_attribution_retention(self):
  rows=[json.loads(p.read_text())['record'] for p in (LANE/'receipts/query-sources').glob('*.json')]
  r=next(x for x in rows if x['title']=='Transport in Belgium')
  self.assertIn('{{CIA World Factbook|year=2009}}',r['wikitext'])
  self.assertTrue(notice_candidate(r['wikitext']))
  self.assertIn('2,950',r['text']);self.assertIn('km',r['text'])
 def test_notice_ranges_and_math_context(self):
  rows=[json.loads(p.read_text())['record'] for p in (LANE/'receipts/query-sources').glob('*.json')]
  r=next(x for x in rows if x['title']=='Transport in Belgium');fragment,ranges,scope=extract_supplement(r['wikitext'])
  self.assertIn('{{CIA World Factbook|year=2009}}',fragment)
  self.assertEqual(fragment,'\n\n'.join(r['wikitext'][a:b] for a,b in ranges))
  enzyme=self.rows[1];fragment,ranges,scope=extract_supplement(enzyme['wikitext'])
  self.assertIn('rightleftharpoons',fragment)
  self.assertEqual(fragment,'\n\n'.join(enzyme['wikitext'][a:b] for a,b in ranges))
  self.assertTrue(notice_candidate('{{ PD-notice|author=Example }}'))
  bad='{{Notice|unclosed';self.assertEqual(extract_supplement(bad)[0],bad)
 def test_lean_notice_math_and_unknown_templates(self):
  wiki='{{Infobox item|name=Example}}\n\n{{Cite web|title=Ordinary reference}}\n\n{{Unknown attribution|author=Example}}\n\n{{convert|12|km}}\n\nThis article incorporates public domain text from Example.'
  fragment,ranges,scope=extract_supplement(wiki,lean=True)
  self.assertNotIn('Ordinary reference',fragment);self.assertNotIn('Infobox item',fragment)
  self.assertIn('Unknown attribution',fragment);self.assertIn('{{convert|12|km}}',fragment);self.assertIn('public domain text',fragment)
  self.assertEqual(fragment,'\n\n'.join(wiki[a:b] for a,b in ranges))
  nested='{{Infobox item|distance={{convert|12|km}}}}'
  self.assertEqual(extract_supplement(nested,lean=True)[0],'{{convert|12|km}}')
  self.assertEqual(extract_supplement('unresolved source formula',lean=True,has_math=True)[0],'unresolved source formula')
  for r in self.rows[:2]:
   fragment,ranges,scope=extract_supplement(r['wikitext'],lean=True,has_math=bool(r['has_math']))
   self.assertEqual(fragment,'\n\n'.join(r['wikitext'][a:b] for a,b in ranges))
  rows=[json.loads(p.read_text())['record'] for p in (LANE/'receipts/query-sources').glob('*.json')]
  r=next(x for x in rows if x['title']=='Transport in Belgium')
  self.assertIn('{{CIA World Factbook|year=2009}}',extract_supplement(r['wikitext'],lean=True)[0])
 def test_real_empty_notice_candidate_falls_back(self):
  source=json.loads((LANE/'receipts/empty-candidate-real.json').read_text());wiki=source['wikitext']
  self.assertTrue(notice_candidate(wiki))
  self.assertEqual(extract_supplement(wiki,lean=True)[0],'')
  fragment,ranges,scope=extract_supplement(wiki,lean=True,preserve_empty_candidate=True)
  self.assertEqual(fragment,wiki);self.assertEqual(ranges,[[0,len(wiki)]])
  self.assertEqual(scope,'complete_empty_notice_candidate_fallback')
 def test_exact_title_with_only_stopwords(self):
  db=sqlite3.connect(':memory:');db.row_factory=sqlite3.Row
  db.executescript("CREATE TABLE articles(id INTEGER,title TEXT,tier TEXT,revision INTEGER,url TEXT); CREATE TABLE aliases(alias TEXT,target INTEGER); INSERT INTO articles VALUES(1,'A','full',2,'https://en.wikipedia.org/wiki/A'); INSERT INTO aliases VALUES('a',1);")
  reader=Reader.__new__(Reader);reader.dbs=[db];reader.packs=[pathlib.Path('fixture')];reader.alias_db=None;reader.total=1;reader.payload=lambda s,r:{'text':'The first letter.'}
  hits=reader.search('A')['hits'];self.assertEqual([h['title'] for h in hits],['A']);db.close()
 def test_normalized_alias_roundtrip(self):
  db=sqlite3.connect(':memory:');db.executescript("CREATE TABLE shard_names(id INTEGER PRIMARY KEY,name TEXT); CREATE TABLE aliases(alias TEXT,target INTEGER,shard INTEGER,fragment TEXT); INSERT INTO shard_names VALUES(0,'000_00014.parquet'); INSERT INTO aliases VALUES('museum plaza',4057884,0,'');")
  reader=Reader.__new__(Reader);reader.alias_db=db;reader.alias_normalized=True
  self.assertEqual(reader.alias_rows('Museum_Plaza'),[(4057884,'000_00014.parquet','')]);db.close()
 def test_index_only_omission_contract(self):
  self.assertEqual(READER_STOP,INDEX_STOP)
  self.assertEqual(index_body('The speed is 299,792,458 m/s.'),'  speed   299,792,458 m/s.')
  self.assertEqual(index_body('theorem and αtheβ'),'theorem   αtheβ')
  self.assertEqual(index_body('a_and_b'),' _ _b')
 def test_shared_block_real_records_and_corruption(self):
  with tempfile.TemporaryDirectory(dir=LANE) as tmp:
   p=pathlib.Path(tmp);payloads=[json.dumps({'text':x['text'],'wikitext':x['wikitext']},ensure_ascii=False).encode() for x in self.rows[:2]];raw=b''.join(payloads);packed=zlib.compress(raw);(p/'articles.blocks').write_bytes(packed)
   db=sqlite3.connect(':memory:');db.row_factory=sqlite3.Row;db.execute('CREATE TABLE blocks(id INTEGER,offset INTEGER,length INTEGER,raw_length INTEGER,sha256 BLOB)');db.execute('INSERT INTO blocks VALUES (1,0,?,?,?)',(len(packed),len(raw),hashlib.sha256(raw).digest()))
   reader=Reader.__new__(Reader);reader.packs=[p];reader.dbs=[db];reader.blocked=[True];reader.block_cache=collections.OrderedDict();offset=0
   for source,record in zip(self.rows,payloads):
    row={'block_id':1,'offset':offset,'length':len(record),'raw_length':len(record),'sha256':hashlib.sha256(record).digest(),'text_sha256':hashlib.sha256(source['text'].encode()).digest(),'wikitext_sha256':hashlib.sha256(source['wikitext'].encode()).digest()}
    self.assertEqual(reader.payload(0,row)['text'],source['text'])
    with self.assertRaises(ValueError):reader.payload(0,{**row,'offset':offset+1})
    offset+=len(record)
   reader.block_cache.clear();db.execute('UPDATE blocks SET sha256=?',(b'0'*32,))
   with self.assertRaises(ValueError):reader.payload(0,row)
   db.close()
 def test_block_rejection(self):
  with tempfile.TemporaryDirectory(dir=LANE) as tmp:
   p=pathlib.Path(tmp);raw=b'{"text":"formula x=1","wikitext":"{{PD-notice}}"}';packed=zlib.compress(raw);(p/'articles.blocks').write_bytes(packed)
   r=Reader.__new__(Reader);r.packs=[p];row={'offset':0,'length':len(packed),'raw_length':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'text_sha256':hashlib.sha256(b'formula x=1').hexdigest(),'wikitext_sha256':hashlib.sha256(b'{{PD-notice}}').hexdigest()}
   self.assertEqual(r.payload(0,row)['text'],'formula x=1')
   for key,val in [('sha256','0'*64),('length',len(packed)-1),('raw_length',len(raw)-1),('text_sha256','0'*64),('wikitext_sha256','0'*64)]:
    bad={**row,key:val}
    with self.assertRaises((ValueError,zlib.error)):r.payload(0,bad)
if __name__=='__main__':unittest.main()
