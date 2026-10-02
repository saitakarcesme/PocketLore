"""Project only the six approved field slices; never ship reviewer raw rows."""
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[3]
SOURCE=pathlib.Path('/home/isa/PocketLore-control/scale-workers/quality-preparation/source-review')
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 handoff=(SOURCE/'HANDOFF.json').read_bytes();assert sha(handoff)=='03388b4678a24a4984d6b3718907d4da2b501cfadfedc5b269e902d48387310c'
 files=json.loads(handoff)['files']
 for f in files:
  b=(SOURCE/f['path']).read_bytes();assert sha(b)==f['sha256'] and len(b)==f['bytes'],f['path']
 assert sha((SOURCE/'proposed-integration-task-v2.json').read_bytes())=='5e6498f1727af08e3cefae329440d9c9dbdb365d5db8722727eb62dd8f8694ad'
 allowed=['geonameid','name','latitude','longitude','country_code','modification_date'];cards=[]
 for id in [292223,292672,292968]:
  p=json.loads((SOURCE/f'packets/geonames-{id}.json').read_text());identity=p['identity'];raw=(SOURCE/p['installed_file']).read_text();fields=p['quoted_fields'];assert [f['field'] for f in fields]==allowed
  assert sha(raw.encode())==identity['stored_row_sha256']
  for f in fields:assert raw.encode('utf-16-le')[f['start_utf16']*2:f['end_utf16']*2].decode('utf-16-le')==f['quote'] and sha(f['quote'].encode())==f['sha256']
  cards.append({'id':str(id),'archive_sha256':identity['archive_sha256'],'original_row_sha256':identity['original_row_sha256'],'stored_row_sha256':identity['stored_row_sha256'],'acquired_utc':identity['acquired_utc'],'source_url':identity['source_url'],'fields':fields,'notice':(SOURCE/f'packets/geonames-{id}-NOTICE.txt').read_text(),'packet_sha256':sha((SOURCE/f'packets/geonames-{id}.json').read_bytes())})
 payload={'schema':1,'handoff_sha256':sha(handoff),'cards':cards,'license_html':(SOURCE/'evidence/licenses/CC-BY-4.0.html').read_text(),'license_sha256':sha((SOURCE/'evidence/licenses/CC-BY-4.0.html').read_bytes())}
 b=(json.dumps(payload,ensure_ascii=False,indent=2)+'\n').encode();assert len(b)<=200000
 dest=ROOT/'android/app/src/main/assets/reviewed-cities.json';dest.write_bytes(b)
 (ROOT/'tools/evaluation/nearby-travel/payload-pin.json').write_text(json.dumps({'sha256':sha(b),'bytes':len(b),'records':[292223,292672,292968],'fields':allowed},indent=2)+'\n')
 print(sha(b),len(b))
if __name__=='__main__':main()
