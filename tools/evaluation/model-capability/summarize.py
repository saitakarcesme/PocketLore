#!/usr/bin/env python3
"""Aggregate explicit builder ratings, never infer factual support from words."""
from pathlib import Path
import collections,hashlib,json,math
from builder_notes import NOTES
R=Path(__file__).resolve().parents[3];E=R/'docs/evidence/model-capability'
def main():
 spec=json.loads((R/'tools/evaluation/model-capability/protocol.json').read_text());reviews=[];summary={}
 for model in [e['id'] for e in json.loads((R/'tools/evaluation/model-capability/execution-v2.json').read_text())['models']]:
  rows=[]
  for c in spec['cases']:
   p=E/'run'/model/(c['id']+'.json');r=json.loads(p.read_text());support,complete,useful,note=NOTES[model][int(c['id'][-2:])]
   a={'model':model,'case':c['id'],'raw_support':support,'raw_completeness':complete,'raw_usefulness':useful,'published_support':support if r['route']=='GENERATED' else 'withheld','note':note,'run_record_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'answerable':c['answerable'],'production_route':r['route']};reviews.append(a);rows.append((r,a))
  percentile=lambda key,p:sorted(r[key] for r,a in rows)[math.ceil(p*len(rows))-1]
  summary[model]={'routes':dict(collections.Counter(r['route'] for r,a in rows)), 'controller_invoked':sum(r['controller_invoked'] for r,a in rows),'diagnostic_only':sum(r['diagnostic_only'] for r,a in rows),'raw_support_all24':dict(collections.Counter(a['raw_support'] for r,a in rows)), 'raw_complete_useful_answerable':sum(a['answerable'] and a['raw_support']=='supported' and a['raw_completeness']=='full' and a['raw_usefulness']=='useful' for r,a in rows),'published_complete_useful_answerable':sum(a['answerable'] and a['production_route']=='GENERATED' and a['raw_support']=='supported' and a['raw_completeness']=='full' and a['raw_usefulness']=='useful' for r,a in rows),'unsupported_published':sum(a['published_support']=='unsupported' for r,a in rows),'absent_published':sum(not a['answerable'] and r['route']=='GENERATED' for r,a in rows),'raw_appropriate_absent_refusal':sum(not a['answerable'] and a['raw_support']=='withheld' and a['raw_completeness']=='full' for r,a in rows),'first_token_ms_p50':percentile('first_token_ms',.5),'first_token_ms_p95':percentile('first_token_ms',.95),'total_ms_p50':percentile('generation_total_ms',.5),'total_ms_p95':percentile('generation_total_ms',.95),'load_ms':json.loads((E/'run'/model/'load.json').read_text())['load_ms']}
 (E/'builder-assessments.json').write_text(json.dumps({'classification':'Builder assessments only; independent source review pending','rows':reviews},indent=2)+'\n')
 (E/'summary.json').write_text(json.dumps({'classification':'Builder-scored development, not acceptance','percentile_definition':'Nearest rank: sorted observations at ceil(p*n)-1; all 24 generation calls including diagnostic calls; load reported separately','models':summary},indent=2)+'\n')
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
