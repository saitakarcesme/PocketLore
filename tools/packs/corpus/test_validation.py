"""Mutation tests using real staged records; no fabricated corpus coverage."""
import copy, json, pathlib, shutil, tempfile, unittest, re
from acquire import digest, normalized, limits, save
from validate import validate

STAGE=None
class CorruptionTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(); self.stage=pathlib.Path(self.temp.name)
  for name in ('selection-v1.json','freeze.json'):
   shutil.copyfile(STAGE/name,self.stage/name)
  with (STAGE/'sources.jsonl').open() as f: self.doc=json.loads(next(f))
  self.parts=[]
  with (STAGE/'chunks.jsonl').open() as f:
   for line in f:
    c=json.loads(line)
    if c['document_id']==self.doc['id']: self.parts.append(c)
  self.write()
 def tearDown(self): self.temp.cleanup()
 def write(self, docs=None, parts=None):
  docs=docs if docs is not None else [self.doc]; parts=parts if parts is not None else self.parts
  for name,rows in [('sources.jsonl',docs),('chunks.jsonl',parts)]:
   (self.stage/name).write_text(''.join(json.dumps(r)+'\n' for r in rows))
  (self.stage/'receipts.jsonl').write_text('')
  (self.stage/'counts.json').write_text(json.dumps({'documents':len(docs),'chunks':len(parts),'area_documents':{self.doc['area']:len(docs)}}))
 def reject(self, pattern):
  with self.assertRaisesRegex(ValueError,pattern): validate(self.stage,False)
 def test_valid_real_subset(self): self.assertEqual(validate(self.stage,False)['documents'],1)
 def test_missing_rights(self):
  del self.doc['license_url']; self.write(); self.reject('Missing rights')
 def test_missing_attribution(self):
  del self.doc['history_url']; self.write(); self.reject('Missing rights')
 def test_back_matter(self):
  text=self.doc['text']; words=list(re.finditer(r'\S+',text)); c=self.parts[-1]; c['start_char']=words[-80].start(); c['end_char']=len(text); c['text']=text[c['start_char']:]; c['text_sha256']=digest(c['text']); c['normalized_text_sha256']=digest(normalized(c['text'])); self.write(); self.reject('Back matter counted')
 def test_curated_topic(self):
  self.doc['id']='9823717'; self.write(); self.reject('Curated topic exclusion')
 def test_unlicensed_dataset(self):
  p=self.stage/'selection-v1.json'; r=json.loads(p.read_text()); r['dataset']='unknown/unlicensed'; p.write_text(json.dumps(r))
  from acquire import filehash
  f=self.stage/'freeze.json'; v=json.loads(f.read_text()); v['selection_sha256']=filehash(p); f.write_text(json.dumps(v))
  self.reject('Unsupported dataset rights basis')
 def test_false_history(self):
  self.doc['history_url']+='bad'; self.write(); self.reject('Attribution identity mismatch')
 def test_duplicate_document(self):
  self.write(docs=[self.doc,self.doc]); self.reject('Duplicate document')
 def test_duplicate_chunk(self):
  self.write(parts=self.parts+[self.parts[-1]]); self.reject('Overlapping|Duplicate chunk')
 def test_corrupt_text(self):
  self.parts[0]['text']+=' changed'; self.write(); self.reject('Corrupt chunk')
 def test_corrupt_offset(self):
  self.parts[0]['start_char']+=1; self.write(); self.reject('Corrupt chunk')
 def test_wrong_topic(self):
  self.doc['area']='wrong'; self.write(); self.reject('Incorrect area')
 def test_invented_revision(self):
  self.doc['revision_id']='123'; self.write(); self.reject('Invented revision')
 def test_license_downgrade(self):
  self.doc['license']='CC0'; self.write(); self.reject('Unapproved license')
 def test_chunk_attribution_loss(self):
  del self.parts[0]['attribution']; self.write(); self.reject('Chunk provenance mismatch')
 def test_corrupt_source(self):
  self.doc['text']+='changed'; self.write(); self.reject('Corrupt source text')

if __name__=='__main__':
 import sys
 STAGE=pathlib.Path(sys.argv.pop(1)); limits(); result=unittest.main(exit=False).result
 save(STAGE/'tests.json',{'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'success':result.wasSuccessful()})
 sys.exit(0 if result.wasSuccessful() else 1)
