"""Frozen constructed controls; never counted as factual corpus articles."""
import argparse, copy, fcntl, hashlib, html, json, os, signal, sqlite3, subprocess, sys, tempfile, time, unittest, zlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import compact as c
import production as p
from test_compact import record
ROOT=Path(__file__).resolve().parents[4]
BASE=ROOT/'downloads/complete-source-production-safety'
BASE.mkdir(exist_ok=True)
RESULTS=[]
# Constructed tests use a test-only absolute window; production CLI retains its frozen cutoff.
p.CUTOFF=time.time()+180

def stage(path,docs):
    db=sqlite3.connect(path);db.execute('PRAGMA journal_mode=WAL');db.execute('CREATE TABLE records(sequence INTEGER PRIMARY KEY,member TEXT,member_offset INTEGER,raw_bytes INTEGER,raw_sha256 TEXT,page INTEGER,revision INTEGER,title TEXT,license_json TEXT,metadata_error TEXT,original_zlib BLOB)')
    for i,d in enumerate(docs):append(db,i,d)
    db.commit();db.close()
def append(db,i,d):
    raw=c.canonical(d);db.execute('INSERT INTO records VALUES(?,?,?,?,?,?,?,?,?,?,?)',(i,'constructed.ndjson',i*100,len(raw),c.sha(raw),d['identifier'],d['version']['identifier'],d['name'],json.dumps(d['license']),None,zlib.compress(raw)))
def args(root,count,resume=False):
    return argparse.Namespace(mode='short',stage=str(root/'stage.sqlite'),out=str(root/'out'),ceiling=count-1,follow=False,seconds=30,cutoff=min(p.CUTOFF,time.time()+60),acquisition=None,stage_status=None,resume=resume)
def guard(root):return p.Guard(30,time.time()+60,root)

class Cases(unittest.TestCase):
    def setUp(self):self.root=Path(tempfile.mkdtemp(prefix='fixture-',dir=BASE))
    def tearDown(self):RESULTS.append({'test':self.id(),'directory':str(self.root),'files':{str(x.relative_to(self.root)):c.file_sha(x) for x in self.root.rglob('*') if x.is_file() and x.suffix!='sqlite'}})
    def test_cross_batch_conflict_unsafe_malformed(self):
        docs=[record(page=i+1,rev=2)for i in range(70)]
        docs.extend([record(page=1,rev=3),record(page=1,rev=2,text='Changed older bytes'),record(page=2,rev=3)])
        docs[-1]['license'][0]['url']='unreviewed'
        docs.extend([record(page=3,rev=3),record(page=4,rev=3)])
        stage(self.root/'stage.sqlite',docs);db=sqlite3.connect(self.root/'stage.sqlite')
        bad=b'{malformed';db.execute('UPDATE records SET original_zlib=?,raw_bytes=?,raw_sha256=? WHERE sequence=73',(zlib.compress(bad),len(bad),c.sha(bad)))
        db.execute("UPDATE records SET title='wrong staged identity' WHERE sequence=74");db.commit();db.close()
        result=p.run(args(self.root,len(docs)));db=sqlite3.connect(self.root/'out/index.sqlite')
        self.assertEqual(db.execute('select count(*) from dispositions').fetchone()[0],75)
        self.assertEqual(db.execute('select count(*) from articles where page<=4').fetchone()[0],0)
        self.assertEqual(db.execute('select count(*) from blocked').fetchone()[0],4)
        self.assertFalse(result['source_admission_established']);self.assertFalse(result['whole_original_identity_matched']);db.close()
    def test_reserve_and_long_external_controls(self):
        stage(self.root/'stage.sqlite',[record()]);g=p.Guard(30,time.time()+60,self.root,free=lambda _:p.RESERVE-1)
        with self.assertRaises(p.Stopped):p.run(args(self.root,1),g)
        s=json.loads((self.root/'out/status.json').read_text());self.assertEqual(s['status'],'STOPPED_RETAINED')
        for mutate in [{'memory.max':'max'},{'memory.swap.max':'1'},{'cpu.max':'500000 100000'},{'pids.max':'33'}]:
            x={'memory.max':'536870912','memory.swap.max':'0','cpu.max':'100000 100000','pids.max':'32'};x.update(mutate)
            with self.assertRaises(ValueError):p.verify_long_limits(x)
    def test_deadlines_all_phases(self):
        for phase in ['parse','index','fts_integrity','sqlite_integrity','hash']:
            root=self.root/phase;root.mkdir();stage(root/'stage.sqlite',[record(page=i+1,text='Literal source '*600)for i in range(6)])
            class Expiring(p.Guard):
                def check(self,write=False):
                    hit=(self.phase==phase) or (phase=='parse' and self.phase=='ingest' and isinstance(c.Projection,type) and self.calls>8)
                    self.calls+=1
                    if hit and self.calls>10:self.deadline=time.monotonic()-1
                    super().check(write)
            g=Expiring(30,time.time()+60,root);g.calls=0
            with self.assertRaises((p.Stopped,sqlite3.OperationalError)):p.run(args(root,6),g)
            s=json.loads((root/'out/status.json').read_text());self.assertEqual(s['status'],'STOPPED_RETAINED');self.assertFalse(s['source_admission_established'])
    def test_sqlite_progress_and_hash_chunk_cutoff(self):
        # Expire inside SQLite progress and after one hash chunk, not phase entry.
        for phase in ['index','fts_integrity','sqlite_integrity']:
            root=self.root/phase;root.mkdir();stage(root/'stage.sqlite',[record(page=i+1,text='Literal source '*600) for i in range(500)])
            class ProgressExpiry(p.Guard):
                def progress(self):
                    if self.phase==phase:
                        self.hits+=1;self.deadline=time.monotonic()-1
                    return super().progress()
            g=ProgressExpiry(30,time.time()+60,root);g.hits=0
            with self.assertRaises((p.Stopped,sqlite3.OperationalError)):p.run(args(root,500),g)
            self.assertGreater(g.hits,0)
            self.assertFalse(json.loads((root/'out/status.json').read_text())['resume_ingest_allowed'])
            with self.assertRaises(ValueError):p.run(args(root,500,True))
        path=self.root/'bounded-hash.bin';path.write_bytes(b'x'*(2*1024*1024))
        class HashExpiry(p.Guard):
            def check(self,write=False):
                self.calls+=1
                if self.calls==2:self.deadline=time.monotonic()-1
                super().check(write)
        g=HashExpiry(30,time.time()+60,self.root);g.calls=0
        with self.assertRaises(p.Stopped):p.hash_file(path,g)
        self.assertEqual(g.calls,2)
    def test_oversized_and_mutated_snapshot(self):
        stage(self.root/'stage.sqlite',[record()]);db=sqlite3.connect(self.root/'stage.sqlite');db.execute('CREATE TABLE oversized(sequence INTEGER,member TEXT,member_offset INTEGER,raw_bytes INTEGER,raw_sha256 TEXT)');db.execute("INSERT INTO oversized VALUES(1,'constructed',10,17000000,'retained-unverified')");db.commit();db.close()
        result=p.run(args(self.root,2));self.assertEqual(result['dispositions']['oversized_unverified'],1);self.assertFalse(result['complete_original_coverage_not_rights'])
        other=self.root/'changed';other.mkdir();stage(other/'stage.sqlite',[record()])
        class Change(p.Guard):
            def check(self,write=False):
                if self.phase=='coverage' and not self.changed:
                    db=sqlite3.connect(other/'stage.sqlite');db.execute("UPDATE records SET original_zlib=x'00' WHERE sequence=0");db.commit();db.close();self.changed=True
                super().check(write)
        g=Change(30,time.time()+60,other);g.changed=False
        with self.assertRaises(ValueError):p.run(args(other,1),g)
        self.assertEqual(json.loads((other/'out/status.json').read_text())['status'],'STOPPED_RETAINED')
    def test_source_wal_not_pinned(self):
        stage(self.root/'stage.sqlite',[record()]);g=guard(self.root);batch=p.read_batch(self.root/'stage.sqlite',0,0,g)
        db=sqlite3.connect(self.root/'stage.sqlite');observations=[]
        for i in range(1,6):
            append(db,i,record(page=i+1));db.commit();r=db.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone();observations.append(r);self.assertEqual(r[0],0)
        db.close();self.assertEqual(batch[0][0],0)
        (self.root/'wal-observations.json').write_text(json.dumps(observations))
    def test_original_independent_roundtrip(self):
        d=record(text='Before 😀 &amp; after.',lic='CC-BY-SA-4.0');stage(self.root/'stage.sqlite',[d]);p.run(args(self.root,1))
        db=sqlite3.connect(self.root/'out/index.sqlite');blob=db.execute('select payload from articles').fetchone()[0];db.close();cap=c.unpack_capsule(c.inflate(blob,c.CAPSULE_MAX));found=p.original_for_capsule(self.root/'stage.sqlite',cap)
        self.assertEqual(hashlib.sha256(found['raw']).hexdigest(),cap['identity']['raw_sha256'])
        raw=json.loads(found['raw']);source=raw['article_body']['html'].encode('utf-16-le');rendered=cap['text'].encode('utf-16-le')
        for a,b,x,y,kind in cap['mapping']:
            left=source[x*2:y*2].decode('utf-16-le');right=rendered[a*2:b*2].decode('utf-16-le')
            if kind=='literal':self.assertEqual(left,right)
            elif kind=='entity':self.assertEqual(html.unescape(left),right)
            else:self.assertEqual(right,'\n')
        self.assertEqual(raw['license'],cap['metadata']['license']);self.assertEqual(raw['date_modified'],cap['metadata']['date_modified'])
        db=sqlite3.connect(self.root/'stage.sqlite');db.execute("update records set raw_sha256='changed'");db.commit();db.close()
        with self.assertRaises(ValueError):p.original_for_capsule(self.root/'stage.sqlite',cap)
    def test_no_complete_promotion(self):
        a={'status':'identity_verified','bytes':140267048582,'md5':'2276dbb8db3bc93eabc90a505117e373','sha256':'a'*64}
        s={'status':'raw_stage_complete','source_bytes':a['bytes'],'source_md5':a['md5'],'source_sha256':a['sha256'],'records_received':3}
        self.assertTrue(p.ready_identity(a,s,3))
        for bad in [{**a,'status':'downloading'},{**a,'bytes':1},{**a,'sha256':'b'*64}]:self.assertFalse(p.ready_identity(bad,s,3))
        self.assertFalse(p.ready_identity(a,s,2))
    def test_concurrent_resume_ownership(self):
        stage(self.root/'stage.sqlite',[record()]);out=self.root/'out';out.mkdir()
        (out/'status.json').write_text('{"status":"RUNNING","phase":"ingest"}')
        before=(out/'status.json').read_bytes()
        with (out/'.producer.lock').open('wb') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.assertRaisesRegex(ValueError,'already active'):p.run(args(self.root,1,True))
        self.assertEqual((out/'status.json').read_bytes(),before)
        self.assertFalse((out/'index.sqlite').exists())
    def test_manual_resume_boundary(self):
        stage(self.root/'stage.sqlite',[record(page=i+1)for i in range(70)])
        class StopSecond(p.Guard):
            def check(self,write=False):
                if self.phase=='ingest' and (self.root/'out/index.sqlite').exists():
                    db=sqlite3.connect(self.root/'out/index.sqlite')
                    try:
                        if db.execute("select 1 from sqlite_master where name='progress'").fetchone() and db.execute('select last_sequence from progress').fetchone()[0]>=63:self.reason='controlled interruption after committed batch'
                    finally:db.close()
                super().check(write)
        with self.assertRaises(p.Stopped):p.run(args(self.root,70),StopSecond(30,time.time()+60,self.root))
        self.assertEqual(json.loads((self.root/'out/status.json').read_text())['committed_through'],63)
        result=p.run(args(self.root,70,True));self.assertEqual(result['counts']['dispositions'],70);self.assertEqual(result['counts']['articles'],70)
if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Cases);result=unittest.TextTestRunner(verbosity=2).run(suite)
    (BASE/('controls-'+str(time.time_ns())+'.json')).write_text(json.dumps({'success':result.wasSuccessful(),'tests':RESULTS},indent=2)+'\n');sys.exit(0 if result.wasSuccessful() else 1)
