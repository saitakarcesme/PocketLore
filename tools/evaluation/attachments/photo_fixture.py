"""Explicit setup for one predeclared CC0 photo control, never an app download."""
import hashlib,json,urllib.request
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parents[3]
pin=json.loads((root/'docs/evidence/attachments/photo-supplement.json').read_text())
original=root/'downloads/attachments/stop-original.jpg'
if not original.exists():
 with urllib.request.urlopen(pin['original_url']) as response:original.write_bytes(response.read())
def verify(p,key):
 expected=pin['files'][key]
 assert p.stat().st_size==expected['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==expected['sha256'], 'Changed photo artifact'
verify(original,original.name)
output=root/'downloads/attachments/fixtures/photo.jpg'
Image.open(original).convert('RGB').resize((1600,1200),Image.Resampling.LANCZOS).save(output,quality=90)
verify(output,output.name)
print('Pinned photo control reproduced')
