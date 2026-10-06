"""CC0 authored inputs and expectations, independent of the adapter implementation."""
import bz2,hashlib,json,pathlib
HEADER=b'<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.11/" version="0.11"><siteinfo><dbname>syntheticwiki</dbname></siteinfo>'
END=b'</mediawiki>'
TEXT='If A & B, 😀 e\u0301 remains.\r\n{| class="wikitable"\n! Unit !! Value\n| m || 2\n|}\n<math>x²</math><ref>Attribution</ref>{{Template|a=1}} otherwise no.'
LEXICAL=TEXT.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').encode()
def revision(rid=11,text=LEXICAL,model='wikitext'):
 return b'<revision><id>'+str(rid).encode()+b'</id><timestamp>2026-10-01T00:00:00Z</timestamp><contributor><username>CC0 Author</username><id>7</id></contributor><model>'+model.encode()+b'</model><format>text/x-wiki</format>'+ (b'<text xml:space="preserve">'+text+b'</text>' if text is not None else b'')+b'<sha1>publisher-unverified</sha1></revision>'
def page(pid=1,title='../../hostile &amp; title',revs=None):
 return b'<page><title>'+title.encode()+b'</title><ns>0</ns><id>'+str(pid).encode()+b'</id><redirect title="Elsewhere"/>'+(revs if revs is not None else revision())+b'</page>'
def create(out):
 out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=False)
 valid=HEADER+page(revs=revision()+revision(12,b'<![CDATA[Literal <x> & entity]]>'))+page(2,'Missing',revision(21,None))+page(3,'Other',revision(31,b'{}','json'))+page()+END
 cut=valid.index('😀'.encode())+1
 cases={'valid':bz2.compress(valid),'multistream':bz2.compress(valid[:cut])+bz2.compress(valid[cut:]),'conflict':bz2.compress(HEADER+page()+page(title='Changed')+END),'doctype':bz2.compress(b'<!DOCTYPE mediawiki [<!ENTITY x SYSTEM "file:///never-read">]>'+HEADER+page()+END),'malformed':bz2.compress(HEADER+page()+b'</wrong>'),'truncated':bz2.compress(valid)[:-7],'trailing-truncated-member':bz2.compress(valid)+bz2.compress(b'junk')[:-7],'namespace':bz2.compress(valid.replace(b'export-0.11/',b'export-0.10/')),'oversized':bz2.compress(HEADER+page(revs=revision(text=b'a'*(2097152+1)))+END),'bomb':bz2.compress(HEADER+page(revs=revision(text=b'z'*100000))+END),'deep':bz2.compress(HEADER+b'<a>'*40+b'</a>'*40+END),'missing-id':bz2.compress(HEADER+page().replace(b'<id>1</id>',b'<id>0</id>')+END)}
 cases.update({'nested-id':bz2.compress(HEADER+page().replace(b'<id>1</id>',b'<id><id>1</id></id>')+END),'duplicate-contributor':bz2.compress(HEADER+page().replace(b'</username>',b'</username><username>Changed</username>')+END),'duplicate-redirect':bz2.compress(HEADER+page().replace(b'<redirect title="Elsewhere"/>',b'<redirect title="Elsewhere"/><redirect title="Changed"/>')+END)})
 for name,b in cases.items():(out/(name+'.bz2')).write_bytes(b)
 oracle={'license':'CC0-1.0','text':TEXT,'text_utf8_sha256':hashlib.sha256(TEXT.encode()).hexdigest(),'text_utf16_length':len(TEXT.encode('utf-16-le'))//2,'emoji_utf16_range':[10,12],'records':4,'pages':4,'ledger':5,'queries':['😀','otherwise no.','Unit','../../hostile & title','absentliteral'],'files':{k:{'sha256':hashlib.sha256(v).hexdigest(),'bytes':len(v)} for k,v in cases.items()},'valid_xml_sha256':hashlib.sha256(valid).hexdigest(),'valid_lexical_sha256':hashlib.sha256(LEXICAL).hexdigest(),'valid_text_xml_range':[valid.index(LEXICAL),valid.index(LEXICAL)+len(LEXICAL)]}
 (out/'oracle.json').write_text(json.dumps(oracle,ensure_ascii=False,indent=2)+'\n')
 return oracle
if __name__=='__main__':
 import sys
 create(sys.argv[1])
