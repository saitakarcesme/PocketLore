"""Tiny constructed stage transactions; counts excluded from real corpus reports."""
import json,sqlite3,tempfile,unittest,zlib
from pathlib import Path
import compact as c
from test_compact import record

class Transactions(unittest.TestCase):
    def stage(self,p,docs,corrupt=None):
        db=sqlite3.connect(p);db.execute('CREATE TABLE records(sequence INTEGER PRIMARY KEY,member TEXT,member_offset INTEGER,raw_bytes INTEGER,raw_sha256 TEXT,page INTEGER,revision INTEGER,title TEXT,license_json TEXT,metadata_error TEXT,original_zlib BLOB)')
        for i,d in enumerate(docs):
            raw=c.canonical(d);title=d['name'] if corrupt!='metadata' or i==0 else 'Changed stage title'
            digest=c.sha(raw) if corrupt!='digest' or i==0 else '0'*64
            db.execute('INSERT INTO records VALUES(?,?,?,?,?,?,?,?,?,?,?)',(i,'constructed.ndjson',i*100,len(raw),digest,d['identifier'],d['version']['identifier'],title,json.dumps(d['license']),None,zlib.compress(raw)))
        db.commit();db.close()
    def test_unsafe_latest_and_retry(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[3]/'downloads') as t:
            p=Path(t);old=record();new=record(rev=3);new['license'][0]['url']='invalid'
            self.stage(p/'stage',[old,new]);r=c.produce(p/'stage',p/'out',1,20)
            self.assertEqual(r['counts']['articles'],0);self.assertEqual(r['counts']['dispositions'],2)
            with self.assertRaises(ValueError):c.produce(p/'stage',p/'out',1,20)
            self.assertEqual(json.loads((p/'out/receipt.json').read_text())['status'],'ENGINEERING_COMPLETE_PROVISIONAL')
    def test_provenance_failure_retained(self):
        for fault in ['metadata','digest']:
            with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[3]/'downloads') as t:
                p=Path(t);self.stage(p/'stage',[record(),record(rev=3)],fault)
                with self.assertRaises(ValueError):c.produce(p/'stage',p/'out',1,20)
                self.assertEqual(json.loads((p/'out/receipt.json').read_text())['status'],'FAIL_RETAINED')
    def test_late_older_conflict(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[3]/'downloads') as t:
            p=Path(t);self.stage(p/'stage',[record(rev=2),record(rev=3),record(rev=2,text='Changed old revision')]);r=c.produce(p/'stage',p/'out',2,20)
            self.assertEqual(r['counts']['articles'],0);self.assertEqual(r['counts']['latest'],1)
    def test_oversized_disposition(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[3]/'downloads') as t:
            p=Path(t);self.stage(p/'stage',[record()]);db=sqlite3.connect(p/'stage');db.execute('CREATE TABLE oversized(sequence INTEGER PRIMARY KEY,member TEXT,member_offset INTEGER,raw_bytes INTEGER,raw_sha256 TEXT)');db.execute("INSERT INTO oversized VALUES(1,'constructed',100,17000000,'unverified-fixture-hash')");db.commit();db.close()
            r=c.produce(p/'stage',p/'out',1,20);self.assertEqual(r['counts']['dispositions'],2);self.assertEqual(r['unverified_oversized_records'],1);self.assertFalse(r['source_admission_established'])
    def test_cancel_deadline_retains(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[3]/'downloads') as t:
            p=Path(t);self.stage(p/'stage',[record()])
            with self.assertRaises(ValueError):c.produce(p/'stage',p/'out',0,0)
            self.assertEqual(json.loads((p/'out/receipt.json').read_text())['status'],'FAIL_RETAINED')
    def test_capsule_reader_corrupt_missing(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[3]/'downloads') as t:
            p=Path(t);self.stage(p/'stage',[record()]);c.produce(p/'stage',p/'out',0,20)
            r=c.Reader(p/'out');self.assertTrue(r.search('literal'))
            calls=[0]
            def cancel_during():
                calls[0]+=1;return calls[0]>=3
            with self.assertRaises((ValueError,sqlite3.OperationalError)):r.search('literal',cancel_during)
            self.assertGreaterEqual(calls[0],3);r.db.close()
            with (p/'out/index.sqlite').open('r+b') as f:f.seek(100);f.write(b'corrupt')
            with self.assertRaises(ValueError):c.Reader(p/'out')
            (p/'out/index.sqlite').rename(p/'retained-corrupt.sqlite')
            with self.assertRaises(FileNotFoundError):c.Reader(p/'out')
if __name__=='__main__':unittest.main()
