#!/usr/bin/env python3
"""Read sealed lane bytes only; stream hashes and bounded full-shard queries on rig."""
import hashlib,json,pathlib,sqlite3,sys,time,resource
ROOT=pathlib.Path(__file__).resolve().parents[3]
LANES=pathlib.Path('/home/isa/PocketLore-control/scale-workers')
sys.path.insert(0,str(ROOT/'tools/scale/places'))
from compact_search import search,source

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def db(p):return sqlite3.connect('file:'+str(p)+'?mode=ro&immutable=1',uri=True)
def main(out):
 out.mkdir(parents=True,exist_ok=False);start=time.monotonic()
 protocol=json.loads((ROOT/'tools/evaluation/full-scale/protocol.json').read_text())
 wiki=LANES/'wiki/edition-v7';places=LANES/'places/data'
 inv=json.loads((wiki/'installed-inventory.json').read_text());handoff=json.loads((LANES/'places/HANDOFF.json').read_text())
 checks=[]
 for base,specs in [(wiki,inv['files']),(pathlib.Path('/'),handoff['assets'])]:
  for f in specs:
   p=base/f['path'];actual=sha(p);assert p.stat().st_size==f['bytes'] and actual==f['sha256'],str(p)
   checks.append({'path':str(p),'bytes':p.stat().st_size,'sha256':actual});print('verified',p.name,flush=True)
 (out/'files.json').write_text(json.dumps(checks,indent=2)+'\n')
 shards=sorted(wiki.glob('*/catalog.sqlite'));counts=[]
 for p in shards:
  with db(p) as c: row=c.execute("select count(*),sum(tier='full'),sum(tier='lead') from articles").fetchone()
  counts.append(dict(shard=p.parent.name,documents=row[0],full=row[1],lead=row[2]))
 ps=sorted(places.glob('compact-*.sqlite'));pc=[]
 for p in ps:
  with db(p) as c:n=c.execute('select sum(records) from block').fetchone()[0]
  pc.append({'shard':p.name,'source_records':n})
 (out/'counts.json').write_text(json.dumps({'wiki':counts,'places':pc},indent=2)+'\n')
 alias=db(wiki/'redirect-aliases.sqlite');queries=[]
 for q in protocol['wiki_queries']+protocol['redirects']:
  t=time.monotonic();exact=[];local=[]
  redirects=list(alias.execute('select s.name,a.target from aliases a join shard_names s on s.id=a.shard where a.alias=? limit 12',(q.lower(),)))
  for p in shards:
   with db(p) as c:
    c.execute('pragma cache_size=-4096');c.execute('pragma mmap_size=0')
    for row in c.execute('select id,title from articles where title=? limit 4',(q,)):exact.append({'shard':p.parent.name,'id':row[0],'title':row[1],'route':'exact'})
    for s,i in redirects:
     if pathlib.Path(s).stem==p.parent.name:
      for row in c.execute('select id,title from articles where id=?',(i,)):exact.append({'shard':p.parent.name,'id':row[0],'title':row[1],'route':'redirect'})
    expr=' OR '.join('"'+w+'"' for w in q.lower().split())
    rows=c.execute('select a.id,a.title from search join articles a on a.id=search.rowid where search match ? order by bm25(search,5.0,1.0) limit 12',(expr,)).fetchall()
    local.append([{'shard':p.parent.name,'id':r[0],'title':r[1],'route':'rank'} for r in rows])
  merged=exact+[s[i] for i in range(12) for s in local if i<len(s)];seen=set();hits=[]
  for h in merged:
   key=(h['shard'],h['id'])
   if key not in seen:seen.add(key);hits.append(h)
  queries.append({'query':q,'hits':hits[:12],'ms':(time.monotonic()-t)*1000});print(q,queries[-1]['ms'],flush=True)
 (out/'wiki-queries.json').write_text(json.dumps(queries,indent=2)+'\n')
 cities=db(places/'cities.sqlite');results=[]
 for name in protocol['cities']:
  t=time.monotonic();anchor=cities.execute('select c.id,c.lat,c.lon,c.name,c.country from city c join alias a on a.city_id=c.id where a.name_key=? order by c.population desc,c.id limit 1',(name.lower(),)).fetchone()
  assert anchor,name
  hits=search(ps,anchor[1],anchor[2],radius_km=1,limit=30)
  categories=search(ps,anchor[1],anchor[2],radius_km=1,category=protocol['category'],limit=10)
  row={'query':name,'anchor':anchor,'hits':hits,'category_hits':categories,'ms':(time.monotonic()-t)*1000}
  if hits:row['first_source']=source(hits[0]['shard'],hits[0]['block_id'],hits[0]['source_ordinal'],hits[0]['id'])
  results.append(row);(out/'cities.json').write_text(json.dumps(results,indent=2)+'\n');print(name,len(hits),row['ms'],flush=True)
 absent=search(ps,19.4326,-99.1332,1,category='pocketlore nonexistent category 300')
 assert not absent
 (out/'summary.json').write_text(json.dumps({'platform':'LLMRig host, not installed Android','seconds':time.monotonic()-start,'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'wiki_documents':sum(x['documents'] for x in counts),'places_source_records':sum(x['source_records'] for x in pc),'city_positive':sum(bool(x['hits']) for x in results),'absent_category':absent,'files_bytes':sum(f['bytes'] for f in checks)},indent=2)+'\n')
if __name__=='__main__':main(pathlib.Path(sys.argv[1]))
