"""Independent disk-backed selection and capsule audit; never admission approval."""
import argparse,base64,hashlib,html,json,pathlib,sqlite3,zlib

def sha(b):return hashlib.sha256(b).hexdigest()
def audit(out,stage,ranking):
 out=pathlib.Path(out);state=json.loads((out/'status.json').read_text());assert state['status']=='PROVISIONAL_PREFIX_COMPLETE' and not state['source_admission_established'] and not state['whole_source_identity_verified'];through=state['configuration']['through'];count=state['configuration']['count']
 d=sqlite3.connect('file:'+str(out/'index.sqlite')+'?mode=ro',uri=True);d.execute('pragma cache_size=-2048');d.execute('pragma mmap_size=0');d.execute('pragma temp_store=FILE')
 # Independent SQL window-function choice over original indexed prefix. No producer selector call.
 src=sqlite3.connect('file:'+str(stage)+'?mode=ro',uri=True);src.execute('pragma query_only=on');src.execute('pragma cache_size=-2048');src.execute('pragma mmap_size=0');src.execute('pragma temp_store=FILE');src.execute('ATTACH DATABASE ? AS rank',('file:'+str(ranking)+'?mode=ro&immutable=1',))
 query='''WITH versions AS (SELECT sequence,page,revision,raw_sha256,metadata_error,license_json,title,row_number() OVER(PARTITION BY page ORDER BY revision DESC,sequence ASC) r FROM records WHERE sequence<=?), conflicts AS (SELECT page FROM records WHERE sequence<=? GROUP BY page,revision HAVING count(distinct raw_sha256)>1) SELECT v.page,v.revision,v.sequence,v.raw_sha256,p.views FROM versions v JOIN rank.priority p ON p.id=v.page WHERE r=1 AND p.full=1 AND metadata_error IS NULL AND license_json IS NOT NULL AND title IS NOT NULL AND v.page NOT IN (SELECT page FROM conflicts) ORDER BY p.views DESC,v.page LIMIT ?'''
 expected=src.execute(query,(through,through,count)).fetchall();actual=d.execute('SELECT page,revision,sequence,sha,views FROM selected ORDER BY position').fetchall();assert actual==expected,'Independent general-priority/latest oracle differs'
 assert len(actual)==count and len({r[0] for r in actual})==count
 assert d.execute('select count(*) from originals').fetchone()[0]==through+1
 # Check every content-addressed capsule independently; bounded one chunk at a time.
 pieces=0;uncompressed=compressed=0
 for digest,size,blob in d.execute('SELECT sha,bytes,z FROM capsules'):
  z=zlib.decompressobj();raw=z.decompress(blob,262145);assert len(raw)==size<=262144 and z.eof and not z.unused_data and not z.unconsumed_tail and sha(raw)==digest;pieces+=1;uncompressed+=size;compressed+=len(blob)
 # Deterministic distributed samples selected before inspecting outputs. Refusals remain in counts.
 positions=sorted(set([1,count]+list(range(1,count+1,997))));samples=[]
 for position in positions:
  page,rev,seq,digest,views,outcome=d.execute('SELECT page,revision,sequence,sha,views,outcome FROM selected WHERE position=?',(position,)).fetchone()
  if outcome!='inspection-only':samples.append({'position':position,'outcome':outcome});continue
  def collect(kind):
   result=[];coordinate=0
   for part,a,b,key,blob in d.execute('SELECT p.part,p.start,p.end,p.sha,c.z FROM pieces p JOIN capsules c ON c.sha=p.sha WHERE p.page=? AND p.revision=? AND p.kind=? ORDER BY part',(page,rev,kind)):
    assert part==len(result);raw=zlib.decompress(blob);assert sha(raw)==key
    if kind=='original':assert a==coordinate and b==a+len(raw);coordinate=b
    elif kind=='html':assert a==coordinate and b==a+len(raw.decode().encode('utf-16-le'))//2;coordinate=b
    else:
     group=json.loads(raw);assert a==group[0][0] and b==group[-1][0]+1 and (not coordinate or a==coordinate);coordinate=b
    result.append(raw)
   return result
  raw=b''.join(collect('original'));assert sha(raw)==digest
  original=src.execute('SELECT raw_sha256,raw_bytes,original_zlib,license_json FROM records WHERE sequence=?',(seq,)).fetchone();assert original is not None and sha(zlib.decompress(original[2]))==digest and len(raw)==original[1]
  document=json.loads(raw);source=document['article_body']['html'];source16=source.encode('utf-16-le');assert b''.join(collect('html')).decode()==source
  metadata=json.loads(d.execute('SELECT metadata FROM articles WHERE page=? AND revision=?',(page,rev)).fetchone()[0]);assert metadata['license']==document['license']==json.loads(original[3]) and metadata['version']==document['version'];assert document['identifier']==page and document['version']['identifier']==rev
  nodes=[node for part in collect('structure') for node in json.loads(part)]
  for n,parent,tag,attrs,a,b,text,kind in nodes:
   exact=source16[2*a:2*b].decode('utf-16-le')
   if kind=='literal':assert text==exact
   elif kind=='entity':assert text==html.unescape(exact)
   if parent:up=nodes[parent-1];assert up[4]<=a<=b<=up[5]
  for node_id,a,b,fragment,scope,title,text,disposition in d.execute('SELECT node,start,end,fragment_sha,scope,title,text,disposition FROM contexts WHERE page=? AND revision=?',(page,rev)):
   assert sha(source16[2*a:2*b].decode('utf-16-le').encode())==fragment
   node=nodes[node_id-1];assert node[4:6]==[a,b] and title==document['name']
   descendants=[n for n in nodes if n[4]>=a and n[5]<=b and n[7] in ('literal','entity')]
   assert text==''.join(n[6] for n in descendants),'Indexed text differs from exact source text'
   assert disposition.startswith(('inspection-context:','reconstructible-prose; independent rights/support review pending'))
   for node,tag,start,end in json.loads(scope):assert nodes[node-1][2]==tag and start<=a<=b<=end
  samples.append({'position':position,'sequence':seq,'page':page,'revision':rev,'original_sha256':digest,'html_sha256':sha(source.encode()),'nodes':len(nodes),'license':document['license'],'outcome':outcome})
 src.close();d.close()
 return {'status':'PASS','selected_distinct_originals':count,'prefix_originals':through+1,'independent_selection':'SQL window latest + frozen importance page-ID join, exact order/ties','capsules_verified':pieces,'capsule_uncompressed_bytes':uncompressed,'capsule_compressed_bytes':compressed,'deterministic_source_samples':samples,'source_admission_established':False,'not_full_source_latest':True}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('out');p.add_argument('stage');p.add_argument('ranking');a=p.parse_args();result=audit(a.out,a.stage,a.ranking);path=pathlib.Path(a.out)/'independent-oracle.json';path.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
