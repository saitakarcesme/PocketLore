#!/usr/bin/env python3
"""Freeze new public source-faithful obligations before implementation/generation."""
from pathlib import Path
import sqlite3,json,hashlib
R=Path(__file__).resolve().parents[3];F=Path(__file__).resolve().parent
pairs=[
('computing','Binary search','Binary search tree',
 'Describe how binary search narrows the possible position of a target.',
 'Explain how insertion order can affect the performance of a binary search tree.',
 'State the data organization required by binary search; describe the left/right ordering in a binary search tree.',
 'Describe the worst-case search behavior of binary search; describe the worst-case behavior of an unbalanced binary search tree.',
 'Binary search works without sorting the array first. Is this premise supported? Explain the prerequisite.',
 'What was the measured nanosecond latency of binary search on my laptop this morning?',
 ['Sorted array, compare middle and discard impossible half; repeat until found/empty.','Arbitrary insertion can cause degeneracy; performance depends on height.','Sorted array versus node ordering; do not equate an algorithm with a tree.','Logarithmic comparisons versus possible linear tree worst case.','Reject unsorted premise; array must be sorted.','Absent device measurement; abstain.']),
('gardening','Compost','Vermicompost',
 'Describe what compost is made from and one stated use.',
 'Explain the role of earthworms in producing vermicompost.',
 'Describe ordinary compost production; describe vermicompost production; identify their shared use.',
 'Name the green and brown inputs for composting; describe what vermicast is.',
 'Vermicomposting avoids using worms. Is that claim consistent with the evidence?',
 'How many kilograms of compost are in stock at my nearest garden shop right now?',
 ['Decomposed plant/food waste and organic materials; fertilizer or soil improvement.','Worm decomposition produces vermicast from organic matter.','Decomposition/organic inputs versus worm process; fertilizer/soil conditioner.','Nitrogen-rich greens/carbon-rich woody browns; worm excreta.','Reject worm-free premise using explicit worm process.','Absent current stock/location; abstain.']),
('horticulture','Grafting','Pruning',
 'Identify the scion and rootstock in a grafted plant.',
 'Explain why smaller pruning cuts are generally preferred to large cuts on mature plants.',
 'Describe what grafting joins; describe what pruning removes.',
 'State what must happen to vascular tissues for a graft to succeed; state a reason for pruning unwanted material.',
 'Grafting succeeds even when the vascular tissues never grow together. Does the source support this?',
 'Which grafted tree at my local nursery will be cheapest next Saturday?',
 ['Scion upper, rootstock lower.','Smaller wounds easier to compartmentalize, limiting pathogens/decay; retain general qualifier.','Joining plant tissues versus selective removal of branches/buds/roots.','Vascular tissues grow together; remove diseased/damaged/unwanted parts.','Reject premise: joining requires vascular tissues growing together.','Absent local future price; abstain.']),
('civics','Constitution','Constitutional monarchy',
 'Explain what makes a constitution codified rather than merely written.',
 'Explain whether every constitutional monarch has the same executive powers.',
 'Describe the function of a constitution; explain how it constrains a constitutional monarch.',
 'Distinguish a codified constitution from an uncodified one; describe two ways constitutional monarchs can differ in power.',
 'Every constitutional monarchy gives its monarch no policy-making power. Is this universal claim supported?',
 'What did the constitutional court decide in my pending case today?',
 ['Single comprehensive document versus single/set of written documents.','Powers vary; some largely symbolic, others meaningful formal powers.','Legal/governing principles; monarch bound by established legal limits.','Single comprehensive versus dispersed documents; symbolic versus meaningful powers.','Reject universal no-power claim; some have formal powers.','Absent personal/current legal result; abstain.']),
('geography','Aruba','Andorra',
 'Locate Aruba relative to Venezuela and identify its constitutional relationship.',
 'Explain why describing Andorra as a coastal Caribbean island would be wrong.',
 'Describe Aruba location and physical setting; describe Andorra location and physical setting.',
 'State the area and climate described for Aruba; name the countries bordering Andorra.',
 'Andorra has a Caribbean coastline near Venezuela. Is that description supported?',
 'What is the live waiting time at the Andorra border crossing I will use today?',
 ['Southern Caribbean north of Venezuelan peninsula, constituent country Netherlands kingdom.','Landlocked eastern Pyrenees/Iberian peninsula in Europe, not island.','Caribbean island versus landlocked Pyrenees bordered France/Spain.','179 square km, dry/arid climate; France/Spain.','Reject premise with landlocked European location.','Absent live crossing/current location; abstain.']),
('travel-history','Barcelona','Athens',
 'Identify Barcelona regional capital status and its coastal location.',
 'Explain why Athens is described as historically important to democracy and learning.',
 'Describe the capital status of Barcelona; describe the capital status of Athens.',
 'Describe one historical role of Barcelona in the Crown of Aragon; describe one historical role of classical Athens.',
 'Barcelona is the national capital of Greece. Is that premise supported by these sources?',
 'Give today opening hours and current ticket prices for the Acropolis and a Barcelona museum.',
 ['Catalonia capital, northeastern Spain/Mediterranean coast; not national Spanish capital.','Classical center of democracy, arts, education/philosophy; historical influence.','Regional Catalonia versus national Greece/region Attica.','Economic/administrative Crown of Aragon center versus ancient Greek city-state/intellectual center.','Reject: Athens capital Greece; Barcelona in Spain.','No current hours/prices or named Barcelona museum; abstain.']),
('food-biochemistry','Fermentation','Pasteurization',
 'Describe the role of redox reactions and ATP in fermentation.',
 'Explain why pasteurization should not be described as eliminating every bacterial spore.',
 'Describe the mechanism of fermentation; describe the mechanism and purpose of pasteurization.',
 'Name two industrial fermentation end products; state the usual temperature qualification for pasteurization.',
 'Pasteurization reliably destroys all bacterial spores. Does the cited evidence support this?',
 'What is the verified microbial count in the milk bottle in my refrigerator today?',
 ['Anaerobic metabolism harnesses reactant redox potential to make ATP and organic end products.','Most bacterial spores survive; destroys/deactivates other spoilage/disease contributors.','Anaerobic metabolism versus mild heat for pathogens/shelf life; do not transfer mechanisms.','Ethanol/lactate; usually below100C/212F, not unconditional.','Reject: most spores survive.','Absent lab measurement; abstain.']),
('astronomy-specialist','Apparent magnitude','Amateur astronomy',
 'Explain how the sign and size of apparent magnitude relate to brightness.',
 'Explain how amateur astronomers can contribute to science even when research is not their main goal.',
 'Describe what apparent magnitude measures; describe what amateur astronomy involves.',
 'State the brightness ratio associated with a magnitude difference of one; name two types of observations amateurs can contribute.',
 'A larger apparent magnitude number always means a brighter object. Is that supported?',
 'What is the exact brightness of the unidentified star I am viewing right now?',
 ['Reverse logarithmic scale: brighter means lower number; brightest can negative.','Citizen science monitoring stars/sunspots/occultations or transient discoveries; some, not all.','Brightness affected by luminosity/distance/extinction versus observing/studying/imaging hobby.','About2.512; e.g variable/double stars,sunspots,occultations.','Reject reverse-scale premise.','Absent identified object/live measurement; abstain.'])]
# Up to three real paragraphs per document; these are oracle inputs for a host upper-bound screen.
db=sqlite3.connect('file:'+str(R/'downloads/broad-reference/rendered-v2/index.sqlite')+'?mode=ro',uri=True)
cases=[]
for group,a,b,*rest in pairs:
 questions=rest[:6];expectations=rest[6];sources=[]
 for title in [a,b]:
  d=db.execute('select id,url,date,rights,sha from documents where title=?',(title,)).fetchone()
  for citation,text,h in db.execute('select citation,body,sha from passages where document=? order by pid limit 3',(d[0],)):
   sources.append(dict(id=citation,title=title,url=d[1],date=d[2],license=d[3],source_sha256=d[4],text=text,sha256=h))
 for index,(question,expected) in enumerate(zip(questions,expectations)):
  kinds=['literal','explanation','comparison','multi-part','false-premise','absence']
  cases.append(dict(id='s'+str(len(cases)+1).zfill(2),topic=group,kind=kinds[index],question=question,obligations=[q.strip(' .') for q in question.split(';')],expectation=expected,sources=sources,expected_route='withhold' if index==5 else 'supported correction' if index==4 else 'supported answer'))
assert len(cases)==48
out=F/'protocol.json';assert not out.exists(),'Never overwrite frozen cases'
protocol={'version':1,'population':'New public development cases, not private holdout','evidence_mode':'Identical pinned oracle paragraphs, host upper-bound capability; production retrieval is separately unproven','source_edition_sha256':'b8d18801b099402205938979ab2bb44ee9a316f06f030aab789cf93ba3605012','cases':cases,'assessment':'Inspect every factual clause and every question obligation; structural citations, lexical overlap and model self-evaluation do not establish entailment. Fully useful requires supported, complete, relevant answer; withheld/fallback never count.'}
out.write_text(json.dumps(protocol,indent=2)+'\n');(F/'protocol.sha256').write_text(hashlib.sha256(out.read_bytes()).hexdigest()+'\n')
print('FROZEN',len(cases),'cases')
