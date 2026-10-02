#!/usr/bin/env python3
"""Reproduce a bounded historical Markdown edition from immutable primary bytes."""
import argparse,hashlib,json,re,urllib.request,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
LOCK=Path(__file__).with_name('sources.lock.json')
CACHE=ROOT/'downloads/specialist/raw'
def sha(b):return hashlib.sha256(b).hexdigest()
def build(output,download=False,cache=CACHE):
 lock=json.loads(LOCK.read_text());docs=[];rows=[];cache.mkdir(parents=True,exist_ok=True)
 for item in lock['documents']:
  def fetch(path,digest):
   local=cache/(item['repo']+'-'+path.replace('/','_'));url='https://raw.githubusercontent.com/ethereum/'+item['repo']+'/'+item['revision']+'/'+path
   if not local.exists() and download:
    with urllib.request.urlopen(url,timeout=30) as r:raw=r.read(1000001)
    if len(raw)>1000000 or sha(raw)!=digest:raise ValueError('Unpinned source: '+url)
    local.write_bytes(raw)
   raw=local.read_bytes()
   if sha(raw)!=digest:raise ValueError('Changed source: '+str(local))
   return raw
  raw=fetch(item['path'],item['raw_sha256']);license=fetch('LICENSE.md',item['license_sha256']).decode();text=raw.decode('utf-8');assert 'CC0 1.0 Universal' in license
  assert '\r' not in text and '\u2028' not in text and '\u2409' not in text
  url='https://github.com/ethereum/'+item['repo']+'/blob/'+item['revision']+'/'+item['path']
  d=dict(id=item['id'],title=item['id'].upper()+': '+item['title'],url=url,source_date='Created '+item['created']+'; status '+item['status']+' at repository revision '+item['revision_date'],retrieved_date=lock['acquired'],attribution=item['author'],license='CC0-1.0; dated specification, not a current network assertion',license_url='https://github.com/ethereum/'+item['repo']+'/blob/'+item['revision']+'/LICENSE.md',license_text=license,language='en',category='Ethereum cryptography and technical interfaces',raw_sha256=item['raw_sha256'],rights_basis=item['rights_basis'],rights_disposition=item['rights_disposition'],passages=[])
  # Keep every character, including complete formulas, code, tables and status header.
  # The TSV container needs reversible visible replacements for LF and TAB only.
  boundaries=[0]+[m.start() for m in re.finditer(r'^#{1,2} ',text,re.M) if m.start()>0]+[len(text)]
  for start,end in zip(boundaries,boundaries[1:]):
   rawspan=text[start:end];span=rawspan.replace('\n','\u2028').replace('\t','\u2409');digest=sha(span.encode());citation=d['id']+'-'+digest[:16]
   assert 0<len(span)<=20000
   d['passages'].append(dict(id=citation,sha256=digest,source_utf16_start=len(text[:start].encode('utf-16-le'))//2,source_utf16_end=len(text[:end].encode('utf-16-le'))//2,source_span_sha256=sha(rawspan.encode())))
   rows.append('\t'.join([citation,d['title'],url,d['source_date']+'; retrieved '+d['retrieved_date'],d['attribution']+'; '+d['license']+'; '+d['license_url'],span]))
  docs.append(d)
 payload=('\n'.join(rows)+'\n').encode();manifest=dict(schema=1,id=lock['edition'],language='en',transformation='Exact Markdown sections; LF represented as U+2028 and TAB as U+2409, reversibly; no linked media or referenced documents fetched.',warning='Historical specification snapshots. Status and network parameters may change. Markdown formulas/code are literal, not executed. Linked references are not included. No generated-answer qualification.',documents=docs,passages_sha256=sha(payload),passage_count=len(rows))
 output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_STORED) as z:
  for name,data in [('manifest.json',(json.dumps(manifest,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()),('passages.tsv',payload)]:
   info=zipfile.ZipInfo(name,(2026,10,2,0,0,0));info.external_attr=0o100644<<16;z.writestr(info,data)
 return manifest
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--download',action='store_true');p.add_argument('--output',default=str(ROOT/'downloads/specialist/ethereum-technical.plpack'));a=p.parse_args();m=build(a.output,a.download);print(json.dumps({'bytes':Path(a.output).stat().st_size,'sha256':sha(Path(a.output).read_bytes()),'documents':len(m['documents']),'passages':m['passage_count']}))
