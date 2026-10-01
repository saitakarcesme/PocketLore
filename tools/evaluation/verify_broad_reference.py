#!/usr/bin/env python3
"""Verify real edition bytes/rows and pinned Android behavior; no semantic clearance implied."""
from pathlib import Path
import collections, copy, hashlib, json, math, sqlite3, tempfile, unicodedata, zipfile
ROOT = Path(__file__).resolve().parents[2]
E = ROOT / 'docs/evidence/broad-reference'
PACK = ROOT / 'downloads/broad-reference/v1/broad-reference.plpack'
DB = ROOT / 'downloads/broad-reference/v1/index.sqlite'
PROTOCOL = ROOT / 'tools/evaluation/broad-reference/protocol.json'
MODEL_SHA = '74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db'
LEGAL_SHA = '170b3685f24d098f590c92867787e7be3a86260aed1b96bf4a7594f72a9116be'
def sha(path):
    with path.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def digest(data): return hashlib.sha256(data).hexdigest()
def normalized(text): return ' '.join(unicodedata.normalize('NFKC', text).casefold().split())
def require(ok, message):
    if not ok: raise ValueError(message)
def manifest_check(m):
    require(m.get('license') == 'CC-BY-SA-4.0', 'Missing or changed license')
    require(m.get('distribution_ready') is False, 'Unreviewed distribution must stay blocked')
    require(m.get('format') == 'pocketlore-sqlite-v1', 'Wrong schema version')
    require(m.get('documents', 0) >= 1000 and m.get('passages', 0) >= 10000, 'Frozen count targets unmet')
    require(len(m.get('areas', {})) == 8 and min(m['areas'].values()) >= 50, 'Heuristic area count target unmet')
def check_hash(path, expected): require(sha(path) == expected, 'Changed artifact: ' + str(path))
def negative(fn, name):
    try: fn()
    except (ValueError, FileNotFoundError): return name
    raise ValueError('Negative regression did not reject: ' + name)
def main():
    receipt = json.loads((E/'run/receipt.json').read_text())
    for name, h in receipt['records'].items(): check_hash(E/'run'/name, h)
    for name, h in receipt['sources'].items(): check_hash(ROOT/name, h)
    check_hash(PROTOCOL, receipt['protocol_sha256'])
    check_hash(PACK, receipt['pack']['sha256'])
    check_hash(ROOT/'android/app/build/outputs/apk/debug/app-debug.apk', receipt['apk']['sha256'])
    with zipfile.ZipFile(PACK) as z:
        require(set(z.namelist()) == {'manifest.json','index.sqlite','CC-BY-SA-4.0.html'}, 'Unexpected archive entries')
        m = json.loads(z.read('manifest.json')); manifest_check(m)
        require(digest(z.read('index.sqlite')) == m['db_sha256'], 'Archive database mismatch')
        require(digest(z.read('CC-BY-SA-4.0.html')) == LEGAL_SHA, 'Missing or changed legal text')
    check_hash(DB, m['db_sha256'])
    con = sqlite3.connect('file:' + str(DB) + '?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    # Independent row/content checks, not merely accepting producer-reported counts.
    areas = collections.Counter(); docs = {}; unique = set()
    for d in con.execute('SELECT * FROM documents'):
        require(digest(d['body'].encode()) == d['sha'], 'Source body hash')
        n = digest(normalized(d['body']).encode()); require(n not in unique, 'Duplicate real document'); unique.add(n)
        require(all(v in d['rights'] for v in ['CC BY-SA 4.0','Wikipedia contributors','share adaptations alike']), 'Document rights')
        require(all(v in d['provenance'] for v in ['Contributor history:','Dataset revision:','Upstream shard SHA-256:','Source SHA-256:','Modifications:','Generation disabled:']), 'Document provenance')
        require('2023-11-01' in d['date'] and 'unknown' in d['date'], 'Source date misrepresented')
        docs[d['id']] = dict(d); areas[d['area']] += 1
    require(len(docs) == m['documents'] and dict(areas) == m['areas'], 'Actual document/area counts')
    count = 0; seen = set()
    for p in con.execute('SELECT * FROM passages'):
        d = docs[p['document']]; count += 1
        require(digest(p['body'].encode()) == p['sha'], 'Passage hash')
        nh = digest(normalized(p['body']).encode()); require(nh == p['normalized_sha'] and nh not in seen, 'Duplicate passage'); seen.add(nh)
        require(d['body'].encode('utf-16-le')[p['start']*2:p['end']*2].decode('utf-16-le') == p['body'], 'Passage not genuine source substring')
        require(p['citation'] == 'wiki-' + d['id'] + '-' + p['sha'][:16], 'Unstable citation')
    require(count == m['passages'], 'Actual passage count')
    require(con.execute('SELECT count(*) FROM search').fetchone()[0] == count, 'Missing search rows')
    require(con.execute('SELECT count(*) FROM search s JOIN passages p ON s.docid=p.pid JOIN documents d ON p.document=d.id WHERE s.body != p.body OR s.title != d.title').fetchone()[0] == 0, 'Index content divergence')
    frozen = json.loads(PROTOCOL.read_text()); prefix = 'p'+receipt['pack']['sha256']+'_'
    runs = {}; summaries = {}
    for mode in ['import','restart']:
        r = json.loads((E/'run'/(mode+'.json')).read_text()); runs[mode] = r
        require(r['status']=='PASS' and (r['collections'],r['documents'],r['passages'])==(3,1094,26870), 'Android catalog/counts')
        require(r['saved_model_before']==r['saved_model_after']==MODEL_SHA and r['stages']==0, 'Rollback/model/staging')
        require(r['after_open']['java_used']-r['before_open']['java_used'] < 32*1024*1024, 'Opening heap exceeds bound')
        require(r['offline_license_visible'] and 'Creative Commons' in r['license_visible_text'] and 'offline license' in r['license_visible_text'], 'Offline license UI')
        require(len(r['dialogs'])==8 and all('Contributor history:' in d['visible'] and d['citation'].startswith(prefix) and 'Generation disabled:' in d['visible'] for d in r['dialogs']), 'Source dialog provenance')
        require(len(r['queries']) == len(frozen['queries']) == 40, 'Incomplete query run')
        found=0; misses=[]; absent_small_hits=0; timings=[]
        for q, actual in zip(frozen['queries'], r['queries']):
            require((q['id'],q['question']) == (actual['id'],actual['question']), 'Frozen question changed')
            require(len(actual['hits'])<=4 and actual['ms']>=0, 'Unbounded/invalid query')
            timings.append(actual['ms']); retrieved=set(); broad=[]
            for h in actual['hits']:
                if not h['id'].startswith(prefix): continue
                broad.append(h); row=con.execute('SELECT p.*,d.title,d.url,d.date,d.rights,d.sha AS source_sha FROM passages p JOIN documents d ON p.document=d.id WHERE p.citation=?',(h['id'][len(prefix):],)).fetchone()
                require(row is not None, 'Unknown edition citation')
                require(all(h[k]==row[v] for k,v in [('title','title'),('text','body'),('url','url'),('date','date'),('rights','rights')]), 'Hit not exact saved source')
                require(row['sha'] in h['provenance'] and row['source_sha'] in h['provenance'], 'Hit source/passage hash missing')
                retrieved.add(row['document'])
            if q['kind']=='absent':
                require(not broad and actual['controller_route']=='ABSTAINED', 'Absent control leaked broad evidence/answer')
                absent_small_hits += bool(actual['hits'])
            else:
                require(docs[q['expected_document']]['sha']==q['source_sha256'] and q['support_excerpt'] in docs[q['expected_document']]['body'], 'Frozen supporting source changed')
                if q['expected_document'] in retrieved: found+=1
                else: misses.append(q['id'])
                require(actual['controller_route']!='GENERATED', 'Unsafe broad generation')
        timings.sort()
        summaries[mode]={'expected_document_top4':found,'supported_queries':32,'misses':misses,'absent_with_small_pack_hits':absent_small_hits,'broad_absent_empty':8,'retrieval_p50_ms':timings[math.ceil(.5*len(timings))-1],'retrieval_p95_ms':timings[math.ceil(.95*len(timings))-1]}
    require(runs['import']['pid'] != runs['restart']['pid'], 'No process restart')
    require('Index SHA-256 mismatch' in runs['import']['corrupt_index_failure'] and 'cancel' in runs['import']['cancel_status'].lower(), 'Missing real corruption/cancellation behavior')
    full = json.loads((E/'failures/android-20261001T074000532651Z/import.json').read_text())
    require(full['import_ms']>0 and full['collections']==3 and full['passages']==26870, 'No real full import measurement')
    repro=json.loads((ROOT/'downloads/broad-reference/repro/build.json').read_text())
    require(repro['pack_sha256']==receipt['pack']['sha256'] and repro['db_sha256']==m['db_sha256'], 'Reproduction differs')
    check_hash(ROOT/'downloads/broad-reference/repro/broad-reference.plpack',receipt['pack']['sha256'])
    negatives=[]; missing=copy.deepcopy(m); missing.pop('license')
    negatives.append(negative(lambda:manifest_check(missing),'missing-license'))
    with tempfile.TemporaryDirectory(prefix='pocketlore-broad-check-') as tmp:
        p=Path(tmp)/'changed'; p.write_bytes((E/'run/restart.json').read_bytes()+b' ')
        negatives.append(negative(lambda:check_hash(p,receipt['records']['restart.json']),'changed-behavior-artifact'))
        negatives.append(negative(lambda:check_hash(Path(tmp)/'missing',receipt['pack']['sha256']),'missing-pack-artifact'))
    print(json.dumps({'status':'PASS','meaning':'Artifact integrity, bounded emulator behavior and measured retrieval only; semantic breadth, source-specific rights and generated usefulness remain open','documents':len(docs),'unique_passages':count,'areas_heuristic':dict(areas),'retrieval':summaries,'negative_regressions':negatives},indent=2))
if __name__=='__main__': main()
