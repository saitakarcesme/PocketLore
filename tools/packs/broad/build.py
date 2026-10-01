#!/usr/bin/env python3
"""Deterministic local evaluation edition from the sealed source handoff; no network or staged writes."""
from pathlib import Path
import argparse,hashlib,json,sqlite3,zipfile,collections,unicodedata,time,resource,re
ROOT=Path(__file__).resolve().parents[3]
STAGE=Path('/home/isa/PocketLore-control/corpus-acquisition/snapshot-final')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def norm(s):return ' '.join(unicodedata.normalize('NFKC',s).casefold().split())
def build(out):
 start=time.monotonic();out.mkdir(parents=True,exist_ok=True)
 inventory=json.loads((STAGE/'ARTIFACTS.json').read_text());assert sha(STAGE/'ARTIFACTS.json')=='849b9b065940b2dc7019c306eac1805fa43fc09c9d9eb396e0d7740a9e9e8810'
 # Validate all sealed bytes, including reused raw shards/receipts, without redownloading.
 for n,v in inventory['files'].items():assert (STAGE/n).stat().st_size==v['bytes'] and sha(STAGE/n)==v['sha256'],n
 db=out/'index.sqlite';assert not db.exists(),'Use a new output directory; preserve prior experiments'
 con=sqlite3.connect(db);con.executescript('''PRAGMA page_size=4096; PRAGMA journal_mode=DELETE;
 CREATE TABLE documents(id TEXT PRIMARY KEY,title TEXT NOT NULL,url TEXT NOT NULL UNIQUE,date TEXT NOT NULL,rights TEXT NOT NULL,provenance TEXT NOT NULL,body TEXT NOT NULL,sha TEXT NOT NULL UNIQUE,area TEXT NOT NULL);
 CREATE TABLE passages(pid INTEGER PRIMARY KEY,citation TEXT NOT NULL UNIQUE,document TEXT NOT NULL REFERENCES documents(id),body TEXT NOT NULL,sha TEXT NOT NULL UNIQUE,normalized_sha TEXT NOT NULL UNIQUE,start INTEGER NOT NULL,end INTEGER NOT NULL);
 CREATE INDEX passage_document ON passages(document);
 CREATE VIRTUAL TABLE search USING fts4(title,body,tokenize=porter);
 PRAGMA user_version=210;''')
 docs={};seen=set();areas=collections.Counter();flags=[]
 for line in (STAGE/'sources.jsonl').open():
  d=json.loads(line);assert digest(d['text'])==d['source_text_sha256'] and d['license']=='CC-BY-SA-4.0'
  for k in ['attribution','history_url','license_url','upstream_shard_sha256','dataset_revision','modifications']:assert d[k]
  normalized=digest(norm(d['text']));assert normalized not in seen;seen.add(normalized);docs[d['id']]=d;areas[d['area']]+=1
  provenance='\n'.join([d['attribution'],'Article: '+d['url'],'Contributor history: '+d['history_url'],'Dataset revision: '+d['dataset_revision'],'Upstream shard SHA-256: '+d['upstream_shard_sha256'],'Source SHA-256: '+d['source_text_sha256'],'Article revision/time unavailable; snapshot is not edit date.','Modifications: '+d['modifications'],'Generation disabled: historical extract can omit formulas/units and source-specific attribution. Evaluation only; distribution review unresolved.'])
  rights='CC BY-SA 4.0; '+d['license_url']+'; '+d['attribution']+'; retain attribution/history/license, indicate changes, share adaptations alike; third-party exceptions unresolved.'
  con.execute('INSERT INTO documents VALUES(?,?,?,?,?,?,?,?,?)',(d['id'],d['title'],d['url'],'Historical 2023-11-01 dataset; article edit date unknown',rights,provenance,d['text'],d['source_text_sha256'],d['area']))
 count=0;areas_pass=collections.Counter();perdoc=collections.Counter()
 for line in (STAGE/'chunks.jsonl').open():
  c=json.loads(line);d=docs[c['document_id']];text=c['text'];assert d['text'][c['start_char']:c['end_char']]==text and digest(text)==c['text_sha256']
  for k in ['license','license_url','url','history_url','attribution','source_text_sha256']:assert c[k]==d[k]
  count+=1;start16=len(d['text'][:c['start_char']].encode('utf-16-le'))//2;end16=start16+len(text.encode('utf-16-le'))//2
  con.execute('INSERT INTO passages VALUES(?,?,?,?,?,?,?,?)',(count,'wiki-'+c['document_id']+'-'+c['text_sha256'][:16],d['id'],text,c['text_sha256'],digest(norm(text)),start16,end16));con.execute('INSERT INTO search(docid,title,body) VALUES(?,?,?)',(count,d['title'],text));areas_pass[d['area']]+=1;perdoc[d['id']]+=1
  # Do not repair absent facts by guessing. Flags are diagnostic, not a full quality filter.
  if re.search(r'\(\s*[,;]\s*|\b(?:up to|of|is|by)\s{2,}(?:in|and|,|\.)',text):flags.append({'citation':'wiki-'+c['document_id']+'-'+c['text_sha256'][:16],'reason':'Possible extraction gap; not cleared for generation'})
 con.commit();con.execute('VACUUM');assert con.execute('PRAGMA integrity_check').fetchone()[0]=='ok';schema=con.execute("SELECT name,sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY name").fetchall();con.close()
 assert len(docs)>=1000 and count>=10000 and min(areas.values())>=50
 manifest={'format':'pocketlore-sqlite-v1','id':'broad-reference-20231101-evaluation-v1','documents':len(docs),'passages':count,'areas':dict(areas),'area_passages':dict(areas_pass),'db_sha256':sha(db),'db_bytes':db.stat().st_size,'schema':schema,'license':'CC-BY-SA-4.0','distribution_ready':False,'snapshot_inventory_sha256':sha(STAGE/'ARTIFACTS.json'),'sources_sha256':sha(STAGE/'sources.jsonl'),'chunks_sha256':sha(STAGE/'chunks.jsonl'),'warning':'Historical 2023 extraction; formulas, units and third-party attribution may be missing. Evaluation-only source lookup; no current travel/safety guidance; generation disabled pending review.','source_topics':'Heuristic assignments, not proof of semantic breadth or 50 reviewed documents per area.'}
 pack=out/'broad-reference.plpack'
 with zipfile.ZipFile(pack,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for name,data in [('manifest.json',(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode()),('index.sqlite',db.read_bytes()),('CC-BY-SA-4.0.html',(STAGE/'raw/cc-by-sa-4.0.html').read_bytes())]:
   i=zipfile.ZipInfo(name,(2026,10,1,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,data)
 result={**manifest,'pack_sha256':sha(pack),'pack_bytes':pack.stat().st_size,'elapsed_seconds':time.monotonic()-start,'peak_host_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'extraction_flags':len(flags),'source_files_verified':len(inventory['files']),'download_bytes_reused':sum(v['bytes'] for n,v in inventory['files'].items() if n.endswith('.parquet'))}
 (out/'build.json').write_text(json.dumps(result,indent=2)+'\n');(out/'extraction-flags.json').write_text(json.dumps(flags,indent=2)+'\n');print(json.dumps(result,indent=2));return pack
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();build(a.out)
