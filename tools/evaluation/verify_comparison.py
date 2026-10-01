#!/usr/bin/env python3
"""Validate preserved real measurements and mutation-test comparison contracts."""
from pathlib import Path
import copy, hashlib, json, math, re, sys
ROOT=Path(__file__).resolve().parents[2]
PROTOCOL_SHA='1c8b1439e40457bf9c141653d7f72fcbb552805a8269e4f64ff8e95861694510'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def make_blind(report):
    # Opaque per-answer labels; identity mapping is shipped separately, never to reviewers.
    rows=sorted(report['rows'],key=lambda r:hashlib.sha256(('comparison-v1:'+r['id']+r['system']).encode()).hexdigest())
    packet={'version':1,'instructions':'Rate each response for correctness, claim support, completeness, uncertainty and citation usability (1-5 or unrateable). Quote unsupported claims. Compare answers within each question only. Do not infer speed from length. No ratings supplied by builder. System names and timing are withheld; wording may reveal extractive style.','items':[]};key={}
    for i,r in enumerate(rows):
        label=f'R{i+1:03d}';key[label]={'id':r['id'],'system':r['system']}
        packet['items'].append({'label':label,'question':r['question'],'response':r['text'],'sources':r['sources'],'ratings':None})
    return packet,key

def validate_rows(report,spec):
    rows=report['rows'];expected={(c['id'],s):c['question'] for c in spec['cases'] for s in spec['systems']}
    assert len(rows)==len(expected)
    assert {(r['id'],r['system']):r['question'] for r in rows}==expected
    assert [(r['id'],r['system']) for r in rows]==[(c['id'], 'pocketlore' if (i+j)%2==0 else 'extractive') for i,c in enumerate(spec['cases']) for j in range(2)]
    assert report['runtime'].startswith('llama.cpp bb4caa7540188872173c44d161602d9271386413')
    assert report['system_prompt'] and report['model_load_ms']>0 and report['pack_load_ms']>0
    for c in spec['cases']:
        pair=[r for r in rows if r['id']==c['id']];assert pair[0]['sources']==pair[1]['sources']
    for r in rows:
        assert r['text'] and isinstance(r['raw_draft'],str) and isinstance(r['prompt'],str)
        for field in ['retrieval_ms','end_to_end_ms','first_token_ms']:
            assert isinstance(r[field],(int,float)) and math.isfinite(r[field]) and r[field]>=0
        assert r['end_to_end_ms']>=r['retrieval_ms']
        ids={s['id'] for s in r['sources']}
        for s in r['sources']:assert all(s.get(k) for k in ['id','text','url','date','license','title'])
        if r['system']=='extractive':assert r['kind']=='EXTRACTIVE' and r['tokens']==0 and not r['raw_draft']
        else:
            assert r['kind'] in ['GENERATED','FALLBACK','ABSTAINED']
            if r['tokens']>0:assert r['raw_draft'] and r['prompt']
            if r['kind']=='GENERATED':
                cited=set(re.findall(r'\[([^\[\]]+)\]',r['text']));assert cited and cited<=ids
    assert any(r['system']=='pocketlore' and r['tokens']>0 for r in rows), 'No actual model generation recorded'

def validate(path):
    spec=json.loads((path/'protocol.json').read_text());manifest=json.loads((path/'manifest.json').read_text());report=json.loads((path/'results.json').read_text())
    assert digest(path/'protocol.json')==PROTOCOL_SHA==manifest['protocol_sha256']
    assert digest(path/'results.json')==manifest['results_sha256']
    assert manifest['model_sha256']==spec['model_sha256'] and manifest['pack_sha256']==spec['pack_sha256']
    assert manifest['environment']['abi']=='x86_64' and manifest['environment']['airplane_mode']=='1'
    validate_rows(report,spec)
    packet,key=make_blind(report)
    assert json.loads((path/'blind.json').read_text())==packet
    assert json.loads((path/'identity-key.json').read_text())==key
    # Negative tests ensure altered questions, unmatched sources, invalid timing,
    # absent real generation and fabricated citation identifiers fail the contract.
    for mutation in ['question','sources','timing','generation','citation']:
        bad=copy.deepcopy(report)
        if mutation=='question':bad['rows'][0]['question']+=' altered'
        elif mutation=='sources':bad['rows'][0]['sources']=[]
        elif mutation=='timing':bad['rows'][0]['end_to_end_ms']=-1
        elif mutation=='generation':
            for r in bad['rows']:
                if r['system']=='pocketlore':r.update(tokens=0,kind='ABSTAINED',raw_draft='')
        else:
            r=next(r for r in bad['rows'] if r['system']=='pocketlore');r.update(kind='GENERATED',text='[fabricated-source] Unsupported claim.')
        try:validate_rows(bad,spec)
        except AssertionError:pass
        else:raise AssertionError('Mutation escaped: '+mutation)
    return report
if __name__=='__main__':
    path=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'docs/evidence/comparison/run-v1'
    report=validate(path)
    print('PASS: exact protocol, paired real records, provenance, timing, blind packet and five rejected mutations')
    print('This verifies measurement integrity, not answer quality, independence or competitive superiority.')
