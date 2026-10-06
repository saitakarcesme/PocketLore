#!/usr/bin/env python3
"""Offline actual-original reconstruction and compact reader acceptance, not admission."""
from pathlib import Path
import ast,base64,collections,hashlib,json,os,resource,sqlite3,sys,tempfile,time,zlib
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/packs/complete-source'))
import compact as c
E=R/'docs/evidence/complete-source-producer'
LICENSE_PINS={'CC-BY-SA-3.0.txt':'3f941b3b89cf7b8370ceb83cc76d2120d471b58735d8ca60238a751a48d7f72f','CC-BY-SA-4.0.txt':'28a9529c7d0bb4dc51f4bf5c116a3d16ef247a052f7591466768ddf563fd1cf5'}
def inspect_license(path,digest):c.require(c.file_sha(path)==digest,'missing/changed full license bytes')
def inspect_samples(path):
    packet=json.loads(path.read_text())
    c.require(packet['sequences']==[0,251,502,753,1004,1255,30000,100000,200000],'sample selection changed')
    for row in packet['samples']:
        raw=c.inflate(base64.b64decode(row['original_zlib_base64'],validate=True),c.RAW_MAX)
        cap=c.transform(raw,row['identity']);c.require(c.sha(c.pack_capsule(cap))==row['transformation']['capsule_sha256'],'packet reconstruction mismatch')
    return len(packet['samples'])
def main():
    for name,digest in LICENSE_PINS.items():inspect_license(E/name,digest)
    count=inspect_samples(E/'original-samples.json')
    with tempfile.TemporaryDirectory() as temp:
        legal=Path(temp)/'license.txt';legal.write_bytes((E/'CC-BY-SA-4.0.txt').read_bytes()+b'changed')
        try:inspect_license(legal,LICENSE_PINS['CC-BY-SA-4.0.txt'])
        except ValueError:pass
        else:raise AssertionError('changed license accepted')
        legal.unlink()
        try:inspect_license(legal,LICENSE_PINS['CC-BY-SA-4.0.txt'])
        except FileNotFoundError:pass
        else:raise AssertionError('missing license accepted')
        p=Path(temp)/'samples.json';d=json.loads((E/'original-samples.json').read_text());d['samples'][0]['identity']['raw_sha256']='0'*64;p.write_text(json.dumps(d))
        try:inspect_samples(p)
        except ValueError:pass
        else:raise AssertionError('changed original accepted')
        p.unlink()
        try:inspect_samples(p)
        except FileNotFoundError:pass
        else:raise AssertionError('missing source packet accepted')
    print('PASS original packet reconstruction/missing/changed controls',count)
    contract=json.loads((E/'runs.json').read_text());reports=[]
    for entry in contract['runs']:
        path=R/entry['path'];receipt=json.loads((path/'receipt.json').read_text())
        c.require(c.file_sha(path/'receipt.json')==entry['receipt_sha256'],'changed receipt')
        c.require(c.file_sha(path/'executed-compact.py')==receipt['source_code_sha256'],'executed source mismatch')
        def producer_tree(p):
            tree=ast.parse(p.read_text());tree.body=[n for n in tree.body if not (isinstance(n,ast.ClassDef) and n.name=='Reader')];return ast.dump(tree)
        c.require(producer_tree(path/'executed-compact.py')==producer_tree(R/'tools/packs/complete-source/compact.py'),'producer changed since actual run')
        start=time.monotonic();reader=c.Reader(path);opening=time.monotonic()-start
        src=sqlite3.connect('file:'+receipt['source_stage']+'?mode=ro',uri=True);src.execute('PRAGMA cache_size=-8192')
        chain=hashlib.sha256();seen=0
        for full in c.staged_rows(src,receipt['sequence_ceiling']):
            row=full[:5]
            c.require(row[0]==seen,'source sequence gap');seen+=1;chain.update(c.canonical(row)+b'\n')
        c.require(chain.hexdigest()==receipt['original_chain_sha256'],'source identity chain')
        c.require(seen==reader.db.execute('SELECT count(*) FROM dispositions').fetchone()[0],'disposition omission')
        c.require(reader.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite posting/source integrity')
        total=reader.db.execute('SELECT count(*) FROM articles').fetchone()[0];c.require(total>5000,'actual articles must exceed old ceiling')
        c.require(receipt['rss_max_kib']<128*1024,'bounded producer RSS')
        c.require(total==reader.db.execute('SELECT count(DISTINCT page) FROM articles').fetchone()[0],'duplicate article inflation')
        c.require(reader.db.execute("SELECT count(*) FROM sqlite_master WHERE name='search_content' AND type='view'").fetchone()[0]==1,'body duplication architecture')
        # Fixed sequence modular sample, not title/topic or query-selected success samples.
        rows=reader.db.execute('SELECT page,sequence FROM articles WHERE sequence % 251=0 ORDER BY sequence').fetchall()
        samples=[];queries=[]
        for page,seq in rows:
            cap=reader.article(page);row=src.execute('SELECT member,member_offset,raw_bytes,raw_sha256,original_zlib FROM records WHERE sequence=?',(seq,)).fetchone()
            raw=c.inflate(row[4],c.RAW_MAX);c.require(len(raw)==row[2] and c.sha(raw)==row[3],'original sample corruption')
            ident={'sequence':seq,'member':row[0],'member_offset':row[1],'raw_bytes':row[2],'raw_sha256':row[3]}
            reconstructed=c.transform(raw,ident);c.require(c.canonical(reconstructed)==c.canonical(cap),'exact capsule reconstruction')
            for a,b,h in reader.db.execute('SELECT start16,end16,sha256 FROM passages WHERE page=?',(page,)):
                c.require(c.sha(c.slice16(cap['text'],a,b).encode())==h,'exact quote mismatch')
            samples.append({'sequence':seq,'page':page,'revision':cap['metadata']['version']['identifier'],'license':cap['metadata']['license'],'raw_sha256':row[3],'html_sha256':cap['html_sha256'],'mapping_segments':len(cap['mapping'])})
            # Engineering token-retrieval check, not a development answer question or relevance score.
            if len(queries)<8:
                import re
                tokens=re.findall(r'[A-Za-z]{4,}',cap['metadata']['name'])[:2]
                if tokens:
                    q=' '.join(tokens);t=time.monotonic();hits=reader.search(q);queries.append({'query':q,'seconds':time.monotonic()-t,'hits':hits})
        try:reader.search('source',lambda:True)
        except ValueError:pass
        else:raise AssertionError('cancellation ignored')
        c.require(not reader.search('zzzznonexistentfixturetoken'),'absent token search')
        c.require(reader.search('Perry_Robinson')==reader.search('Perry Robinson'),'underscore normalization changed results')
        reader.search('COVID_19')
        try:reader.search('x'*4097)
        except ValueError:pass
        else:raise AssertionError('unbounded query accepted')
        reports.append({'path':str(path.relative_to(R)),'article_count':total,'opening_seconds':opening,'samples':samples,'queries':queries,'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'source_admission_established':False})
        reader.db.close();src.close()
    mixed=[]
    for sequence in [30000,100000,200000]:
        src=sqlite3.connect('file:'+receipt['source_stage']+'?mode=ro',uri=True)
        row=src.execute('SELECT member,member_offset,raw_bytes,raw_sha256,original_zlib FROM records WHERE sequence=?',(sequence,)).fetchone();src.close()
        raw=c.inflate(row[4],c.RAW_MAX);ident={'sequence':sequence,'member':row[0],'member_offset':row[1],'raw_bytes':row[2],'raw_sha256':row[3]}
        cap=c.transform(raw,ident);c.require(cap['metadata']['license'][0]['identifier']=='CC-BY-SA-4.0','actual4.0 control');mixed.append({'identity':ident,'license':cap['metadata']['license']})
    c.require(reports[-1]['article_count']>reports[0]['article_count'],'growing actual distinct records required')
    c.require(max(r['max_rss_kib'] for r in reports)<256*1024,'bounded reader memory')
    out=R/'downloads/complete-source-producer'/('verification-'+str(time.time_ns())+'.json')
    out.write_bytes(c.canonical({'status':'PASS_ENGINEERING_ONLY','reports':reports,'actual4_license_samples':mixed})+b'\n');print(out);print('PASS complete-source engineering; corpus admission remains false')
if __name__=='__main__':main()
