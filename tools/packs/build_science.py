#!/usr/bin/env python3
"""Build the separately versioned science edition from reviewed agency paragraphs."""
import argparse,json,urllib.request,zipfile
from pathlib import Path
from build_pack import ROOT,Blocks,sha
LOCK=Path(__file__).with_name('science-sources.lock.json')
CACHE=ROOT/'downloads/science/raw'
def build(download=False,output=None):
    lock=json.loads(LOCK.read_text());rows=[];docs=[];CACHE.mkdir(parents=True,exist_ok=True)
    for d in lock['documents']:
        p=CACHE/(d['cache_key']+'.html')
        if not p.exists():
            if not download:raise ValueError('Missing ignored source cache; run --download: '+str(p))
            with urllib.request.urlopen(urllib.request.Request(d['url'],headers={'User-Agent':'PocketLore source acquisition/1.0'}),timeout=45) as r:raw=r.read(4000001)
            p.write_bytes(raw)
        raw=p.read_bytes()
        if len(raw)>4000000 or sha(raw)!=d['raw_sha256']:raise ValueError('Raw snapshot changed; preserved cache needs reviewed acquisition: '+d['id'])
        parser=Blocks(d['selector']);parser.feed(raw.decode('utf-8'));blocks={sha(t.encode()):t for t in parser.blocks}
        doc={k:v for k,v in d.items() if k not in ['cache_key','selector','passages']};doc['passages']=[]
        for digest in d['passages']:
            if digest not in blocks:raise ValueError('Pinned paragraph missing: '+d['id'])
            citation=d['id']+'-'+digest[:16];doc['passages'].append({'id':citation,'sha256':digest})
            rows.append('\t'.join([citation,d['title'],d['url'],d['source_date']+'; retrieved '+d['retrieved_date'],d['attribution']+'; '+d['license']+'; '+d['license_url'],blocks[digest]]))
        docs.append(doc)
    payload=('\n'.join(rows)+'\n').encode()
    manifest={'schema':1,'id':lock['edition'],'language':'en','transformation':'Reviewed agency paragraphs; HTML removed and whitespace normalized. No synthetic factual text, images, captions or third-party media.','warning':'Dated introductory science excerpts, not current forecasts or medical advice. This separate edition replaces the active pack; it does not merge libraries.','documents':docs,'passages_sha256':sha(payload),'passage_count':len(rows)}
    output=Path(output or ROOT/'downloads/science/science-supplement-2026-10-01-v1.plpack');output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_STORED) as z:
        for name,data in [('manifest.json',(json.dumps(manifest,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()),('passages.tsv',payload)]:
            entry=zipfile.ZipInfo(name,(2026,10,1,0,0,0));entry.external_attr=0o100644<<16;z.writestr(entry,data)
    return output,manifest
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--download',action='store_true');p.add_argument('--output');a=p.parse_args();out,m=build(a.download,a.output);print(json.dumps({'path':str(out),'sha256':sha(out.read_bytes()),'bytes':out.stat().st_size,'documents':len(m['documents']),'passages':m['passage_count']},indent=2))
