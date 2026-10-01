#!/usr/bin/env python3
"""Compare real frozen-query source records with installed lazy-reader content."""
import argparse,hashlib,json,pathlib,re,time
from acquire import atomic,digest
from build import lead
from reader import Reader
p=argparse.ArgumentParser();p.add_argument('lane');p.add_argument('edition');p.add_argument('output');a=p.parse_args();lane=pathlib.Path(a.lane);reader=Reader(lane/a.edition);cases=[];start=time.monotonic();loaded={}
for source_file in sorted((lane/'receipts/selected-query-sources').glob('*.json')):
 source=json.loads(source_file.read_text())
 if 'record' not in source:continue
 r=source['record'];found=reader.source(r['title']);case={'title':r['title'],'source_shard':source['source_shard'],'source_row':source['source_row'],'source_parquet_sha256':source['source_sha256'],'source_record_receipt_sha256':digest(source_file),'present':bool(found)}
 if found:
  s,row,payload=found;loaded[r['title']]=(row,payload);ranges=payload['wikitext_ranges'];valid_ranges=all(0<=b<e<=len(r['wikitext']) for b,e in ranges) and all(ranges[i-1][1]<=ranges[i][0] for i in range(1,len(ranges)));expected_text=r['text'] if row['tier']=='full' else lead(r['text']);math=re.findall(r'<(?:math|chem)\b[^>]*>.*?</(?:math|chem)\s*>',r['wikitext'],re.I|re.S)
  checks={'identity':row['id']==r['page_id'] and row['revision']==r['version'] and row['modified']==r['date_modified'] and row['url']==r['url'] and row['source_row']==source['source_row'] and reader.packs[s].name+'.parquet'==source['source_shard'],'retained_text_exact':payload['text']==expected_text,'original_text_hash':payload['source_text_sha256']==hashlib.sha256(r['text'].encode()).hexdigest(),'original_wikitext_hash':payload['source_wikitext_sha256']==hashlib.sha256(r['wikitext'].encode()).hexdigest(),'range_bounds':valid_ranges,'retained_ranges_exact':valid_ranges and payload['wikitext']=='\n\n'.join(r['wikitext'][b:e] for b,e in ranges),'structured_infoboxes_exact':payload['infoboxes']==r.get('infoboxes'),'all_source_math_tags_retained':all(m in payload['wikitext'] for m in math)}
  case.update({'tier':row['tier'],'views':row['views'],'revision':row['revision'],'date':row['modified'],'scope':payload['wikitext_scope'],'source_math_tags':len(math),'checks':checks,'passed':all(checks.values())})
 else:case['passed']=False
 cases.append(case)
checks=[]
for title,field,needles in [('Transport in Belgium','text',['2,950','km']),('Transport in Belgium','wikitext',['{{CIA World Factbook|year=2009}}']),('Speed of light','text',['299,792,458','metres per second']),('Pythagorean theorem','wikitext',['a^2 + b^2 = c^2']),('(+)-Menthofuran synthase','text',['NADPH + H+ + O2','rightleftharpoons'])]:
 found=loaded.get(title)
 if not found:
  extra=reader.source(title)
  if extra:found=(extra[1],extra[2])
 checks.append({'title':title,'field':field,'needles':needles,'revision':found[0]['revision'] if found else None,'source_row':found[0]['source_row'] if found else None,'original_text_sha256':found[1]['source_text_sha256'] if found else None,'passed':bool(found) and all(n in found[1][field] for n in needles)})
exclusions=[]
for example in json.loads(pathlib.Path('docs/evidence/scale/wiki/counterexample-audit.json').read_text())['real_unresolved_marker_examples']:
 index=next(i for i,p in enumerate(reader.packs) if p.name==pathlib.Path(example['shard']).stem);row=reader.dbs[index].execute('SELECT reason FROM exclusions WHERE source_row=?',(example['source_row'],)).fetchone();exclusions.append({**example,'installed_exclusion':row[0] if row else None,'passed':bool(row) and row[0]==example['reason']})
# Missing frozen title stays a missing locator; direct alias discovery does not rewrite the probe.
missing=[]
for title in sorted({t for q in json.loads(pathlib.Path('docs/evidence/scale/wiki/queries-v1.json').read_text())['queries'] for t in q['expected_titles']}):
 if title not in loaded:
  aliases=reader.alias_rows(title)
  missing.append({'frozen_title':title,'direct_alias_targets':[list(x) for x in aliases],'status':'Strict source locator missing; frozen expectation unchanged'})
result={'passed_available_source_fidelity':all(c['passed'] for c in cases) and all(c['passed'] for c in checks) and all(c['passed'] for c in exclusions),'available_source_cases':len(cases),'cases':cases,'counterexamples':checks,'unresolved_marker_exclusions':exclusions,'missing_frozen_locators':missing,'seconds':time.monotonic()-start,'limits':['Builder source-fidelity checks, not human usefulness or rights acceptance','Unavailable frozen locator remains a failure, not silently corrected','Full/lead fidelity tested against 67 acquired canonical source records, not exhaustive source re-extraction']};atomic(a.output,result);reader.close();print(json.dumps({k:v for k,v in result.items() if k not in ['cases','unresolved_marker_exclusions']},indent=2));raise SystemExit(0 if result['passed_available_source_fidelity'] else 1)
