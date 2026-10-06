#!/usr/bin/env python3
"""Offline actual-original reconstruction and compact reader acceptance, not admission."""
from pathlib import Path
import collections,hashlib,json,os,resource,sqlite3,sys,time,zlib
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/packs/complete-source'))
import compact as c
E=R/'docs/evidence/complete-source-producer'
def main():
    contract=json.loads((E/'runs.json').read_text());reports=[]
    for entry in contract['runs']:
        path=R/entry['path'];receipt=json.loads((path/'receipt.json').read_text())
        c.require(c.file_sha(path/'receipt.json')==entry['receipt_sha256'],'changed receipt')
        c.require(c.file_sha(path/'executed-compact.py')==receipt['source_code_sha256'],'executed source mismatch')
        start=time.monotonic();reader=c.Reader(path);opening=time.monotonic()-start
        src=sqlite3.connect('file:'+receipt['source_stage']+'?mode=ro',uri=True);src.execute('PRAGMA cache_size=-8192')
        chain=hashlib.sha256();seen=0
        for row in src.execute('SELECT sequence,member,member_offset,raw_bytes,raw_sha256 FROM records WHERE sequence<=? ORDER BY sequence',(receipt['sequence_ceiling'],)):
            c.require(row[0]==seen,'source sequence gap');seen+=1;chain.update(c.canonical(row)+b'\n')
        c.require(chain.hexdigest()==receipt['original_chain_sha256'],'source identity chain')
        c.require(seen==reader.db.execute('SELECT count(*) FROM dispositions').fetchone()[0],'disposition omission')
        c.require(reader.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite posting/source integrity')
        total=reader.db.execute('SELECT count(*) FROM articles').fetchone()[0];c.require(total>5000,'actual articles must exceed old ceiling')
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
        reports.append({'path':str(path.relative_to(R)),'article_count':total,'opening_seconds':opening,'samples':samples,'queries':queries,'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'source_admission_established':False})
        reader.db.close();src.close()
    c.require(reports[-1]['article_count']>reports[0]['article_count'],'growing actual distinct records required')
    c.require(max(r['max_rss_kib'] for r in reports)<256*1024,'bounded reader memory')
    out=R/'downloads/complete-source-producer'/('verification-'+str(time.time_ns())+'.json')
    out.write_bytes(c.canonical({'status':'PASS_ENGINEERING_ONLY','reports':reports})+b'\n');print(out);print('PASS complete-source engineering; corpus admission remains false')
if __name__=='__main__':main()
