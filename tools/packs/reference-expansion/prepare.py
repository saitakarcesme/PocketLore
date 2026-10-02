#!/usr/bin/env python3
"""Re-extract frozen source bytes without network access or corpus-wide rights approval."""
import hashlib, importlib.util, json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location('reference_html', ROOT/'tools/packs/broad/repair/extract.py')
html = importlib.util.module_from_spec(spec); spec.loader.exec_module(html)

def sha(data): return hashlib.sha256(data).hexdigest()
def units(s): return len(s.encode('utf-16-le'))//2

class LocatedParser(html.Parser):
    def __init__(self, source):
        super().__init__(); self.source=source
        self.lines=[0]
        for m in re.finditer('\n',source): self.lines.append(m.end())
    def position(self):
        line,col=self.getpos(); return self.lines[line-1]+col
    def handle_starttag(self,tag,attrs):
        at=self.position(); parent=self.stack[-1]
        super().handle_starttag(tag,attrs)
        n=parent.children[-1]; n.start=at
    def handle_endtag(self,tag):
        for n in reversed(self.stack):
            if n.tag==tag:
                n.end=self.source.index('>',self.position())+1; break
        super().handle_endtag(tag)

def prepare():
    selection=json.loads((HERE/'selection.json').read_text())
    receipts=[json.loads(x) for x in (ROOT/'downloads/broad-reference/html-v2/receipts.jsonl').read_text().splitlines()]
    docs=[]
    for row in selection['candidates']:
        data=(ROOT/row['html_path']).read_bytes(); meta=(ROOT/row['metadata_path']).read_bytes()
        assert sha(data)==row['html_sha256'] and sha(meta)==row['metadata_sha256']
        matches=[r for r in receipts if r['sha256']==sha(data) and r['status']==200]
        assert matches, 'Missing original acquisition receipt: '+row['title']
        source=data.decode('utf-8',errors='strict'); p=LocatedParser(source);p.feed(source)
        extracted=html.extract(source)
        roots=[n for n in p.root.walk() if 'mw-parser-output' in n.a.get('class','').split()]
        root=max(roots,key=lambda n:len(n.raw()))
        warnings=[]
        for n in root.walk():
            if 'ambox' in n.a.get('class','').split():
                warnings.append(' '.join(n.raw().split()))
        footer=[n for n in p.root.walk() if n.a.get('id')=='footer-info-copyright']
        assert len(footer)==1 and 'Creative Commons Attribution-ShareAlike' in footer[0].raw(),row['title']
        assert str(row['revision']) in source and str(row['page_id']) in source
        # Reuse the reviewed transformation, while pinning the *original HTML* range
        # independently of the transformed source-text range; these are not interchangeable.
        located={}
        for n in root.walk():
            if n.tag=='p' and hasattr(n,'end'):
                text=' '.join(html.text(n).split());located.setdefault(text,[]).append(n)
        selected=[]; exclusions=list(extracted['excluded']); total=0
        for block in extracted['blocks']:
            text=block['text']
            if text.endswith(':') or units(text)>3000:
                exclusions.append({'sha256':sha(text.encode()),'reason':'Dependent lead-in or paragraph exceeds bounded selection size'});continue
            if len(selected)>=8 or total+units(text)>16000:break
            nodes=located.get(text,[])
            if len(nodes)!=1:
                exclusions.append({'sha256':sha(text.encode()),'reason':'Ambiguous original paragraph mapping'});continue
            node=nodes[0]; raw=source[node.start:node.end]
            selected.append(dict(text=text,section=block['section'],sha256=sha(text.encode()),html_utf16_start=units(source[:node.start]),html_utf16_end=units(source[:node.end]),html_utf8_start=len(source[:node.start].encode()),html_utf8_end=len(source[:node.end].encode()),original_paragraph_sha256=sha(raw.encode())))
            total+=units(text)
        body='\n\n'.join(x['text'] for x in selected);offset=0
        for s in selected:
            s['source_utf16_start']=offset;s['source_utf16_end']=offset+units(s['text']);offset=s['source_utf16_end']+2
        docs.append(dict(**row,source_text=body,source_text_sha256=sha(body.encode()),spans=selected,source_receipt=matches[0],rights_footer=' '.join(footer[0].raw().split()),attribution_notices=extracted['attribution_notices'],warnings=warnings,exclusions=exclusions,contributors_url='https://en.wikipedia.org/w/index.php?curid='+str(row['page_id'])+'&action=history',revision_url='https://en.wikipedia.org/w/index.php?oldid='+str(row['revision']),decision='pending independent source review'))
    return dict(schema=1,selection_sha256=sha((HERE/'selection.json').read_bytes()),extractor_sha256=sha(Path(__file__).read_bytes()),upstream_extractor_sha256=sha((ROOT/'tools/packs/broad/repair/extract.py').read_bytes()),transformation='Complete paragraphs only; decode HTML entities, remove markup/media, normalize whitespace, copy source TeX and mark super/subscripts; preserve original UTF8/UTF16 HTML ranges separately from transformed text offsets; no builder-written factual text.',documents=docs)

if __name__=='__main__':
    out=ROOT/'downloads/reference-expansion';out.mkdir(exist_ok=True)
    packet=prepare();path=out/'source-packet.json';path.write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'path':str(path),'sha256':sha(path.read_bytes()),'documents':len(packet['documents']),'paragraphs':sum(len(x['spans']) for x in packet['documents']),'warning_documents':sum(bool(x['warnings']) for x in packet['documents']),'rights':'PENDING'}))
