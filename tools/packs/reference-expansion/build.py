#!/usr/bin/env python3
"""Build only explicitly source-reviewed paragraphs; no automatic rights promotion."""
import json, hashlib, zipfile
from pathlib import Path
from prepare import ROOT, HERE, sha, units
PACKET=ROOT/'downloads/reference-expansion/source-packet.json'
REVIEW=ROOT/'docs/evidence/reference-coverage-expansion/source-review.json'
LICENSE=ROOT/'downloads/general-research/acquisition/CC-BY-SA-4.0.txt'
LICENSE_SHA='28a9529c7d0bb4dc51f4bf5c116a3d16ef247a052f7591466768ddf563fd1cf5'

def build(output, packet_path=PACKET, review_path=REVIEW):
    packet=json.loads(packet_path.read_text()); review=json.loads(review_path.read_text())
    assert packet['selection_sha256']==sha((HERE/'selection.json').read_bytes())
    assert review['packet_sha256']==sha(packet_path.read_bytes()),'Review belongs to another source packet'
    legal=LICENSE.read_bytes();assert sha(legal)==LICENSE_SHA,'Missing/changed legal bytes'
    documents=[];rows=[];coverage=[];identities=set();texts=set()
    for source in packet['documents']:
        raw=(ROOT/source['html_path']).read_bytes()
        assert sha(raw)==source['html_sha256']
        assert sha((ROOT/source['metadata_path']).read_bytes())==source['metadata_sha256']
        decision=review['documents'][str(source['page_id'])]
        if decision['decision']!='admit-selected-spans':continue
        allowed=decision['admitted_span_sha256'];assert allowed and len(set(allowed))==len(allowed)
        selected=[s for s in source['spans'] if s['sha256'] in allowed]
        assert len(selected)==len(allowed) and all(s in source['spans'][:3] for s in selected),'Review scope exceeds bounded edition'
        did='reference-'+str(source['page_id']);url=source['revision_url']
        assert source['page_id'] not in identities;identities.add(source['page_id'])
        body='\n\n'.join(s['text'] for s in selected);assert units(body)<=16000
        attribution='Wikipedia contributors; '+source['title']+'; '+url+'; contributor history '+source['contributors_url']
        notices=decision.get('attribution_notices',[])
        notice_text='; '.join(n if isinstance(n,str) else n['text'] for n in notices)
        if notice_text:attribution+='; '+notice_text
        assert len(attribution)<=2048,'Attribution exceeds product metadata bound; do not truncate'
        rights='CC BY-SA 4.0; selected transformed text distributed on the same terms; no added restrictions'
        d=dict(id=did,title=source['title'],url=url,source_date='Revision '+str(source['revision'])+' at '+source['revision_date'],retrieved_date=source['source_receipt']['utc'][:10],attribution=attribution,license=rights,license_url='https://creativecommons.org/licenses/by-sa/4.0/',license_id='cc-by-sa-4',language='en',category=source['family'],raw_sha256=source['html_sha256'],source_identity=url+'#sha256='+source['html_sha256'],source_text=body,source_text_sha256=sha(body.encode()),source_text_format='selected complete paragraphs transformed from original HTML; exact original HTML ranges retained in source packet',rights_basis='Independent per-source selected-span inspection; source HTML including footer, exact revision and contributor link retained',rights_disposition=decision['limitations'],rights_status='admit-selected-spans',rights_review_sha256=sha(review_path.read_bytes()),passages=[])
        offset=0
        for s in selected:
            text=s['text'];digest=sha(text.encode());assert digest==s['sha256'] and digest not in texts,'Duplicate passage';texts.add(digest)
            assert '\n' not in text and '\t' not in text
            a,b=s['html_utf8_start'],s['html_utf8_end'];assert sha(raw[a:b])==s['original_paragraph_sha256']
            utf16=raw.decode().encode('utf-16-le');assert utf16[s['html_utf16_start']*2:s['html_utf16_end']*2].decode('utf-16-le')==raw[a:b].decode()
            citation=did+'-'+digest[:16]
            d['passages'].append(dict(id=citation,sha256=digest,source_utf16_start=offset,source_utf16_end=offset+units(text),source_span_sha256=digest));offset+=units(text)+2
            rows.append('\t'.join([citation,d['title'],url,d['source_date']+'; retrieved '+d['retrieved_date'],attribution+'; '+rights+'; '+d['license_url'],text]))
        documents.append(d);coverage.append(dict(page_id=source['page_id'],family=source['family'],title=source['title'],revision=source['revision'],original_sha256=source['html_sha256'],selected_paragraphs=len(selected),span_sha256=allowed))
    assert len(documents)>=100,'Fewer than 100 admitted distinct documents'
    assert len({d['category'] for d in documents})>=20,'Fewer than20 admitted subject families'
    payload=('\n'.join(rows)+'\n').encode()
    m=dict(schema=2,id='reference-expansion-2026-10-02-v1',language='en',transformation=packet['transformation'],warning='Bounded selected reference paragraphs; dated source excerpts, not generated answers, current advice or corpus-wide rights clearance.',source_packet_sha256=sha(packet_path.read_bytes()),licenses={'cc-by-sa-4':dict(url='https://creativecommons.org/licenses/by-sa/4.0/',sha256=LICENSE_SHA,text=legal.decode())},documents=documents,passages_sha256=sha(payload),passage_count=len(rows))
    encoded=(json.dumps(m,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode();assert len(encoded)<=2*1024*1024
    output=Path(output);output.parent.mkdir(exist_ok=True,parents=True)
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_STORED) as z:
        for name,data in [('manifest.json',encoded),('passages.tsv',payload)]:
            info=zipfile.ZipInfo(name,(2026,10,2,0,0,0));info.external_attr=0o100644<<16;z.writestr(info,data)
    assert output.stat().st_size<=16*1024*1024
    inventory=dict(edition=m['id'],pack_sha256=sha(output.read_bytes()),pack_bytes=output.stat().st_size,manifest_bytes=len(encoded),distinct_documents=len(documents),subject_families=len({d['category'] for d in documents}),passages=len(rows),documents=coverage,installed_status='Not established by pack construction; requires fresh device receipt',packaged_fallback='Existing bundled pack unchanged; not counted as active coverage',source_packet_sha256=sha(packet_path.read_bytes()),source_review_sha256=sha(review_path.read_bytes()),license_sha256=LICENSE_SHA)
    (output.parent/'coverage.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n')
    return m

if __name__=='__main__':
    p=ROOT/'downloads/reference-expansion/reference-expansion.plpack';m=build(p)
    print(json.dumps({'pack_sha256':sha(p.read_bytes()),'documents':len(m['documents']),'paragraphs':m['passage_count'],'bytes':p.stat().st_size}))
