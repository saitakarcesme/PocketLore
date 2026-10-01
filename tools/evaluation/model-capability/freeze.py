"""One-time public development fixture creation; no model output is consulted."""
from pathlib import Path
import csv, io, json, zipfile, hashlib
R=Path(__file__).resolve().parents[3]
packs=['downloads/packs/english-reference.plpack','downloads/science/science-supplement-2026-10-01-v1.plpack']
rows={}
for p in packs:
 for r in csv.reader(io.StringIO(zipfile.ZipFile(R/p).read('passages.tsv').decode()),delimiter='\t'):
  rows[r[0]]=dict(zip(['id','title','url','date','license','text'],r))
def find(prefix):return next(k for k in rows if k.startswith(prefix))
# Expectations are human-authored evaluation criteria, never prompts or corpus facts.
cases=[
('geology','explanation','Why does stress at a fault cause earthquake shaking?', ['science-earthquakes-870'], 'Stress overcomes friction; sudden slip releases energy waves through the crust causing shaking.'),
('geology','comparison','Compare magma and lava.', ['science-magma-'], 'Molten rock underground is magma; after breaking through the surface it is lava.'),
('geology','multisource','How can magma rise and build volcanic terrain?', ['science-volcanoes-ac98','science-volcanoes-fdd'], 'Buoyancy and gas pressure drive magma upward; accumulation of erupted lava builds volcanic terrain; eruption is conditional.'),
('geology','contradiction','All parts of the San Andreas Fault creep constantly, so strain cannot build up for centuries. Is that supported?', ['science-earthquakes-a2'], 'Reject premise: some parts creep; other parts can accumulate strain for hundreds of years.'),
('genetics','explanation','Why is DNA wrapped around histones?', ['science-chromosomes-1c'], 'Packaging allows long DNA to fit inside cells.'),
('genetics','multisource','How do DNA instructions and chromosomes contribute to inheritance?', ['science-dna-021','science-chromosomes-bd'], 'DNA carries biological instructions passed to offspring; chromosomes consist of protein and one DNA molecule. Avoid unsupported inheritance mechanisms.'),
('genetics','qualifier','Does chromosome copying always distribute DNA accurately?', ['science-chromosomes-ae'], 'Vast majority of cell divisions copy and distribute accurately, but rare mistakes occur; not always.'),
('genetics','absent','How many chromosomes does a domestic cat have?', ['science-chromosomes-bd'], 'Withhold the number: no cat chromosome count in evidence.'),
('geomagnetism','explanation','What sustains the magnetic field generated in the outer core?', ['science-magnetic-core-'], 'Conducting iron motion induces currents and magnetic field feedback, sustained while sufficient convection energy exists.'),
('geomagnetism','comparison','Compare magnetic storms and magnetic reversals.', ['science-magnetic-storms-3','science-magnetic-reversals-fc'], 'Storms are rapid field variation lasting hours to days; reversals take hundreds to thousands of years, with one possible one-year research exception.'),
('geomagnetism','contradiction','Do magnetic reversals occur on a regular schedule every 780,000 years?', ['science-magnetic-reversals-b1'], 'No apparent periodicity; 780,000 years is time since last reversal, not a repeat interval.'),
('geomagnetism','absent','What is the exact date of the next magnetic reversal?', ['science-magnetic-reversals-b1'], 'No exact prediction is supported; random with no apparent periodicity.'),
('civics','comparison','Compare the rights concerning searches and criminal trials in these excerpts.', ['bill-of-rights-07','bill-of-rights-508'], 'Searches: protection against unreasonable searches and warrant probable cause/specificity; trials: speedy public impartial jury plus defense rights. Keep subjects separate.'),
('civics','qualifier','Under what conditions may soldiers be quartered in a house?', ['bill-of-rights-970'], 'In peace requires owner consent; in war in manner prescribed by law. Do not omit wartime qualification.'),
('civics','contradiction','Does listing certain rights deny other rights retained by the people?', ['bill-of-rights-4b'], 'No; enumeration must not be construed to deny or disparage other retained rights.'),
('civics','absent','What prison sentence applies today to an unreasonable search?', ['bill-of-rights-07'], 'No current criminal penalty in supplied historical text; withhold.'),
('outdoor','explanation','Why are headlamps recommended for lighting at night?', ['essentials-e772'], 'Hands-free lighting; can find way out or signal for help; extra batteries useful.'),
('outdoor','multisource','How do extra food and emergency shelter help if trip plans change?', ['essentials-18','essentials-ba'], 'Extra day food helps unexpected changes and maintains energy; shelter protects from severe weather/exposure. No guarantee of survival.'),
('outdoor','qualifier','What should determine the extra clothing packed for sudden weather changes?', ['essentials-9a'], 'Most extreme conditions one could encounter; examples raincoat/jacket/hat/gloves; bright clothing helps visibility for rescue.'),
('outdoor','absent','Which brand of headlamp has the longest battery life?', ['essentials-e772'], 'No brands or comparative battery durations supplied; withhold.'),
('travel','comparison','Compare camping access from Yosemite Valley and Tuolumne Meadows.', ['yosemite-c075','yosemite-05'], 'Both at least four miles before camping; Valley minimum 2500-foot gain and mostly no-camping zone; Tuolumne cooler high country. Do not transfer gain to Tuolumne.'),
('travel','multisource','How do snow and river crossings affect planning a Yellowstone hike?', ['yellowstone-241','yellowstone-240'], 'Snow persists late May/early June, some passes late July; late spring rivers cold/deep/swift; map lacks current status and current conditions need checking. No live assessment.'),
('travel','contradiction','Will Yosemite rangers plan my wilderness trip for me?', ['yosemite-6d'], 'No; general guidance only, traveler plans based on interests/timeframe/abilities.'),
('travel','absent','Is the Yellowstone trail I want open and safe today?', ['yellowstone-240','yellowstone-c7'], 'No live trail status or safety guarantee. Supplied precautions do not establish current availability.')]
out=[]
for i,(topic,kind,q,ids,expected) in enumerate(cases,1):
 out.append({'id':f'cap-{i:02}','topic':topic,'type':kind,'question':q,'sources':[rows[find(p)] for p in ids],'expectation':expected,'answerable':kind!='absent'})
spec={'version':1,'classification':'New public development only; oracle supplied evidence, not retrieval benchmark','cases':out,'packs':{p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in packs},'execution':{'models':['baseline','qwen25-1.5b','qwen3-1.7b'],'order':'model then case; one run per pair; no retries or seed search','context_tokens':2048,'output_tokens':256,'threads':2,'sampling':'Production: greedy Qwen2.5; Qwen3 non-thinking t=.7 top-k=20 top-p=.8 presence=1.5/256 seed=42. Not sampling-matched; same budget and production policy.','controller':'Unmodified AnswerEngine with pinned evidence; no retrieval. For controller-blocked cases run diagnostic generateClaims on same selected evidence and production template; never publish it as product output.','timeout_seconds_per_model':1800,'assessment':'Builder reads each full output against excerpts and required relations. Support: supported/unsupported/withheld; completeness: full/partial/none; usefulness: useful/limited/not-useful. No automated lexical entailment scoring.','selection':'Candidate must improve supported complete useful GENERATED count and have no increase in unsupported published answers or unsafe absent-case publication; otherwise no replacement. Raw diagnostic gains motivate separate architecture task only.'}}
p=R/'tools/evaluation/model-capability/protocol.json'
assert not p.exists(),'Frozen fixture exists; do not overwrite'
p.write_text(json.dumps(spec,indent=2)+'\n')
