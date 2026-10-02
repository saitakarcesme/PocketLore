"""Local subprocess controls; no Android commands or product inference."""
import json
import pathlib
import sys
import tempfile
import unittest
from capture import capture

class CaptureTest(unittest.TestCase):
    def run_case(self,code,timeout=5):
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp)/'raw.txt'
            raw,receipt=capture([sys.executable,'-u','-c',code],p,cwd=tmp,timeout=timeout)
            self.assertEqual(p.read_bytes(),raw)
            self.assertEqual(json.loads(p.with_name('raw.txt.command.json').read_text()),receipt)
            return raw,receipt

    def test_failed_transport_keeps_receipt_stream(self):
        raw,r=self.run_case("import sys; print('partial receipt'); print('failure detail',file=sys.stderr); sys.exit(7)")
        self.assertEqual(r['returncode'],7)
        self.assertIn(b'partial receipt',raw);self.assertIn(b'failure detail',raw)

    def test_timeout_keeps_partial_stream(self):
        raw,r=self.run_case("import time; print('before timeout'); time.sleep(5)",1)
        self.assertTrue(r['timed_out']);self.assertIsNone(r['returncode'])
        self.assertIn(b'before timeout',raw)

    def test_success(self):
        raw,r=self.run_case("print('local success')")
        self.assertEqual(r['returncode'],0);self.assertFalse(r['timed_out'])
        self.assertEqual(raw,b'local success\n')

    def test_missing_executable_keeps_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp)/'raw.txt'
            raw,r=capture([str(pathlib.Path(tmp)/'missing')],p,cwd=tmp)
            self.assertEqual(r['error'],'FileNotFoundError');self.assertIsNone(r['returncode'])
            self.assertEqual(raw,b'');self.assertTrue(p.with_name('raw.txt.command.json').exists())

if __name__=='__main__':unittest.main()
