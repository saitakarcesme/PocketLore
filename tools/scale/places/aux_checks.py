"""Inspect frozen-city GeoNames rows and travel pages against original bulk sources."""
import bz2,io,json,pathlib,sqlite3,xml.etree.ElementTree as ET,zipfile,zlib
from catalog import Catalog
from common import atomic_json
D=pathlib.Path('/home/isa/PocketLore-control/scale-workers/places/data');E=pathlib.Path('docs/evidence/scale/places');catalog=Catalog([],D/'cities.sqlite',D/'osm.sqlite',D/'wikivoyage.sqlite')
names=sorted({q['city'] for q in json.loads((E/'queries-frozen.json').read_text())['queries']});cities={};travel={};coverage=[]
for name in names:
 found=catalog.city_candidates(name);pages=catalog.travel(name);coverage.append({'city':name,'geonames_candidates':len(found),'exact_travel_titles':len(pages)})
 if found:cities[found[0]['id']]=found[0]
 if pages:travel[pages[0]['id']]=catalog.travel_source(pages[0]['id'])
city_checked=set()
with zipfile.ZipFile(D/'cities500-2026-10-01.zip') as archive:
 with io.TextIOWrapper(archive.open('cities500.txt'),encoding='utf-8') as stream:
  for line in stream:
   identity=int(line.split('\t',1)[0])
   if identity in cities:assert cities[identity]['raw']==line.rstrip('\n');city_checked.add(identity)
travel_checked=set();ns='{http://www.mediawiki.org/xml/export-0.11/}'
with bz2.open(D/'enwikivoyage-20260901-pages-articles.xml.bz2','rb') as stream:
 events=ET.iterparse(stream,events=('start','end'));_,root=next(events)
 for event,e in events:
  if event!='end' or e.tag!=ns+'page':continue
  identity=int(e.findtext(ns+'id'))
  if identity in travel:
   stored=travel[identity];rev=e.find(ns+'revision');assert stored['wikitext']==(rev.findtext(ns+'text') or '');assert str(stored['revision'])==rev.findtext(ns+'id');assert stored['timestamp']==rev.findtext(ns+'timestamp')
   for listing in stored['listings']:assert listing['raw'] in stored['wikitext']
   travel_checked.add(identity)
  e.clear();root.clear()
assert city_checked==set(cities);assert travel_checked==set(travel)
db=sqlite3.connect('file:'+str(D/'wikivoyage.sqlite')+'?mode=ro',uri=True);maximum=0
for packed, in db.execute('SELECT wikitext_zlib FROM page'):maximum=max(maximum,len(zlib.decompress(packed)))
db.close();assert maximum<=16*1024*1024
report={'frozen_city_coverage':coverage,'original_geonames_rows_checked':sorted(city_checked),'original_xml_pages_checked':sorted(travel_checked),'checks_passed':True,'max_wikitext_bytes':maximum,'reader_wikitext_bound_bytes':16*1024*1024,'scope':'exact source rows/text/revision and literal listing containment; title absence is not destination coverage absence; no answer-quality acceptance'};atomic_json(E/'auxiliary-source-checks.json',report);print(json.dumps(report,indent=2))
