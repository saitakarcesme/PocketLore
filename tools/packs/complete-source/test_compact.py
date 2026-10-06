"""Constructed algorithm controls, never counted as factual corpus coverage."""
import copy, hashlib, json, sqlite3, tempfile, unittest, zlib
from pathlib import Path
import compact as c

def record(page=1,rev=2,text='A literal source 😀 &amp; exact condition.',lic='CC-BY-SA-3.0'):
    return {'identifier':page,'version':{'identifier':rev},'name':'Constructed algorithm fixture','url':'https://en.wikipedia.org/wiki/Fixture','date_modified':'2025-03-20T00:00:00Z','namespace':{'identifier':0},'in_language':{'identifier':'en'},'license':[{'identifier':lic,'url':c.LICENSES[lic]}],'article_body':{'html':f'<html about="https://en.wikipedia.org/wiki/Special:Redirect/revision/{rev}"><head><meta property="mw:pageId" content="{page}"/></head><body><h2>Heading</h2><p>{text}</p></body></html>'}}
def capsule(d):
    b=c.canonical(d);return c.transform(b,{'raw_sha256':c.sha(b),'sequence':0,'member':'fixture','member_offset':0,'raw_bytes':len(b)})
class Controls(unittest.TestCase):
    def test_mixed_rights(self):
        for lic in c.LICENSES:self.assertEqual(capsule(record(lic=lic))['metadata']['license'][0]['identifier'],lic)
        for rows in [[],[{'identifier':'CC-BY-SA-4.0','url':c.LICENSES['CC-BY-SA-3.0']}],[{'identifier':'unknown','url':'x'}],record()['license']*2]:
            d=record();d['license']=rows
            with self.assertRaises(ValueError):capsule(d)
    def test_mapping_and_digest(self):
        x=capsule(record());self.assertIn('😀 & exact',x['text']);c.validate_capsule(x)
        y=copy.deepcopy(x);y['mapping'][1][2]+=1
        with self.assertRaises(ValueError):c.validate_capsule(y)
        y=copy.deepcopy(x);y['text']+='forged'
        with self.assertRaises(ValueError):c.validate_capsule(y)
        with self.assertRaises(ValueError):c.transform(c.canonical(record()),{'raw_sha256':'0'*64})
    def test_unsafe_and_complete(self):
        for t in ['<math><semantics><mi>x</mi><annotation encoding="application/x-tex">\\sqrt[5]{100}</annotation></semantics></math>','<table><tr><td>value</td></tr></table>','<alien>unknown</alien>','Copyright another owner','<script>secret</script>','<blockquote>quoted</blockquote>']:
            x=capsule(record(text=t));self.assertTrue(x['dispositions']);self.assertIn(t,x['html'])
        x=capsule(record(text='Before <sup>2</sup> after'));self.assertTrue(x['dispositions'])
    def test_bounds(self):
        with self.assertRaises(ValueError):c.inflate(zlib.compress(b'x'*100),99)
        with self.assertRaises(ValueError):c.inflate(zlib.compress(b'ok')[:-1],99)
        with self.assertRaises(ValueError):c.inflate(zlib.compress(b'ok')+b'extra',99)
        d=record();d['article_body']['html']='x'*(c.HTML_MAX+1)
        with self.assertRaises(ValueError):capsule(d)
    def test_revision_choice(self):
        db=sqlite3.connect(':memory:');db.executescript(c.SCHEMA)
        self.assertEqual(c.choose(db,1,2,'2025','a',0),'latest')
        self.assertEqual(c.choose(db,1,2,'2025','a',1),'duplicate or older revision')
        self.assertEqual(c.choose(db,1,1,'2026','b',2),'duplicate or older revision')
        self.assertEqual(c.choose(db,1,3,'2025','c',3),'latest')
        self.assertEqual(c.choose(db,1,3,'2025','d',4),'conflicting same revision')
        self.assertEqual(db.execute('select conflict from latest').fetchone()[0],1)
    def test_passage_reconstruction(self):
        text='😀 literal source condition. '*200;spans=c.passages(text)
        self.assertEqual(''.join(c.slice16(text,a,b) for a,b,h in spans),text)
        for a,b,h in spans:self.assertEqual(c.sha(c.slice16(text,a,b).encode()),h)
    def test_posting_integrity(self):
        db=sqlite3.connect(':memory:');db.create_function('capsule_text',1,lambda b:json.loads(c.inflate(b,c.CAPSULE_MAX))['text']);db.executescript(c.SCHEMA)
        x=capsule(record());blob=zlib.compress(c.canonical(x))
        db.execute('INSERT INTO articles VALUES(?,?,?,?,?,?,?,?,?)',(1,2,0,'Fixture','CC-BY-SA-3.0','raw','cap',blob,0))
        db.execute('INSERT INTO search(docid,title,body) VALUES(1,?,?)',('Fixture',x['text']))
        self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
        db.execute("UPDATE articles SET title='Changed' WHERE page=1")
        self.assertNotEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
    def test_partial_denied(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'receipt.json').write_text(json.dumps({'status':'ENGINEERING_COMPLETE_PROVISIONAL','source_admission_established':True}))
            with self.assertRaises(ValueError):c.Reader(p)
if __name__=='__main__':unittest.main()
