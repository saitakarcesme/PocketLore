#!/usr/bin/env python3
"""Build an offline pack from reviewed, hash-pinned English source blocks."""
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / 'downloads/packs/raw'
LOCK = Path(__file__).with_name('sources.lock.json')
def sha(data): return hashlib.sha256(data).hexdigest()

class Blocks(HTMLParser):
    def __init__(self, mode='p'):
        super().__init__(); self.mode=mode; self.depth=0; self.parts=[]; self.blocks=[]
    def handle_starttag(self, tag, attrs):
        if self.depth:
            if tag == self.mode: self.depth += 1
            if tag in ('br', 'li'): self.parts.append(' ')
        elif tag == self.mode and (tag == 'p' or 'ArticleTextGroup' in dict(attrs).get('class','')):
            self.depth=1; self.parts=[]
    def handle_data(self, data):
        if self.depth: self.parts.append(data)
    def handle_endtag(self, tag):
        if tag == self.mode and self.depth:
            self.depth -= 1
            if not self.depth:
                text=' '.join(''.join(self.parts).split())
                if text: self.blocks.append(text)

def build(download=False, output=None):
    lock=json.loads(LOCK.read_text()); rows=[]; documents=[]
    CACHE.mkdir(parents=True,exist_ok=True)
    for source in lock['documents']:
        path=CACHE/(source['id']+'.html')
        if not path.exists():
            if not download: raise ValueError('Missing source cache; explicitly run --download: '+str(path))
            request=urllib.request.Request(source['url'],headers={'User-Agent':'PocketLore source acquisition/1.0'})
            with urllib.request.urlopen(request,timeout=60) as response: raw=response.read(4_000_001)
            if len(raw)>4_000_000: raise ValueError('Source exceeds limit')
            # Keep failed acquisitions for diagnosis; never accept a changed source silently.
            path.write_bytes(raw)
        raw=path.read_bytes()
        parser=Blocks(source['selector']); parser.feed(raw.decode('utf-8'))
        by_hash={sha(t.encode()):t for t in parser.blocks}
        doc={k:v for k,v in source.items() if k not in ('selector','passages')}
        doc['passages']=[]
        for digest in source['passages']:
            if digest not in by_hash: raise ValueError('Pinned source text changed: '+source['id']+' '+digest)
            text=by_hash[digest]; citation=source['id']+'-'+digest[:16]
            doc['passages'].append({'id':citation,'sha256':digest})
            rows.append('\t'.join([citation,source['title'],source['url'],source['source_date']+'; retrieved '+source['retrieved_date'],source['attribution']+'; '+source['license']+'; '+source['license_url'],text]))
        documents.append(doc)
    payload=('\n'.join(rows)+'\n').encode()
    manifest={'schema':1,'id':'english-reference-2026-10-01','language':'en','transformation':'Selected source text; HTML removed and whitespace normalized. No generated factual text.', 'warning':'Dated reference excerpts, not current conditions or complete safety guidance. Verify travel conditions before departure.', 'documents':documents,'passages_sha256':sha(payload),'passage_count':len(rows)}
    output=Path(output or ROOT/'downloads/packs/english-reference.plpack'); output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_STORED) as archive:
        for name,data in [('manifest.json',(json.dumps(manifest,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()),('passages.tsv',payload)]:
            entry=zipfile.ZipInfo(name,date_time=(2026,10,1,0,0,0));entry.external_attr=0o100644<<16;archive.writestr(entry,data)
    return output,manifest
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--download',action='store_true');p.add_argument('--output');a=p.parse_args()
    path,m=build(a.download,a.output); print(json.dumps({'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path.read_bytes()),'documents':len(m['documents']),'passages':m['passage_count']},indent=2))
