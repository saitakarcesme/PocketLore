"""Verify the acquired planet against its separately downloaded official MD5."""
import fcntl,hashlib,json,pathlib,time
from common import atomic_json
D=pathlib.Path('/home/isa/PocketLore-control/scale-workers/places/data');p=D/'planet-260921.osm.pbf';slot=(D.parent/'second-compute.lock').open('a');fcntl.flock(slot,fcntl.LOCK_EX);start=time.time()
receipt=json.loads((D/'planet-official-md5.receipt.json').read_text());assert receipt['status']==200
expected=(D/'planet-260921-official-md5.txt').read_text().split()[0]
with p.open('rb') as stream:actual=hashlib.file_digest(stream,'md5').hexdigest()
report={'path':str(p),'bytes':p.stat().st_size,'official_md5':expected,'actual_md5':actual,'matched':actual==expected,'checksum_receipt':receipt,'seconds':time.time()-start,'sha256_receipt':json.loads(p.with_suffix('.receipt.json').read_text())};atomic_json('docs/evidence/scale/places/planet-official-checksum.json',report);print(json.dumps(report,indent=2));assert actual==expected
