#!/usr/bin/env python3
"""Host reference for the immutable Android reader contract; no network or bulk loading."""
import argparse, collections, hashlib, json, math, pathlib, re, sqlite3, time, zlib
TOKENS=re.compile(r'[^\W_]+',re.UNICODE)
STOP=set('a an the is are of to in and or for from with what how why which when does do by on at as into explain compare between'.split())
def words(text):return [w.casefold() for w in TOKENS.findall(text)]
class Reader:
    def __init__(self,root):
        root=pathlib.Path(root)
        self.packs=[root] if (root/'catalog.sqlite').exists() else sorted(p.parent for p in root.glob('*/catalog.sqlite') if (p.parent/'measurement.json').exists())
        if not self.packs:raise ValueError('No completed packs')
        self.alias_db=sqlite3.connect(f'file:{root / "redirect-aliases.sqlite"}?mode=ro&immutable=1',uri=True) if (root/'redirect-aliases.sqlite').exists() else None
        if self.alias_db:self.alias_db.execute('PRAGMA cache_size=-4096')
        self.alias_normalized=bool(self.alias_db and self.alias_db.execute("SELECT 1 FROM sqlite_master WHERE name='shard_names' AND type='table'").fetchone())
        self.block_cache=collections.OrderedDict()
        self.blocked=[]
        self.dbs=[]
        for pack in self.packs:
            db=sqlite3.connect(f'file:{pack / "catalog.sqlite"}?mode=ro&immutable=1',uri=True);db.row_factory=sqlite3.Row
            db.execute('PRAGMA cache_size=-4096');db.execute('PRAGMA mmap_size=0');self.dbs.append(db);self.blocked.append(bool(db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='blocks'").fetchone()))
        self.total=sum(db.execute('SELECT count(*) FROM articles').fetchone()[0] for db in self.dbs)
    def payload(self,shard,row):
        def valid(raw,expected):
            h=hashlib.sha256(raw)
            return h.digest()==expected if isinstance(expected,bytes) else h.hexdigest()==expected
        shared=getattr(self,'blocked',[])[shard] if getattr(self,'blocked',[]) else False
        if shared:
            block=self.dbs[shard].execute('SELECT * FROM blocks WHERE id=?',(row['block_id'],)).fetchone()
            if not block:raise ValueError('Missing block')
            meta=block;key=(shard,row['block_id'])
            raw=self.block_cache.get(key)
        else:meta=row;raw=None
        if not 0<meta['length']<=64*1024**2 or not 0<meta['raw_length']<=128*1024**2:raise ValueError('Block size bound')
        if raw is None:
            with (self.packs[shard]/'articles.blocks').open('rb') as f:f.seek(meta['offset']);b=f.read(meta['length'])
            dec=zlib.decompressobj();raw=dec.decompress(b,meta['raw_length']+1)
            if not dec.eof or dec.unused_data or len(raw)!=meta['raw_length'] or not valid(raw,meta['sha256']):raise ValueError('Block integrity')
            if shared and len(raw)<=8*1024**2:
                self.block_cache[key]=raw
                while len(self.block_cache)>2:self.block_cache.popitem(last=False)
        if shared:
            if row['offset']<0 or row['length']!=row['raw_length'] or row['offset']+row['length']>len(raw):raise ValueError('Record slice bounds')
            raw=raw[row['offset']:row['offset']+row['length']]
            if not valid(raw,row['sha256']):raise ValueError('Record integrity')
        payload=json.loads(raw)
        if not valid(payload['text'].encode(),row['text_sha256']) or not valid(payload['wikitext'].encode(),row['wikitext_sha256']):raise ValueError('Source field integrity')
        return payload
    def source(self,title):
        for s,db in enumerate(self.dbs):
            row=db.execute('SELECT * FROM articles WHERE title=?',(title,)).fetchone()
            if row:return s,row,self.payload(s,row)
        return None
    def alias_rows(self,query):
        if not self.alias_db:return []
        sql='SELECT a.target,n.name,a.fragment FROM aliases a JOIN shard_names n ON n.id=a.shard WHERE a.alias=? LIMIT 8' if getattr(self,'alias_normalized',False) else 'SELECT target,shard,fragment FROM aliases WHERE alias=? LIMIT 8'
        return list(self.alias_db.execute(sql,(query.replace('_',' ').casefold(),)))
    def search(self,query,k=10):
        start=time.perf_counter();terms=list(dict.fromkeys(w for w in words(query) if w not in STOP))[:16]
        if not query.strip():return {'hits':[],'milliseconds':0,'candidates':0,'terms':[],'term_document_frequencies':{},'answer_support':'not assessed by lexical retrieval'}
        df={w:sum((db.execute('SELECT doc FROM terms WHERE term=?',(w,)).fetchone() or [0])[0] for db in self.dbs) for w in terms}
        match=' OR '.join('"'+w.replace('"','""')+'"' for w in terms)
        candidates={}
        redirect_hits=self.alias_rows(query)
        for s,db in enumerate(self.dbs):
            for target,shard,fragment in redirect_hits:
                if self.packs[s].name==pathlib.Path(shard).stem:
                    r=db.execute('SELECT * FROM articles WHERE id=?',(target,)).fetchone()
                    if r:candidates[(s,r['id'])]=(r,True)
            exact=db.execute('SELECT a.* FROM aliases x JOIN articles a ON a.id=x.target WHERE alias=? LIMIT 4',(query.replace('_',' ').casefold(),)).fetchall()
            for r in exact:candidates[(s,r['id'])]=(r,True)
            for hit in (db.execute('SELECT rowid,bm25(search,5.0,1.0) score FROM search WHERE search MATCH ? ORDER BY score LIMIT 12',(match,)) if terms else []):
                r=db.execute('SELECT * FROM articles WHERE id=?',(hit['rowid'],)).fetchone();candidates.setdefault((s,r['id']),(r,False))
        scored=[]
        for (s,_),(r,exact) in candidates.items():
            payload=self.payload(s,r);body=words(payload['text']);freq=collections.Counter(body);title=set(words(r['title']));score=100.0 if exact else 0
            for term in terms:
                idf=math.log(1+(self.total-df[term]+0.5)/(df[term]+0.5));tf=freq[term]
                score+=idf*(tf*2.2/(tf+1.2*(0.25+0.75*len(body)/500)) if tf else 0)+(idf*2 if term in title else 0)
            scored.append({'id':r['id'],'title':r['title'],'tier':r['tier'],'revision':r['revision'],'url':r['url'],'score':score,'shard':self.packs[s].name})
        scored.sort(key=lambda x:(-x['score'],x['id']))
        return {'hits':scored[:k],'milliseconds':(time.perf_counter()-start)*1000,'candidates':len(candidates),'terms':terms,'term_document_frequencies':df,'answer_support':'not assessed by lexical retrieval'}
    def close(self):
        for db in self.dbs:db.close()
        if self.alias_db:self.alias_db.close()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('query');a=p.parse_args();r=Reader(a.root);print(json.dumps(r.search(a.query),indent=2));r.close()
