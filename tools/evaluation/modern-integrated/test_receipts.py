"""Regression inputs are actual failed task400 bytes, never invented successful lane evidence."""
import importlib.util,json,pathlib,unittest
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('modern_check',HERE/'check.py');check=importlib.util.module_from_spec(spec);spec.loader.exec_module(check)
EVIDENCE=check.ROOT/'docs/evidence/modern-integrated/failures'
class Receipts(unittest.TestCase):
 def test_formatted_pass_does_not_replace_completion(self):
  first=EVIDENCE/'20261002T020922Z-0fb6e277/native-cards-recognition'
  report=json.loads((first/'report.json').read_text());self.assertEqual(report['status'],'PASS')
  with self.assertRaises(AssertionError):check.validate_transport((first/'runtime.txt').read_text(),json.loads((first/'runtime.txt.command.json').read_text()))
 def test_actual_raw_completion_requires_successful_transport(self):
  second=EVIDENCE/'20261002T021019Z-6f678acc/native-cards-recognition'
  raw=(second/'runtime.txt').read_text();meta=json.loads((second/'runtime.txt.command.json').read_text());check.validate_transport(raw,meta)
  for changed in [dict(meta,returncode=1),{'timeout_seconds':1},{}]:
   with self.assertRaises(AssertionError):check.validate_transport(raw,changed)
  for changed in [raw.replace('INSTRUMENTATION_CODE: -1','INSTRUMENTATION_CODE: 1'),raw+'\nProcess crashed']:
   with self.assertRaises(AssertionError):check.validate_transport(changed,meta)
 def test_actual_report_cannot_be_rebound_to_new_invocation(self):
  r=json.loads((EVIDENCE/'20261002T020922Z-0fb6e277/native-cards-recognition/report.json').read_text());check.validate(r,r['run_id'])
  with self.assertRaises(AssertionError):check.validate(r,'another-invocation')
  changed=dict(r,status='FAIL')
  with self.assertRaises(AssertionError):check.validate(changed,r['run_id'])

class EvidenceBundle(unittest.TestCase):
 def test_safe_report_and_unsafe_path(self):
  import io,tarfile,tempfile
  payload=(EVIDENCE/'20261002T020922Z-0fb6e277/native-cards-recognition/report.json').read_bytes()
  for name,allowed in [('report.json',True),('../outside.json',False),('model.gguf',False)]:
   raw=io.BytesIO()
   with tarfile.open(fileobj=raw,mode='w') as t:
    entry=tarfile.TarInfo(name);entry.size=len(payload);t.addfile(entry,io.BytesIO(payload))
   with tempfile.TemporaryDirectory() as d:
    if allowed:
     check.unpack(raw.getvalue(),pathlib.Path(d));self.assertEqual((pathlib.Path(d)/name).read_bytes(),payload)
    else:
     with self.assertRaises(AssertionError):check.unpack(raw.getvalue(),pathlib.Path(d))
 def test_truncated_archive_rejected(self):
  with self.assertRaises(Exception):check.unpack(b'broken tar',pathlib.Path('/tmp'))

if __name__=='__main__':unittest.main()
