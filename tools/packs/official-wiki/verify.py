"""Verify actual authoritative bytes, original revision content and every projected span."""
import base64,bz2,hashlib,json,re,sqlite3,zlib,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[3];NS='{http://www.mediawiki.org/xml/export-0.11/}'
def payload(p):
 b=base64.b64decode(p['base64'],validate=True);assert len(b)==p['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256'];return b
def sha1base36(raw):
 n=int(hashlib.sha1(raw).hexdigest(),16);out=''
 while n:n,r=divmod(n,36);out='0123456789abcdefghijklmnopqrstuvwxyz'[r]+out
 return out.zfill(31)
def verify_packet(p):
 a={n:payload(v) for n,v in p['authority'].items()};assert b'CC BY-SA 4.0' in a['terms.raw'] and b'Attribution-ShareAlike 4.0' in a['license.raw']
 meta=json.loads(a['status.raw']);pin=p['index_receipt']['pin'];assert meta['jobs']['articlesmultistreamdump']['files'][pin['name']]['sha1']==pin['sha1'];assert (pin['sha1']+'  '+pin['name']) in a['sha1.raw'].decode().splitlines()
 assert meta['jobs']['articlesmultistreamdump']['files'][pin['name']]['size']==pin['size']
 assert hashlib.sha256(a['status.raw']).hexdigest()==pin['status_sha256']
 assert len(p['source_records'])==16
 assert len({r['document']['id'] for r in p['source_records']})==16
 assert {r['partition']['partition'] for r in p['source_records']}==set(range(16))
 assert sum(r['partition']['documents'] for r in p['source_records'])==p['index_receipt']['counts']['indexed_documents']
 for r in p['source_records']:
  e=ET.fromstring(b'<root xmlns="'+NS[1:-1].encode()+b'">'+payload(r['original_page_xml'])+b'</root>').find(NS+'page');d=r['document'];rev=e.find(NS+'revision');text=rev.findtext(NS+'text') or ''
  assert e.findtext(NS+'ns')=='0' and e.find(NS+'redirect') is None and rev.findtext(NS+'model')=='wikitext'
  assert d['id']%16==r['partition']['partition'] and d['id']==r['partition']['sample_id']
  assert d['url']=='https://en.wikipedia.org/?curid='+str(d['id'])
  assert d['history_url']=='https://en.wikipedia.org/w/index.php?curid='+str(d['id'])+'&action=history'
  assert d['revision_url']=='https://en.wikipedia.org/w/index.php?oldid='+str(d['revision'])
  assert sha1base36(text.encode())==d['text_sha1']
  assert int(e.findtext(NS+'id'))==d['id'] and int(rev.findtext(NS+'id'))==d['revision']
  assert e.findtext(NS+'title')==d['title'] and rev.findtext(NS+'timestamp')==d['date']
  assert hashlib.sha256(text.encode()).hexdigest()==d['text_sha256'];assert rev.findtext(NS+'sha1')==d['text_sha1']
  for s in r['candidate_spans']:verify_span(text,s)
  assert d['rights']=='pending_source_specific_rights_and_fidelity'
 assert p['research_admitted_documents']==0 and p['android_run'] is None
 return len(p['source_records'])
def verify_span(text,s):
 b=text.encode('utf-16-le');assert 0<=s['start_utf16']<s['end_utf16']<=len(b)//2;span=b[2*s['start_utf16']:2*s['end_utf16']].decode('utf-16-le');assert span==s['text'] and hashlib.sha256(span.encode()).hexdigest()==s['sha256']
def main():
 p=json.loads((R/'docs/evidence/broad-corpus-admission-review.json').read_text());print('Original systematic source packets verified',verify_packet(p))
 pin=p['index_receipt']['pin'];archive=R/'downloads/official-wiki'/pin['name']
 with archive.open('rb') as f:assert hashlib.file_digest(f,'sha1').hexdigest()==pin['sha1']
 assert archive.stat().st_size==pin['size']
 wanted={r['document']['id']:payload(r['original_page_xml']) for r in p['source_records']};found=set();buf=None
 with bz2.open(archive,'rb') as f:
  for line in f:
   if line.strip()==b'<page>':buf=bytearray()
   if buf is not None:
    buf.extend(line);assert len(buf)<=8_000_000
    if line.strip()==b'</page>':
     raw=bytes(buf);identifier=int(re.search(rb'<id>(\d+)</id>',raw).group(1))
     if identifier in wanted:assert raw==wanted[identifier];found.add(identifier)
     buf=None
 assert found==set(wanted)
 db=sqlite3.connect('file:'+str(R/'downloads/official-wiki/index-v1/provenance.sqlite')+'?mode=ro',uri=True);db.row_factory=sqlite3.Row;count=0;spans=0;partitions={};partition_counts={}
 for d in db.execute('select * from documents'):
  raw=zlib.decompress(d['raw_zlib']);assert len(raw)==d['raw_utf8_bytes'] and hashlib.sha256(raw).hexdigest()==d['text_sha256'];text=raw.decode();assert d['rights']=='pending_source_specific_rights_and_fidelity'
  for s in db.execute('select * from spans where doc=?',(d['id'],)):verify_span(text,s);spans+=1
  assert sha1base36(raw)==d['text_sha1']
  part=d['id']%16;rank=hashlib.sha256(str(d['id']).encode()).hexdigest();partitions[part]=min(partitions.get(part,(rank,d['id'])),(rank,d['id']));partition_counts[part]=partition_counts.get(part,0)+1
  count+=1
 assert count==p['index_receipt']['counts']['indexed_documents'];assert spans==p['index_receipt']['counts']['candidate_plain_spans'];assert db.execute('pragma integrity_check').fetchone()[0]=='ok'
 for r in p['source_records']:
  part=r['partition']['partition'];assert partitions[part]==(r['partition']['sample_hash'],r['document']['id']);assert partition_counts[part]==r['partition']['documents']
 for kind in ['duplicate-samples','wrong-url','false-count','negative-offset','missing-license','corrupt-source','wrong-offset','false-admission']:
  q=json.loads(json.dumps(p))
  if kind=='duplicate-samples':q['source_records']=[q['source_records'][0]]*16
  elif kind=='wrong-url':q['source_records'][0]['document']['url']='https://example.invalid/'
  elif kind=='false-count':q['index_receipt']['counts']['indexed_documents']+=1
  elif kind=='negative-offset':
   row=next(r for r in q['source_records'] if r['candidate_spans']);row['candidate_spans'][0]['start_utf16']=-1
  elif kind=='missing-license':del q['authority']['license.raw']
  elif kind=='corrupt-source':q['source_records'][0]['original_page_xml']['sha256']='0'*64
  elif kind=='wrong-offset':
   row=next(r for r in q['source_records'] if r['candidate_spans']);row['candidate_spans'][0]['start_utf16']+=1
  else:q['research_admitted_documents']=count
  try:verify_packet(q)
  except (AssertionError,KeyError,UnicodeError):pass
  else:raise AssertionError('Mutation accepted: '+kind)
 print(json.dumps({'primary_documents_verified':count,'candidate_mapped_spans':spans,'negative_controls':8,'research_admitted':0,'status':'FAIL_PRODUCT_ADMISSION_AND_ANDROID_GATES'}))
 raise SystemExit(1)
if __name__=='__main__':main()
