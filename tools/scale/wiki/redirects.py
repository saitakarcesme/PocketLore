#!/usr/bin/env python3
"""Primary bulk SQL/title-index aliases with identity-checked direct targets."""
import argparse,bz2,collections,gzip,json,pathlib,resource,sqlite3,time
from acquire import atomic

def sql_tuple(line):
    """Parse MySQL dump VALUES strings without executing SQL from a source file."""
    out=[];field=[];quote=False;escape=False
    for c in line.strip()[1:]:
        if escape:field.append({'n':'\n','r':'\r','t':'\t','0':'\0','Z':'\x1a'}.get(c,c));escape=False
        elif quote and c=='\\':escape=True
        elif c=="'":quote=not quote
        elif not quote and c in ',)':
            out.append(''.join(field));field=[]
            if c==')':return out
        else:field.append(c)
    raise ValueError('Unterminated SQL tuple')

def run(lane):
    start=time.monotonic();out=lane/'redirects-staging.sqlite';db=sqlite3.connect(out);db.executescript('PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL; PRAGMA cache_size=-262144; PRAGMA temp_store=FILE; CREATE TABLE IF NOT EXISTS pages(id INTEGER PRIMARY KEY,title TEXT NOT NULL); CREATE TABLE IF NOT EXISTS redirects(id INTEGER PRIMARY KEY,target_title TEXT NOT NULL,fragment TEXT NOT NULL); CREATE TABLE IF NOT EXISTS progress(key TEXT PRIMARY KEY,value INTEGER NOT NULL);');counts=collections.Counter()
    if not db.execute("SELECT 1 FROM progress WHERE key='pages'").fetchone():
        db.execute('BEGIN')
        with bz2.open(lane/'bulk/enwiki-20260901-pages-articles-multistream-index.txt.bz2','rt') as f:
            for line in f:
                offset,ident,title=line.rstrip('\n').split(':',2);db.execute('INSERT OR IGNORE INTO pages VALUES (?,?)',(int(ident),title));counts['index_lines']+=1
        db.execute('CREATE INDEX IF NOT EXISTS pages_title ON pages(title)');db.execute('INSERT INTO progress VALUES (?,?)',('pages',counts['index_lines']));db.commit();print('Title index complete',counts['index_lines'],flush=True)
    if not db.execute("SELECT 1 FROM progress WHERE key='redirects'").fetchone():
        db.execute('BEGIN')
        with gzip.open(lane/'bulk/enwiki-20260901-redirect.sql.gz','rt') as f:
            for line in f:
                if not line.startswith('('):continue
                row=sql_tuple(line);counts['redirect_rows']+=1
                if len(row)!=5:raise ValueError('Unexpected redirect schema')
                ident,namespace,title,interwiki,fragment=row
                if namespace=='0' and not interwiki:db.execute('INSERT INTO redirects VALUES (?,?,?)',(int(ident),title.replace('_',' '),fragment))
        db.execute('INSERT INTO progress VALUES (?,?)',('redirects',counts['redirect_rows']));db.commit();print('Redirect table complete',counts['redirect_rows'],flush=True)
    db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    result={'snapshot':'20260901','title_index_rows':db.execute('SELECT count(*) FROM pages').fetchone()[0],'main_target_redirect_rows':db.execute('SELECT count(*) FROM redirects').fetchone()[0],'seconds':time.monotonic()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'limitations':'Snapshot newer than FineWiki. Final aliases require exact current target ID and stored FineWiki title agreement; unresolved chains are not guessed.'};atomic(lane/'redirects-staging.json',result);db.close();print(json.dumps(result),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('lane');a=p.parse_args();run(pathlib.Path(a.lane))
