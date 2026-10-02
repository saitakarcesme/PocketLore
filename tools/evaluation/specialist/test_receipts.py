"""Actual local command failures and stale-report controls; no Android or inference."""
import json,pathlib,subprocess,sys,tempfile,unittest
from check import record_command,verify_report
class Receipts(unittest.TestCase):
 def test_empty_nonzero_is_fatal_and_recorded(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)
   with self.assertRaises(AssertionError):record_command(p,[sys.executable,'-c','raise SystemExit(9)'],'failure.txt')
   self.assertEqual((p/'failure.txt').read_bytes(),b'')
   self.assertEqual(json.loads((p/'failure.txt.command.json').read_text())['returncode'],9)
 def test_timeout_is_fatal_and_recorded(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)
   with self.assertRaises(subprocess.TimeoutExpired):record_command(p,[sys.executable,'-c','import time; time.sleep(2)'],'timeout.txt',timeout=.05)
   self.assertEqual(json.loads((p/'timeout.txt.command.json').read_text())['timeout_seconds'],.05)
 def test_pass_report_cannot_replace_another_run(self):
  r={'run_id':'first','status':'PASS','pack_sha256':'pin'}
  verify_report(r,'first','pin')
  for altered in [dict(r,run_id='old'),{k:v for k,v in r.items() if k!='run_id'},dict(r,pack_sha256='changed')]:
   with self.assertRaises(AssertionError):verify_report(altered,'first','pin')
if __name__=='__main__':unittest.main()
