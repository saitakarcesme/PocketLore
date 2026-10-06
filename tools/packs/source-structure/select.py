#!/usr/bin/env python3
"""Disk-backed latest/importance join specification implementation; separate owned output.

Engineering mode only. Does not transform originals, mark ready or mutate staging.
"""
import argparse,hashlib,json,pathlib,sqlite3,time

def digest(path):
 with open(path,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def select(stage,rank,rank_sha,out,ceiling,cutoff):
 assert digest(rank)==rank_sha,'Frozen ranking identity mismatch'
 assert not pathlib.Path(out).exists(),'Refuse overwrite or implicit resume'
 dest=sqlite3.connect(out);dest.executescript('PRAGMA cache_size=-2048; PRAGMA mmap_size=0; PRAGMA temp_store=FILE; CREATE TABLE ledger(sequence INTEGER PRIMARY KEY,page INTEGER,revision INTEGER,binding TEXT,reason TEXT); CREATE TABLE latest(page INTEGER PRIMARY KEY,revision INTEGER,sequence INTEGER,sha TEXT,blocked INTEGER);')
 seq=0
 try:
  while seq<=ceiling:
   assert time.time()<cutoff,'Absolute cutoff'
   # Detached metadata-only committed batches; no raw body or pinned long snapshot.
   src=sqlite3.connect('file:'+str(stage)+'?mode=ro',uri=True,timeout=.2)
   try:
    src.execute('PRAGMA cache_size=-2048');src.execute('PRAGMA mmap_size=0')
    rows=src.execute('SELECT sequence,page,revision,raw_sha256,metadata_error,member,member_offset,raw_bytes FROM records WHERE sequence>=? AND sequence<=? ORDER BY sequence LIMIT 256',(seq,ceiling)).fetchall()
   finally:src.close()
   assert rows,'Incomplete committed prefix'
   for n,page,rev,sha,error,member,offset,size in rows:
    assert n==seq,'Missing original/oversized disposition; full accounting denied'
    binding=hashlib.sha256(json.dumps([n,page,rev,sha,error,member,offset,size],ensure_ascii=False,separators=(',',':')).encode()).hexdigest();reason=error or 'metadata-only; original not reconstructed'
    dest.execute('INSERT INTO ledger VALUES(?,?,?,?,?)',(n,page,rev,binding,reason))
    if page is not None and rev is not None:
     old=dest.execute('SELECT revision,sha,blocked FROM latest WHERE page=?',(page,)).fetchone()
     if old is None or rev>old[0]:dest.execute('INSERT OR REPLACE INTO latest VALUES(?,?,?,?,?)',(page,rev,n,sha,int(bool(error)) or (old[2] if old else 0)))
     elif rev==old[0] and sha!=old[1]:dest.execute('UPDATE latest SET blocked=1 WHERE page=?',(page,))
    seq+=1
   dest.commit()
  dest.execute('ATTACH DATABASE ? AS ranking',('file:'+str(rank)+'?mode=ro',))
  dest.execute('CREATE TABLE selected AS SELECT l.page,l.revision,l.sequence,l.sha,p.views FROM latest l JOIN ranking.priority p ON p.id=l.page WHERE l.blocked=0 AND p.full=1 ORDER BY p.views DESC,l.page')
  dest.execute('CREATE UNIQUE INDEX selected_page ON selected(page)');dest.commit()
  return {'prefix_through':seq-1,'originals':dest.execute('select count(*) from ledger').fetchone()[0],'distinct_latest':dest.execute('select count(*) from latest').fetchone()[0],'selected':dest.execute('select count(*) from selected').fetchone()[0],'source_admission_established':False,'latest_freshness':'provisional prefix only','rank_sha256':rank_sha}
 finally:dest.close()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--stage',required=True);p.add_argument('--ranking',required=True);p.add_argument('--ranking-sha256',required=True);p.add_argument('--out',required=True);p.add_argument('--through',type=int,required=True);p.add_argument('--cutoff-epoch',type=float,required=True);a=p.parse_args();assert a.cutoff_epoch<=1791269964;print(json.dumps(select(a.stage,a.ranking,a.ranking_sha256,a.out,a.through,a.cutoff_epoch),indent=2))
