"""Offline constructed privacy/integrity fixtures; not Android qualification."""
import tempfile,pathlib,sys,importlib.util,json,hashlib,base64
p=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(p));sp=importlib.util.spec_from_file_location('runtime_check',p/'check.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
with tempfile.TemporaryDirectory() as t:
 root=pathlib.Path(t);m.ROOT=root;(root/'docs/evidence/android-runtime-durability').mkdir(parents=True);out=root/'run';out.mkdir()
 (out/'before.txt').write_bytes(b'SQLite format 3\x00'+b'constructed private body')
 (out/'ordinary.txt').write_bytes(b'public raw receipt\n')
 source='print("original")\n';code={'fixture.py':{'content':source,'sha256':hashlib.sha256(source.encode()).hexdigest()}}
 (out/'executed-sources.json').write_text(json.dumps(code));m.freeze_packet(out)
 packet=json.loads((root/'docs/evidence/android-runtime-durability-review.json').read_text());assert 'content' not in packet['raw_files']['before.txt'];assert base64.b64decode(packet['raw_files']['ordinary.txt']['content'])==b'public raw receipt\n';assert packet['executed_sources']==code
 code['fixture.py']['content']='changed';(out/'executed-sources.json').write_text(json.dumps(code))
 try:m.freeze_packet(out)
 except AssertionError:pass
 else:raise AssertionError('Corrupt source freeze accepted')
print('PASS constructed SQLite-extension exclusion, exact public bytes and changed source rejection')
