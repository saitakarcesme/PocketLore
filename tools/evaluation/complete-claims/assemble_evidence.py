#!/usr/bin/env python3
"""Assemble preserved runs and explicitly builder-authored source assessments (not a grader)."""
from pathlib import Path
import json,hashlib,shutil,collections
R=Path(__file__).resolve().parents[3];O=R/'docs/evidence/complete-claims';O.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
for stage,dirname in [('before','before-20261001T054140Z'),('after','after-20261001T054408Z')]:
 source=R/'downloads/complete-claims'/dirname;dest=O/stage;dest.mkdir(exist_ok=True)
 for f in ['manifest.json','stdout.txt','stderr.txt']:shutil.copyfile(source/f,dest/f)
 shutil.copytree(source/'results',dest/'results',dirs_exist_ok=True)
for f in ['android-build-failed-java-api.log','android-build.log','unit.log']:shutil.copyfile(R/'downloads/complete-claims'/f,O/f)
old=json.loads((R/'tools/evaluation/model-capability/protocol.json').read_text())['cases'];new=json.loads((R/'tools/evaluation/complete-claims/protocol.json').read_text())['cases']
# Each note follows review against the actual selected cited excerpts, not citation shape or overlap.
notes=[
('supported','partial','limited','Moving plates and friction are supported, but the explanation omits stress overcoming friction, sudden slip and energy waves.'),
('supported','full','useful','One complete comparison supplies both underground magma and surface lava, without the old unsupported extra comparison line.'),
('unsupported','full','limited','The second line cites the terrain/storage excerpt for upward movement and crust weakness established only in the other excerpt; this claim-to-source link is wrong.'),
('supported','partial','not-useful','Plate motion rate is supported but fails to reject the all-parts constant-creep premise.'),
('supported','full','useful','Packaging allows long DNA to fit in cells, directly explaining histones.'),
('supported','partial','limited','Defines DNA but omits inheritance and chromosome composition.'),
('supported','partial','limited','Rare mistakes and intact distribution are supported, but the answer has an unclosed quotation and omits the vast-majority qualifier.'),
('unsupported','none','not-useful','No cat count exists in the source; 42 is unsupported. Diagnostic only and withheld.'),
('supported','partial','limited','Conducting iron and generator analogy are supported, but feedback and sufficient convection energy are missing.'),
('supported','partial','limited','Storm definition is correct; reversal evidence was dropped by the unchanged selector and no comparison results.'),
('supported','partial','not-useful','Occasional reversal is consistent with the source, but a question followed by Yes does not correct the false regular interval premise.'),
('supported','full','useful','No date is invented; appropriately acknowledges unknown exact timing from the supplied nonperiodic history.'),
('supported','partial','limited','Complete long comparison retains correct subjects but omits warrant probable cause/specificity, impartial jury and defense rights.'),
('supported','full','useful','Preserves both peace/owner consent and wartime law conditions.'),
('supported','full','useful','Faithful retained-rights statement answers the premise.'),
('supported','partial','not-useful','Historical search-rights quote does not give or explicitly refuse the requested current prison penalty; safely withheld.'),
('supported','full','useful','Hands-free operation directly answers why headlamps are recommended, as in the prior rubric.'),
('supported','partial','not-useful','Heading plus generic preparation advice omits extra food benefits and shelter entirely.'),
('supported','full','useful','Most extreme possible conditions directly answers the selection criterion, using the same prior rubric.'),
('supported','partial','not-useful','Headlamp recommendation supplies no brand or battery comparison; withheld.'),
('supported','partial','limited','Complete supported comparison preserves Valley-only gain and both distances, but omits no-camping-zone and high-country conditions in the frozen expectation.'),
('supported','partial','limited','Generic planning statement omits snow dates, dangerous fords and need for current conditions.'),
('supported','full','useful','Despite a redundant source heading, the complete clause directly rejects ranger trip planning, using the prior rubric.'),
('supported','partial','not-useful','No live claim is invented, but metadata and mangled URLs contaminate prose; precautions are not a current status answer.')]
newnotes=[
('supported','partial','limited','Only states a two-step process; neither transcription to mRNA nor translation to amino-acid order is explained.'),
('supported','partial','limited','Valid protein-production paraphrase is withheld by the terminal-word heuristic; omits one percent and detailed regulation qualifiers.'),
('supported','partial','limited','Vent/storage connection is supported but fresh replenishment explaining repeated eruption remains implicit.'),
('supported','full','useful','Preserves the can qualifier and direct Earth/Sun magnetic-field connection condition; diagnostic only.'),
('supported','partial','not-useful','Spring/fall crowding is in the Hetch Hetchy excerpt, but this does not compare late-summer heat/dryness with Wawona. Wrong question answered; jointly citing Wawona adds no support.'),
('supported','partial','limited','Generic medical resources paraphrase is withheld by the ending heuristic; omits repair-kit function and concrete preparation.'),
('supported','full','useful','Faithful historical just-compensation protection, without claiming current legal procedure; diagnostic only.'),
('supported','partial','limited','Four complete supported clauses connect vents, tephra and wind-borne ash, but omit the frozen smallest-particle/global-distance distinction; diagnostic only.')]
before_notes=[newnotes[0],('supported','partial','limited','Correct genes/outside-genes regulation distinction, but omits the frozen about-one-percent detail.'),newnotes[2],newnotes[3],('supported','full','useful','Both late-summer conditions and the can qualifier are preserved.'),('supported','partial','not-useful','Tautological packing advice does not explain medical and repair functions.'),newnotes[6],('supported','partial','not-useful','Defines vents and says eruption varies, without wind or ash-fall mechanism.')]
rows=[]
for stage,cases,ratings in [('before',new,before_notes),('after',old+new,notes+newnotes)]:
 for c,rating in zip(cases,ratings):
  p=O/stage/'results'/(c['id']+'.json');d=json.loads(p.read_text());support,complete,useful,note=rating
  rows.append(dict(stage=stage,case=c['id'],answerable=c['answerable'],route=d['route'],raw_support=support,raw_completeness=complete,raw_usefulness=useful,published_support=support if d['route']=='GENERATED' else 'withheld',published_fully_useful=d['route']=='GENERATED' and (support,complete,useful)==('supported','full','useful'),note=note,record_sha256=sha(p)))
prior=json.loads((R/'docs/evidence/model-capability/builder-assessments.json').read_text())
for r in prior['rows']:
 if r['model']=='qwen3-1.7b':
  p=R/'docs/evidence/model-capability/run/qwen3-1.7b'/(r['case']+'.json');d=json.loads(p.read_text());rows.append(dict(stage='before',case=r['case'],answerable=r['answerable'],route=d['route'],raw_support=r['raw_support'],raw_completeness=r['raw_completeness'],raw_usefulness=r['raw_usefulness'],published_support=r['published_support'],published_fully_useful=d['route']=='GENERATED' and (r['raw_support'],r['raw_completeness'],r['raw_usefulness'])==('supported','full','useful'),note='Unchanged task190 builder assessment: '+r['note'],record_sha256=sha(p)))
write(O/'builder-assessments.json',{'classification':'Builder source assessments only; independent source review pending. Full means the requested central answer using the prior rubric; completeness is not grammatical well-formedness.','rows':rows})
summary={}
for stage in ['before','after']:
 for suite in ['prior24','new8']:
  rs=[r for r in rows if r['stage']==stage and r['case'].startswith('cap-' if suite=='prior24' else 'new-')];summary[stage+'_'+suite]={'routes':dict(collections.Counter(r['route'] for r in rs)),'answerable':sum(r['answerable'] for r in rs),'fully_useful_supported_published':sum(r['published_fully_useful'] for r in rs),'unsupported_published':sum(r['published_support']=='unsupported' for r in rs),'absent_withheld':sum(not r['answerable'] and r['route']=='ABSTAINED' for r in rs)}
write(O/'summary.json',summary)
review=[]
for r in rows:
 c=next(c for c in old+new if c['id']==r['case']);p=(R/'docs/evidence/model-capability/run/qwen3-1.7b' if r['stage']=='before' and r['case'].startswith('cap-') else O/r['stage']/'results')/(r['case']+'.json');d=json.loads(p.read_text())
 review.append({'stage':r['stage'],'case':c['id'],'question':c['question'],'expectation':c['expectation'],'sources':c['sources'],'actual_prompt':d['prompt'],'resolved_raw':d['resolved_raw'],'published_text':d['text'],'route':d['route'],'record_sha256':sha(p)})
write(O/'source-review-inputs.json',{'classification':'Inputs for independent source review; no independent verdict supplied by builder','rows':review})
print(json.dumps(summary,indent=2))
