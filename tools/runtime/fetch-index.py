"""Explicit reproducible setup; default builds verify cached immutable bytes offline."""
from pathlib import Path
import json,hashlib,urllib.request,zipfile,sys
R=Path(__file__).resolve().parents[2];pin=json.loads((R/'tools/runtime/sqlite-pin.json').read_text());root=R/'downloads/sqlite';archive=root/'sqlite-amalgamation-3530400.zip'
if '--verify-only' not in sys.argv:
 root.mkdir(parents=True,exist_ok=True)
 if not archive.exists():
  with urllib.request.urlopen(pin['url'],timeout=60) as response:archive.write_bytes(response.read())
raw=archive.read_bytes();assert hashlib.sha256(raw).hexdigest()==pin['sha256'] and hashlib.sha3_256(raw).hexdigest()==pin['sha3_256'],'SQLite archive identity'
source=root/'sqlite-amalgamation-3530400'
if '--verify-only' not in sys.argv:
 with zipfile.ZipFile(archive) as z:
  for name in pin['source_files']:
   data=z.read('sqlite-amalgamation-3530400/'+name);assert hashlib.sha256(data).hexdigest()==pin['source_files'][name];source.mkdir(exist_ok=True);(source/name).write_bytes(data)
for name,h in pin['source_files'].items():assert hashlib.sha256((source/name).read_bytes()).hexdigest()==h,'SQLite source identity'
print('Pinned SQLite source verified')
