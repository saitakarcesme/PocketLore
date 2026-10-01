#!/usr/bin/env python3
"""Deterministic source-block extraction; math is copied from source TeX, never reconstructed."""
from html.parser import HTMLParser
from pathlib import Path
import re,json,hashlib,sqlite3,collections
class Node:
 def __init__(self,tag='',attrs=(),parent=None):self.tag=tag;self.a=dict(attrs);self.parent=parent;self.children=[]
 def walk(self):
  yield self
  for child in self.children:
   if isinstance(child,Node):yield from child.walk()
 def raw(self):return ''.join(c.raw() if isinstance(c,Node) else c for c in self.children)
class Parser(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.root=Node();self.stack=[self.root]
 def handle_starttag(self,tag,attrs):
  n=Node(tag,attrs,self.stack[-1]);self.stack[-1].children.append(n)
  if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:self.stack.append(n)
 def handle_endtag(self,tag):
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i].tag==tag:self.stack=self.stack[:i];break
 def handle_data(self,data):self.stack[-1].children.append(data)
def text(n):
 if not isinstance(n,Node):return n
 if n.tag in {'script','style','img','figure','svg','audio','video'} or 'mw-editsection' in n.a.get('class',''):return ''
 if 'mwe-math-element' in n.a.get('class',''):
  for d in n.walk():
   if d.tag=='math' and d.a.get('alttext'):return ' [TeX: '+d.a['alttext']+'] '
   if d.tag=='annotation' and d.a.get('encoding')=='application/x-tex':return ' [TeX: '+d.raw()+'] '
  raise ValueError('Math element has no textual representation')
 if n.tag=='math':
  if n.a.get('alttext'):return ' [TeX: '+n.a['alttext']+'] '
  raise ValueError('Unrepresented standalone math')
 s=''.join(text(c) for c in n.children)
 if n.tag=='sup' and 'reference' not in n.a.get('class',''):return '^('+s+')'
 if n.tag=='sub':return '_('+s+')'
 return s

def extract(html):
 p=Parser();p.feed(html);roots=[n for n in p.root.walk() if 'mw-parser-output' in n.a.get('class','').split()]
 if not roots:raise ValueError('Article body absent')
 root=max(roots,key=lambda n:len(n.raw()));blocks=[];excluded=[];references=[];notices=[];section='Lead';math=0
 for n in root.walk():
  if n.tag in {'h2','h3','h4'}:section=' '.join(text(n).split())
  if n.tag not in {'p','li','div'}:continue
  raw=' '.join(n.raw().split())
  if re.search(r'this article (?:incorporates|contains) (?:public domain|text)|copyright permission|used with permission|creative commons attribution',raw,re.I) and len(raw)<4000:notices.append({'text':raw,'links':list(dict.fromkeys(d.a['href'] for d in n.walk() if d.tag=='a' and d.a.get('href','').startswith(('http:','https:','//'))))})
  if n.tag=='li' and n.a.get('id','').startswith('cite_note'):
   references.append({'text':' '.join(text(n).split()),'links':list(dict.fromkeys(d.a['href'] for d in n.walk() if d.tag=='a' and d.a.get('href','').startswith(('http:','https:','//'))))});continue
  if n.tag!='p':continue
  ancestors=[];a=n.parent
  while a and a!=root:ancestors.append(a);a=a.parent
  if any(a.tag in {'table','figure','blockquote','nav','li'} or any(x in a.a.get('class','') for x in ['navbox','reflist','sidebar','hatnote','infobox','ambox']) for a in ancestors):continue
  s=' '.join(text(n).split())
  if len(s)<100:continue
  if any(q in s for q in ['"','“','”','«','»']) or any(d.tag in {'q','blockquote'} for d in n.walk()):
   excluded.append({'sha256':hashlib.sha256(s.encode()).hexdigest(),'reason':'Quoted prose excluded; no third-party quotation license inferred'});continue
  if section in {'References','External links','Notes','Further reading','See also'}:continue
  blocks.append({'section':section,'text':s});math+=s.count('[TeX:')
 notices=[n for n in notices if not any(o['text']!=n['text'] and o['text'] in n['text'] for o in notices)]
 return {'blocks':blocks,'references':references,'attribution_notices':list({json.dumps(x,sort_keys=True):x for x in notices}.values()),'excluded':excluded,'math_representations':math}
if __name__=='__main__':
 root=Path(__file__).resolve().parents[4];stage=root/'downloads/broad-reference/html-v2';out=stage/'extracted';out.mkdir(exist_ok=True);db=sqlite3.connect(root/'downloads/broad-reference/v1/index.sqlite');summary=[]
 records=list(db.execute('select id,title,area from documents order by rowid'))
 if (stage/'extra-index.json').exists():records += [(r['id'],r['title'],r['area']) for r in json.loads((stage/'extra-index.json').read_text()) if 'id' in r]
 for ident,title,area in records:
  src=stage/(ident+'.html');meta=stage/(ident+'.json')
  if not src.exists():continue
  try:
   data=extract(src.read_text());page=next(iter(json.loads(meta.read_text())['query']['pages'].values()));data.update({'id':ident,'title':page['title'],'original_area':area,'revision':page['revisions'][0],'html_sha256':hashlib.sha256(src.read_bytes()).hexdigest()});(out/(ident+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');summary.append({'id':ident,'title':title,'area':area,'blocks':len(data['blocks']),'math':data['math_representations'],'notices':len(data['attribution_notices']),'excluded':len(data['excluded'])})
  except Exception as e:summary.append({'id':ident,'title':title,'error':str(e)})
 (stage/'extraction-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('Processed',len(summary),'documents; blocks',sum(x.get('blocks',0) for x in summary))
