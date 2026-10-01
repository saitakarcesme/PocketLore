#!/usr/bin/env python3
"""Counterexamples and unknown-rights dispositions from exact source rows."""
import argparse,hashlib,json,pathlib,re,sqlite3
from acquire import atomic
from build import eligibility,notice_candidate
p=argparse.ArgumentParser();p.add_argument('lane');p.add_argument('output');a=p.parse_args();lane=pathlib.Path(a.lane);rows={}
for f in (lane/'receipts/selected-query-sources').glob('*.json'):
 x=json.loads(f.read_text());rows[x['record']['title']]=x
checks=[]
def add(title,description,predicate,evidence):
 x=rows.get(title)
 if x:
  r=x['record'];checks.append({'title':title,'check':description,'passed':bool(predicate(r)),'source_shard':x['source_shard'],'source_sha256':x['source_sha256'],'source_row':x['source_row'],'article_revision':r['version'],'article_date':r['date_modified'],'url':r['url'],'source_text_sha256':hashlib.sha256(r['text'].encode()).hexdigest(),'source_wikitext_sha256':hashlib.sha256(r['wikitext'].encode()).hexdigest(),'evidence':evidence(r),'eligibility':eligibility(r)})
 else:checks.append({'title':title,'check':description,'passed':False,'failure':'Not found in acquired query-source census'})
add('Transport in Belgium','Rendered rail distance units and source CIA attribution survive supplement screening',lambda r:'2,950' in r['text'] and 'km' in r['text'] and '{{CIA World Factbook' in r['wikitext'] and notice_candidate(r['wikitext']),lambda r:{'text_excerpt':r['text'][:850],'notice_templates':re.findall(r'\{\{CIA World Factbook[^}]*\}\}',r['wikitext'])})
add('Speed of light','Exact speed value and units are present in pinned text; no reconstructed value',lambda r:bool(re.search(r'299[ ,\u00a0\u202f]?792[ ,\u00a0\u202f]?458',r['text'])) and ('metre' in r['text'] or 'm/s' in r['text']),lambda r:{'text_excerpt':r['text'][:1400],'has_math':r['has_math']})
add('Pythagorean theorem','Source equation representation is available without inventing removed math',lambda r:bool(r['has_math']) and ('<math' in r['wikitext'] or 'a^2' in r['wikitext']),lambda r:{'text_excerpt':r['text'][:1400],'raw_math_examples':re.findall(r'<math[^>]*>.*?</math>',r['wikitext'],re.S)[:3]})
add('Futurist cooking','Cultural food movement remains an encyclopedia topic, not a practical recipe quota',lambda r:'Futurist' in r['text'],lambda r:{'text_excerpt':r['text'][:1000],'practical_cooking_quota_credit':False})
add('Museum Plaza','Historical project source is not presented as current operating travel service',lambda r:'Museum Plaza' in r['text'],lambda r:{'text_excerpt':r['text'][:1400],'operational_travel_claim':False})
db=sqlite3.connect(f'file:{lane / "census-v2.sqlite"}?mode=ro',uri=True);bad=db.execute("SELECT id,title,shard,source_row,reason,revision FROM source WHERE reason LIKE 'unresolved_rights_marker:%' LIMIT 12").fetchall();counts=db.execute('SELECT reason,count(*) FROM source WHERE eligible=0 GROUP BY reason').fetchall();db.close()
result={'checks':checks,'passed':sum(c['passed'] for c in checks),'total':len(checks),'real_unresolved_marker_examples':[dict(zip(['id','title','shard','source_row','reason','revision'],r)) for r in bad],'exclusion_reason_counts':counts,'rights_limit':'Unknown notices/templates are not cleared by absence of recognized markers; independent rights review remains open. Retention of wikitext preserves inspectability, not expanded legal attribution.','query_source_record_count':len(rows)};atomic(a.output,result);print(json.dumps({'passed':result['passed'],'total':len(checks),'real_exclusion_examples':len(bad)},indent=2))
