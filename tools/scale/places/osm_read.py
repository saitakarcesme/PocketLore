"""Decode either OSM staging rows or bounded source blocks without changing facts."""
import json,zlib
from compact_search import inflate
def is_compact(db):return db.execute("SELECT 1 FROM sqlite_master WHERE name='block'").fetchone() is not None
def expand(db,row,compact=False,cache=None):
 r=dict(row)
 if not compact:
  if isinstance(r['raw'],bytes):r['raw']=zlib.decompress(r['raw']).decode()
  return r
 cache={} if cache is None else cache;block=r.pop('block');slot=r.pop('slot')
 if block not in cache:
  if len(cache)>=2:cache.clear()
  cache[block]=inflate(*db.execute('SELECT payload,sha256 FROM block WHERE id=?',(block,)).fetchone())
 a,b,raw=cache[block][slot];assert (a,b)==(r['lat'],r['lon']) and raw['id']==r['id'] and raw['type']==r['type'];tags=raw['tags'];assert tags.get('diet:vegan')==r['vegan'] and tags.get('diet:vegetarian')==r['vegetarian'];r.update(name=tags.get('name'),version=raw['version'],hours=tags.get('opening_hours'),snapshot=db.execute('SELECT sha256 FROM snapshot').fetchone()[0],raw=json.dumps(raw,ensure_ascii=False,separators=(',',':')));return r
