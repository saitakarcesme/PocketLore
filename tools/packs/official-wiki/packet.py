"""Freeze systematic original XML representatives and authoritative terms, not clearance claims."""
import base64,bz2,hashlib,json,re,sqlite3
from pathlib import Path
R=Path(__file__).resolve().parents[3];D=R/'downloads/official-wiki';out=R/'docs/evidence/broad-corpus-admission-review.json'
assert not out.exists(),'Do not overwrite frozen packet'
c=sqlite3.connect(D/'index-v1/provenance.sqlite');c.row_factory=sqlite3.Row
samples={r['sample_id']:dict(r) for r in c.execute('select * from partitions')};docs={r['id']:dict(r) for r in c.execute('select * from documents') if r['id'] in samples}
archive=D/json.loads((R/'tools/packs/official-wiki/shard-pin.json').read_text())['name'];pages={};buf=None
with bz2.open(archive,'rb') as f:
 for line in f:
  if line.strip()==b'<page>':buf=bytearray()
  if buf is not None:
   buf.extend(line)
   if len(buf)>8_000_000:raise ValueError('XML record exceeds packet collector bound')
   if line.strip()==b'</page>':
    raw=bytes(buf);identifier=int(re.search(rb'<id>(\d+)</id>',raw).group(1))
    if identifier in samples:pages[identifier]=raw
    buf=None
assert set(pages)==set(samples)
def payload(b):return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'base64':base64.b64encode(b).decode()}
records=[]
for identifier,sample in sorted(samples.items()):
 d=docs[identifier];d.pop('raw_zlib');records.append({'partition':sample,'document':d,'original_page_xml':payload(pages[identifier]),'candidate_spans':[dict(r) for r in c.execute('select * from spans where doc=?',(identifier,))]})
authority={name:payload((D/name).read_bytes()) for name in ['terms.raw','license.raw','status.raw','sha1.raw','acquisition.json','dump-acquisition.json',archive.name+'.receipt.json']}
x={'status':'INCOMPLETE_NOT_ADMITTED','scope':'Official first shard primary-source evidence; not blanket rights approval, not Android installation','authority':authority,'index_receipt':json.loads((D/'index-v1/receipt.json').read_text()),'source_records':records,'criteria':{'url_attribution':'Wikimedia Terms7g allows an article URL; full contributor-list copies not universally required','license':'CC BY-SA4.0 with modifications disclosed and additional notices preserved','exceptions':'Unresolved third-party quotation, imported text and notice-producing templates require disposition; current index is pending','mapping':'Exact decoded wikitext UTF16 spans; markup excluded, never silently rewritten'},'research_admitted_documents':0,'android_run':None,'remaining_gates':['Source-specific notice/template/quotation dispositions','Full declared inventory, distinct from first-shard pilot','Admitted edition integration and real API37 flows','Current complete installed/update budget']}
data=(json.dumps(x,indent=2)+'\n').encode();assert len(data)<8_000_000;out.write_bytes(data)
print('Frozen original packet bytes',len(data))
