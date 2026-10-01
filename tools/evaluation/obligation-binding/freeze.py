"""Freeze public source-bound discriminating cases before implementation/inference."""
import copy,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[3]; F=Path(__file__).parent
old=json.loads((R/'tools/evaluation/scale-model-quality/protocol.json').read_text())
new=[
(7,'role-transfer','Is vermicast the material eaten by earthworms or the result of their breakdown of organic matter? Explain the distinction.','Vermicast is earthworm excreta/end-product, not organic input; mixtures contain vermicast.'),
(7,'multi-source','Describe a soil-conditioning use shared by compost and vermicompost; identify which source specifically mentions water-soluble nutrients.','Both used as soil conditioners; water-soluble nutrients specifically vermicompost, not transferred to compost.'),
(13,'condition','Does the wound-compartmentalization explanation justify every removal of plant material, or specifically the preference for smaller cuts?','Specific smaller-cut benefit, not general reason for every pruning operation.'),
(13,'comparison','Compare a graft scion with its rootstock; explain the tissue condition required for the joining to succeed.','Scion upper part, rootstock lower; vascular tissues must grow together.'),
(19,'false-premise','An uncodified constitution cannot contain written legal documents. Explain whether the United Kingdom example supports this claim.','False; UK uncodified but written acts, cases and treaties; codified single comprehensive document.'),
(19,'qualifier','Does being a constitutional monarchy guarantee democracy and a powerless monarch? Explain both limits.','No; some not democratic; powers vary from almost none to substantial discretionary/formal powers.'),
(31,'temporal','Did Barcelona first become capital of the Principality of Catalonia after joining Aragon, or did that role continue?','Continued; must not change continued to began/become following joining.'),
(31,'scope','Which Barcelona origin statement is qualified as tradition; identify a classical Athens role without transferring that qualifier.','Phoenician/Carthaginian founding traditional; Athens democracy/arts/education/philosophy, not only according to tradition.'),
(37,'multi-source','Name the industrial fermentation products ethanol and lactate; explain why pasteurization is not a guarantee that all bacterial spores are destroyed.','Fermentation industrial ethanol/lactate from exact paragraph; most spores survive pasteurization.'),
(43,'formula','Is the brightness ratio for a one-magnitude difference the square root or fifth root of 100, and approximately what is it?','Fifth root 100 about2.512, not square root. Formula brackets must never become source IDs.'),
(43,'comparison','Compare magnitude 2.0 and 3.0 stars in brightness; explain whether a negative magnitude necessarily means fainter light.','Magnitude2.0 is2.512times3.0; negative belongs brightest, lower number brighter.'),
(31,'absent','What are the confirmed accessible entrance and live queue time at the Athens museum I intend to visit tomorrow?','No venue identified/accessibility or live queue data; withhold, no invented live availability.')]
cases=[]
for i,(n,kind,q,e) in enumerate(new,1):
 c=copy.deepcopy(old['cases'][n-1]);c.update(id='n%02d'%i,kind=kind,question=q,obligations=[x.strip().rstrip('.') for x in q.split(';')],expectation=e,expected_route='withhold absent evidence' if kind=='absent' else 'supported answer');cases.append(c)
p={'version':1,'task220_protocol_sha256':hashlib.sha256((R/'tools/evaluation/scale-model-quality/protocol.json').read_bytes()).hexdigest(),'source_edition_sha256':old['source_edition_sha256'],'cases':cases,'assessment':'Every claim compared with exact cited sentence spans by builder; independent review pending. No overlap/exact-quote entailment shortcut.'}
(F/'new-cases.json').write_text(json.dumps(p,indent=2)+'\n')
(F/'new-cases.sha256').write_text(hashlib.sha256((F/'new-cases.json').read_bytes()).hexdigest()+'\n')
