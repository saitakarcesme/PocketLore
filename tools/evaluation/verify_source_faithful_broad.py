#!/usr/bin/env python3
"""Source/rights gate, reusing exact Android behavior only while candidate hashes match."""
from pathlib import Path
import copy,json,sqlite3
import verify_broad_reference as broad
ROOT=Path(__file__).resolve().parents[2];E=ROOT/'docs/evidence/source-faithful-broad'
def check_cases(cases,db,dispositions):
 rows={r['id']:r for r in dispositions['documents']}
 for case in cases['cases']:
  r=rows[case['id']];d=db.execute('SELECT body,provenance FROM documents WHERE id=?',(case['id'],)).fetchone()
  broad.require(d is not None and r['disposition']=='admitted','Counterexample source absent')
  broad.require(r['revision']==case['revision'] and r['html_sha256']==case['html_sha256'],'Counterexample pin drift')
  broad.require(all(t in d[0] for t in case['required_source_substrings']),'Formula/unit/history fidelity lost')
  broad.require(r['semantic_judgment']['area'] not in case['forbidden_quota_areas'],'Unsuitable semantic quota credited')
  for n in r['source_notices']:broad.require(n['text'] in d[1] and all(u in d[1] for u in n['links']),'Third-party attribution lost')
def main():
 broad.main() # All original breadth, source-byte, rights, import/restart/cancel and identity gates.
 producer=broad.module('source_dispositions',ROOT/'tools/packs/broad/repair/dispositions.py')
 saved=json.loads((E/'dispositions.json').read_text());broad.require(saved==producer.records(),'Disposition drift')
 cases=json.loads((E/'counterexamples.json').read_text())
 db=sqlite3.connect('file:'+str(broad.PACKDIR/'index.sqlite')+'?mode=ro',uri=True);check_cases(cases,db,saved)
 negatives=[]
 bad=copy.deepcopy(saved);next(r for r in bad['documents'] if r['id']=='4429510')['semantic_judgment']['area']='practical reference'
 negatives.append(broad.rejected(lambda:check_cases(cases,db,bad),'cultural-movement-as-practical-guidance'))
 bad=copy.deepcopy(saved);next(r for r in bad['documents'] if r['id']=='4057884')['semantic_judgment']['area']='travel'
 negatives.append(broad.rejected(lambda:check_cases(cases,db,bad),'abandoned-project-as-travel-quota'))
 # Mutate a real database copy in memory, not the sealed artifact.
 memory=sqlite3.connect(':memory:');db.backup(memory)
 memory.execute("UPDATE documents SET body=replace(body,'2,950 km (1,830 mi)','2,950') WHERE id='3546'")
 negatives.append(broad.rejected(lambda:check_cases(cases,memory,saved),'lost-transport-units'))
 memory.execute("UPDATE documents SET provenance='' WHERE id='3546'")
 transport={'cases':[c for c in cases['cases'] if c['id']=='3546']};memory.execute('UPDATE documents SET body=? WHERE id=?',(db.execute("SELECT body FROM documents WHERE id='3546'").fetchone()[0],'3546'))
 negatives.append(broad.rejected(lambda:check_cases(transport,memory,saved),'lost-incorporated-source-attribution'))
 print(json.dumps({'task':'211','status':'PASS','dispositions':len(saved['documents']),'counterexamples':len(cases['cases']),'negative_regressions':negatives,'android_evidence':'Exact unchanged task210 repair APK/edition/import/restart receipts revalidated; no new emulator run claimed','limitations':'Builder source/rights judgments need independent review; no generated-answer, publication or phone acceptance'},indent=2))
if __name__=='__main__':main()
