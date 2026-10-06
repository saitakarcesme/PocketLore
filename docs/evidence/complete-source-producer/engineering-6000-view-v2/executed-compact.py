#!/usr/bin/env python3
"""Provisional complete-original producer and bounded compact article reader.

This format intentionally has no source-admission or Android routing authority.
"""
import argparse, array, collections, datetime, hashlib, html, json, os, re
import resource, shutil, sqlite3, sys, time, zlib
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote

FORMAT = 'pocketlore-compact-article-v1'
RAW_MAX = 16_000_000
HTML_MAX = 4_000_000
TEXT_MAX = 4_000_000
SEG_MAX = 50_000
CAPSULE_MAX = 48_000_000
LICENSES = {'CC-BY-SA-3.0': 'https://creativecommons.org/licenses/by-sa/3.0/',
            'CC-BY-SA-4.0': 'https://creativecommons.org/licenses/by-sa/4.0/'}
NOTICE = re.compile(r'copyright|fair.use|permission|incorporat(?:es|ed|ing) (?:text|material)|public.domain|creative commons|licen[cs](?:ed|e|ing)', re.I)
VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
BLOCK = {'p','div','section','li','dt','dd','h1','h2','h3','h4','h5','h6','tr','table','blockquote','pre'}
KNOWN = BLOCK | VOID | {'html','head','body','title','span','a','b','i','strong','em','small','sup','sub','ul','ol','dl','tbody','thead','tfoot','td','th','caption','cite','abbr','time','code','s','u','del','ins','q','figure','figcaption','script','style','noscript','audio','video','svg','math','semantics','annotation','annotation-xml','mrow','mi','mn','mo','mtext','msup','msub','mfrac','msqrt','mroot','mstyle','mtable','mtr','mtd'}
SKIP = {'head','script','style','noscript','svg','audio','video','figure'}

def canonical(x): return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',',':')).encode()
def sha(b): return hashlib.sha256(b).hexdigest()
def file_sha(p):
    with open(p,'rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def u16(s): return len(s.encode('utf-16-le'))//2
def slice16(s,a,b): return s.encode('utf-16-le')[2*a:2*b].decode('utf-16-le')
def require(ok,msg):
    if not ok: raise ValueError(msg)
def atomic(p,x):
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_bytes(canonical(x)+b'\n');os.replace(tmp,p)
def inflate(b,limit):
    z=zlib.decompressobj();raw=z.decompress(b,limit+1)
    require(len(raw)<=limit and z.eof and not z.unconsumed_tail and not z.unused_data,'oversized or corrupt compressed payload')
    return raw

def exact_license(d):
    rows=d.get('license')
    require(isinstance(rows,list) and len(rows)==1 and isinstance(rows[0],dict),'unresolved license list')
    row=rows[0];require(row.get('identifier') in LICENSES,'unknown license identifier')
    require(row.get('url')==LICENSES[row['identifier']],'license URI mismatch')
    return row

class Projection(HTMLParser):
    """Lossless data-token projection with explicit synthetic separators and source ranges.

    Mathematical/table structures remain inspectable in original HTML, but deny
    research candidacy rather than flattening numeric meaning into claimed prose.
    """
    def __init__(self,source):
        super().__init__(convert_charrefs=False);self.source=source;self.stack=[]
        self.lines=[0]+[m.end() for m in re.finditer('\n',source)]
        self.prefix=array.array('I',[0]);n=0
        for c in source:n+=2 if ord(c)>65535 else 1;self.prefix.append(n)
        self.parts=[];self.maps=[];self.end=0;self.byte_count=0;self.reasons=set();self.headings=[];self.page=None;self.revision=None
    def pos(self):
        row,col=self.getpos();return self.lines[row-1]+col
    def emit(self,text,a,b,kind):
        if not text:return
        n=u16(text);self.byte_count+=len(text.encode())
        require(self.byte_count<=TEXT_MAX and len(self.maps)<SEG_MAX,'projection bound')
        self.maps.append([self.end,self.end+n,self.prefix[a],self.prefix[b],kind])
        self.parts.append(text);self.end+=n
    def blocked(self):return any(t in SKIP for t in self.stack) or 'body' not in self.stack
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);pos=self.pos();end=pos+len(self.get_starttag_text())
        if tag=='html':self.revision=a.get('about','').rsplit('/',1)[-1]
        if tag=='meta' and a.get('property')=='mw:pageId':self.page=a.get('content')
        if tag not in KNOWN:self.reasons.add('unknown element:'+tag)
        if tag in {'math','table','q','blockquote'}:self.reasons.add('structural review required:'+tag)
        if tag in {'sup','sub'}:self.reasons.add('scripted numeral or reference scope requires review')
        if tag in SKIP and tag!='head':self.reasons.add('projection excludes active/media:'+tag)
        if tag in {'img','embed','object','iframe'}:self.reasons.add('projection excludes media or embedded content:'+tag)
        if tag in BLOCK and not self.blocked():self.emit('\n',pos,pos,'separator')
        if tag.startswith('h') and tag[1:] in ('1','2','3','4','5','6'):self.headings.append([self.end,self.prefix[pos],tag])
        if tag=='br' and not self.blocked():self.emit('\n',pos,end,'break')
        if tag not in VOID:self.stack.append(tag)
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        if tag not in VOID:self.handle_endtag(tag)
    def handle_endtag(self,tag):
        pos=self.pos()
        if tag in BLOCK and not self.blocked():self.emit('\n',pos,pos,'separator')
        if tag in self.stack:
            while self.stack.pop()!=tag: self.reasons.add('HTML repaired nesting')
        elif tag not in VOID:self.reasons.add('unmatched closing element:'+tag)
    def handle_data(self,data):
        if not self.blocked():self.emit(data,self.pos(),self.pos()+len(data),'literal')
    def handle_entityref(self,name):self.entity('&'+name+';')
    def handle_charref(self,name):self.entity('&#'+name+';')
    def entity(self,token):
        if self.blocked():return
        pos=self.pos()
        # HTMLParser permits missing semicolons; bind only bytes actually present.
        if not self.source.startswith(token,pos):token=token[:-1]
        require(self.source.startswith(token,pos),'entity source mismatch')
        self.emit(html.unescape(token),pos,pos+len(token),'entity')
    def finish(self):
        self.close()
        if self.stack:self.reasons.add('unclosed HTML elements')
        text=''.join(self.parts)
        if NOTICE.search(text):self.reasons.add('possible additional rights notice or rights discussion')
        if not text.strip():self.reasons.add('empty visible projection')
        return text

def transform(raw,identity):
    require(len(raw)<=RAW_MAX and sha(raw)==identity['raw_sha256'],'original record digest or size mismatch')
    d=json.loads(raw);lic=exact_license(d)
    require(type(d.get('identifier'))==int and d['identifier']>0,'invalid page')
    require(type(d.get('version',{}).get('identifier'))==int and d['version']['identifier']>0,'invalid revision')
    require(d.get('namespace',{}).get('identifier')==0 and d.get('in_language',{}).get('identifier')=='en','not English mainspace')
    require(isinstance(d.get('name'),str) and d['name'],'missing title')
    require(isinstance(d.get('date_modified'),str),'missing source date')
    datetime.datetime.fromisoformat(d['date_modified'].replace('Z','+00:00'))
    source=d['article_body']['html'];require(isinstance(source,str) and len(source.encode())<=HTML_MAX,'HTML bound')
    p=Projection(source);p.feed(source);body=p.finish()
    require(p.page==str(d['identifier']) and p.revision==str(d['version']['identifier']),'HTML identity mismatch')
    require(d.get('url','').startswith('https://en.wikipedia.org/wiki/'),'source article URL mismatch')
    metadata={k:v for k,v in d.items() if k!='article_body'}
    metadata['attribution']={'credit':d['name']+' — Wikipedia contributors','revision_url':'https://en.wikipedia.org/w/index.php?oldid='+str(d['version']['identifier']),'history_url':'https://en.wikipedia.org/w/index.php?title='+quote(d['name'].replace(' ','_'))+'&action=history','scope':'Archive metadata and linked contributor history, not a locally complete author list or independent rights clearance'}
    capsule={'identity':identity,'metadata':metadata,'html':source,'html_sha256':sha(source.encode()),'text':body,'text_sha256':sha(body.encode()),'mapping':p.maps,'headings':p.headings,'dispositions':sorted(p.reasons),'format':FORMAT}
    validate_capsule(capsule)
    return capsule

def validate_capsule(c):
    require(c['format']==FORMAT,'format');exact_license(c['metadata'])
    source=c['html'];text=c['text'];require(sha(source.encode())==c['html_sha256'] and sha(text.encode())==c['text_sha256'],'capsule text digest')
    # Encode once: validation is linear in article bytes, not quadratic per segment.
    hb=source.encode('utf-16-le');tb=text.encode('utf-16-le');last=0
    for a,b,x,y,kind in c['mapping']:
        require(a==last and a<b and 0<=x<=y<=len(hb)//2 and b<=len(tb)//2,'mapping offset/gap')
        original=hb[2*x:2*y].decode('utf-16-le');rendered=tb[2*a:2*b].decode('utf-16-le')
        if kind=='literal':require(rendered==original,'literal reconstruction')
        elif kind=='entity':require(rendered==html.unescape(original),'entity reconstruction')
        elif kind=='separator':require(x==y and rendered=='\n','separator reconstruction')
        elif kind=='break':require(original.lower().startswith('<br') and rendered=='\n','break reconstruction')
        else:raise ValueError('unknown mapping transformation')
        last=b
    require(last==len(tb)//2,'incomplete rendered coverage')

def passages(text):
    """Bounded contiguous slices; never split a Unicode scalar. No duplicated bodies."""
    begin=0;units=0;parts=[];start=0
    for i,c in enumerate(text):
        units+=2 if ord(c)>65535 else 1
        if units-start>=1600 and (c.isspace() or units-start>=2000):
            parts.append((start,units,sha(text[begin:i+1].encode())));begin=i+1;start=units
    if units>start:parts.append((start,units,sha(text[begin:].encode())))
    return parts

SCHEMA='''PRAGMA page_size=4096; PRAGMA journal_mode=DELETE; PRAGMA cache_size=-8192; PRAGMA temp_store=FILE;
CREATE TABLE dispositions(sequence INTEGER PRIMARY KEY,page INTEGER,revision INTEGER,member TEXT,member_offset INTEGER,raw_bytes INTEGER,raw_sha256 TEXT,status TEXT,reason TEXT);
CREATE INDEX disposition_page ON dispositions(page,revision);
CREATE TABLE latest(page INTEGER PRIMARY KEY,revision INTEGER,date TEXT,raw_sha256 TEXT,sequence INTEGER,conflict INTEGER NOT NULL DEFAULT 0);
CREATE TABLE candidates(page INTEGER PRIMARY KEY,sequence INTEGER,payload BLOB);
CREATE TABLE articles(page INTEGER PRIMARY KEY,revision INTEGER,sequence INTEGER UNIQUE,title TEXT,license TEXT,raw_sha256 TEXT,capsule_sha256 TEXT,payload BLOB,candidate INTEGER);
CREATE TABLE passages(id INTEGER PRIMARY KEY,page INTEGER,start16 INTEGER,end16 INTEGER,sha256 TEXT,UNIQUE(page,start16));
CREATE INDEX passage_page ON passages(page);
CREATE VIEW search_content AS SELECT page AS rowid,page AS docid,title,capsule_text(payload) AS body FROM articles;
CREATE VIRTUAL TABLE search USING fts4(title,body,content='search_content',tokenize=unicode61);
PRAGMA user_version=522;
'''

def choose(c,page,revision,date,digest,seq):
    prev=c.execute('SELECT revision,date,raw_sha256,sequence,conflict FROM latest WHERE page=?',(page,)).fetchone()
    if prev and revision==prev[0] and digest!=prev[2]:
        c.execute('UPDATE latest SET conflict=1 WHERE page=?',(page,));return 'conflicting same revision'
    if prev and (revision,date,digest)<=(prev[0],prev[1],prev[2]):return 'duplicate or older revision'
    conflict=prev[4] if prev else 0
    if prev:c.execute("UPDATE dispositions SET status='superseded' WHERE sequence=?",(prev[3],))
    c.execute('INSERT OR REPLACE INTO latest VALUES(?,?,?,?,?,?)',(page,revision,date,digest,seq,conflict))
    return 'latest'

def produce(stage,out,ceiling,seconds=180):
    require(not out.exists(),'output already exists; retained runs cannot be overwritten')
    require(shutil.disk_usage(out.parent).free>=100*1024**3,'100GiB free-space preflight')
    mem=dict((line.split(':')[0],int(line.split()[1])*1024) for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith(('MemTotal:','MemAvailable:')))
    require(mem['MemAvailable']>=768*1024**2,'host memory preflight')
    out.mkdir();start=time.monotonic();deadline=min(start+seconds,start+max(0,1791269964-time.time()))
    state={'format':FORMAT,'source_admission_established':False,'distribution_ready':False,'status':'RUNNING','sequence_ceiling':ceiling,'source_stage':str(stage),'source_scope':'committed provisional range, not full archive','pid':os.getpid(),'preflight':{'memory':mem,'free_bytes':shutil.disk_usage(out).free},'counts':{},'source_code_sha256':file_sha(Path(__file__))}
    atomic(out/'receipt.json',state)
    db=sqlite3.connect(out/'index.sqlite');db.create_function('capsule_text',1,lambda b:json.loads(inflate(b,CAPSULE_MAX))['text'],deterministic=True);db.executescript(SCHEMA)
    source=sqlite3.connect('file:'+str(stage)+'?mode=ro',uri=True);source.execute('PRAGMA cache_size=-8192');source.execute('BEGIN')
    original_chain=hashlib.sha256();count=0
    def bound():require(time.monotonic()<deadline,'producer deadline; incomplete retained')
    try:
        for seq,member,offset,size,digest,page,rev,title,license_json,error,blob in source.execute('SELECT * FROM records WHERE sequence<=? ORDER BY sequence',(ceiling,)):
            bound();require(seq==count,'source sequence gap including oversized originals; complete accounting required');count+=1
            original_chain.update(canonical([seq,member,offset,size,digest])+b'\n')
            identity={'sequence':seq,'member':member,'member_offset':offset,'raw_bytes':size,'raw_sha256':digest}
            status='excluded';reason='';capsule=None
            # Metadata choice precedes transformation, so unsafe latest never revives old output.
            require(size<=RAW_MAX,'oversized raw record');raw=inflate(blob,RAW_MAX);require(len(raw)==size and sha(raw)==digest,'original digest mismatch')
            try:
                d=json.loads(raw);require(d.get('identifier')==page and d.get('version',{}).get('identifier')==rev and d.get('name')==title,'stage metadata mismatch')
                require(type(page)==int and type(rev)==int and page>0 and rev>0,'invalid page/revision')
                reason=choose(db,page,rev,d.get('date_modified',''),digest,seq)
                if reason=='latest':
                    db.execute('DELETE FROM candidates WHERE page=?',(page,))
                    capsule=transform(raw,identity);payload=canonical(capsule);require(len(payload)<=CAPSULE_MAX,'capsule bound')
                    db.execute('INSERT INTO candidates VALUES(?,?,?)',(page,seq,zlib.compress(payload,6)));status='transformed'
                else:status='duplicate'
            except (ValueError,KeyError,TypeError,UnicodeError,RecursionError) as e:reason=type(e).__name__+': '+str(e)
            db.execute('INSERT INTO dispositions VALUES(?,?,?,?,?,?,?,?,?)',(seq,page,rev,member,offset,size,digest,status,reason))
            if count%100==0:
                db.commit();state.update(records=count,original_chain_sha256=original_chain.hexdigest(),rss_max_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);atomic(out/'receipt.json',state)
        require(count==ceiling+1,'requested committed range unavailable');source.rollback();source.close()
        # Stream latest capsules, create contentless postings, then delete the staging copy.
        pid=0
        for page,seq,blob in db.execute('SELECT c.page,c.sequence,c.payload FROM candidates c JOIN latest l ON c.page=l.page WHERE l.conflict=0 ORDER BY c.page'):
            bound();cap=json.loads(inflate(blob,CAPSULE_MAX));meta=cap['metadata'];payload=canonical(cap)
            db.execute('INSERT INTO articles VALUES(?,?,?,?,?,?,?,?,?)',(page,meta['version']['identifier'],seq,meta['name'],meta['license'][0]['identifier'],cap['identity']['raw_sha256'],sha(payload),blob,int(not cap['dispositions'])))
            db.execute('INSERT INTO search(docid,title,body) VALUES(?,?,?)',(page,meta['name'],cap['text']))
            for a,b,h in passages(cap['text']):pid+=1;db.execute('INSERT INTO passages VALUES(?,?,?,?,?)',(pid,page,a,b,h))
        db.execute('DELETE FROM candidates');db.commit();bound();db.execute('VACUUM');db.commit()
        require(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','index integrity')
        state['counts']={t:db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ['dispositions','latest','articles','passages']}
        state['counts']['candidate_articles_not_admitted']=db.execute('SELECT count(*) FROM articles WHERE candidate=1').fetchone()[0]
        state['disposition_counts']=dict(db.execute('SELECT status,count(*) FROM dispositions GROUP BY status'))
        state['license_counts']=dict(db.execute('SELECT license,count(*) FROM articles GROUP BY license'))
        state['schema_storage_bytes']=dict(db.execute('SELECT name,sum(pgsize) FROM dbstat GROUP BY name'))
        state.update(status='ENGINEERING_COMPLETE_PROVISIONAL',original_chain_sha256=original_chain.hexdigest(),index_bytes=(out/'index.sqlite').stat().st_size,seconds=time.monotonic()-start,rss_max_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        db.close();state['index_sha256']=file_sha(out/'index.sqlite');atomic(out/'receipt.json',state)
        return state
    except BaseException as e:
        db.commit();state.update(status='FAIL_RETAINED',error=type(e).__name__+': '+str(e),records=count,seconds=time.monotonic()-start,rss_max_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);atomic(out/'receipt.json',state);raise
    finally:
        db.close();source.close()

class Reader:
    def __init__(self,path):
        receipt=json.loads((path/'receipt.json').read_text());require(receipt['status']=='ENGINEERING_COMPLETE_PROVISIONAL' and receipt['source_admission_established'] is False,'not provisional engineering edition')
        require(file_sha(path/'index.sqlite')==receipt['index_sha256'],'index digest mismatch')
        self.db=sqlite3.connect('file:'+str(path/'index.sqlite')+'?mode=ro',uri=True);self.db.execute('PRAGMA cache_size=-8192');self.db.create_function('capsule_text',1,lambda b:json.loads(inflate(b,CAPSULE_MAX))['text'],deterministic=True)
    def article(self,page):
        r=self.db.execute('SELECT capsule_sha256,payload FROM articles WHERE page=?',(page,)).fetchone();require(r is not None,'missing article');b=inflate(r[1],CAPSULE_MAX);require(sha(b)==r[0],'capsule hash');c=json.loads(b);validate_capsule(c);return c
    def search(self,query,cancel=lambda:False):
        require(not cancel(),'cancelled');tokens=re.findall(r'\w+',query)[:12]
        if not tokens:return []
        expression=' AND '.join('"'+x.replace('"','')+'"' for x in tokens)
        self.db.set_progress_handler(lambda:1 if cancel() else 0,1000)
        try:rows=self.db.execute('SELECT docid FROM search WHERE search MATCH ? LIMIT 20',(expression,)).fetchall()
        finally:self.db.set_progress_handler(None,0)
        out=[]
        for (page,) in rows:
            require(not cancel(),'cancelled');c=self.article(page);text=c['text'];pieces=self.db.execute('SELECT start16,end16,sha256 FROM passages WHERE page=?',(page,)).fetchall()
            scored=[]
            for a,b,h in pieces:
                quote_text=slice16(text,a,b);require(sha(quote_text.encode())==h,'passage digest');score=sum(quote_text.casefold().count(t.casefold()) for t in tokens)
                scored.append((score,a,b,h,quote_text))
            if scored:
                _,a,b,h,q=max(scored,key=lambda v:(v[0],-v[1]));out.append({'page':page,'revision':c['metadata']['version']['identifier'],'title':c['metadata']['name'],'start16':a,'end16':b,'sha256':h,'quote':q,'source_admission_established':False})
        return out

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('stage',type=Path);a.add_argument('out',type=Path);a.add_argument('--ceiling',type=int,required=True);a.add_argument('--seconds',type=int,default=180);v=a.parse_args()
    resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));resource.setrlimit(resource.RLIMIT_CPU,(300,300));os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
    print(json.dumps(produce(v.stage,v.out,v.ceiling,v.seconds),indent=2))
