import unittest,importlib.util
from pathlib import Path
P=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('extract',P/'extract.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
RAW=P.parents[3]/'downloads/broad-reference/html-v2'
class FidelityTests(unittest.TestCase):
 def source(self,ident):return m.extract((RAW/(ident+'.html')).read_text())
 def test_real_absolute_value_math(self):
  d=self.source('991');t=d['blocks'][0]['text'];self.assertIn('[TeX: {\\displaystyle |0|=0}]',t);self.assertIn('absolute value of 3 is 3',t);self.assertGreater(d['math_representations'],50)
 def test_real_algae_unit(self):
  d=self.source('633');self.assertIn('50 metres (160 ft)',d['blocks'][0]['text'])
 def test_main_body_not_small_template(self):self.assertGreater(len(self.source('358')['blocks']),30)
 def test_missing_math_rejected(self):
  with self.assertRaisesRegex(ValueError,'Math element'):m.extract('<div class="mw-parser-output"><p>'+('A'*100)+'<span class="mwe-math-element"><img src="x"></span></p></div>')
 def test_quoted_block_excluded(self):
  d=m.extract('<div class="mw-parser-output"><p>'+('"quoted prose" '*20)+'</p><blockquote><p>'+('B'*120)+'</p></blockquote></div>');self.assertEqual(d['blocks'],[]);self.assertEqual(len(d['excluded']),1)
 def test_references_and_notice_links(self):
  d=m.extract('<div class="mw-parser-output"><p>This article incorporates text from a free content work. <a href="https://example.invalid/license">CC BY 4.0</a>.</p><ol><li id="cite_note-1"><a href="https://example.invalid/source">Reference</a></li></ol></div>');self.assertEqual(d['references'][0]['links'],['https://example.invalid/source']);self.assertTrue(d['attribution_notices'][0]['links'])
if __name__=='__main__':unittest.main()
