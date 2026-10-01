"""Explicit builder judgments from reading raw outputs and frozen sources.
This is a review record, not an automatic factual-entailment classifier.
"""
NOTES={
'baseline':{
1:('withheld','none','not-useful','Unnecessary refusal: the retained USGS excerpt directly explains stress, friction, slip and waves.'),
2:('supported','full','not-useful','Underground/surface distinction is present, but repeated question text and contradictory Insufficient evidence wording make this incoherent as an answer; controller rejects sentence citation structure.'),
3:('supported','partial','limited','Correct lighter-rock fragment; omits gas pressure, ascent and accumulation of erupted lava requested across the two sources.'),
4:('supported','none','not-useful','Plate direction and speed are supported but do not address the false all-parts-creep premise or centuries of strain accumulation.'),
5:('withheld','none','not-useful','Unnecessary refusal despite explicit packaging/fit explanation.'),
6:('withheld','none','not-useful','No inheritance explanation despite supplied DNA and chromosome descriptions.'),
7:('withheld','none','not-useful','Fails to explain vast-majority accuracy and rare mistakes.'),
8:('withheld','full','useful','Correctly withholds cat chromosome count absent from evidence.'),
9:('withheld','none','not-useful','Refuses supported core-current feedback and energy condition.'),
10:('unsupported','none','not-useful','Transfers rapid storm changes to reversals, whose excerpt the production selector dropped. Only storm evidence reached generation; no basis for the reversal assertion.'),
11:('unsupported','none','not-useful','Leading Yes affirms the requested regular schedule; occasional reversals alone do not establish a 780000-year interval and source explicitly says random.'),
12:('unsupported','none','not-useful','Invents next reversal around 780000 years from now by reversing the past-event date; no future estimate is supplied.'),
13:('supported','partial','not-useful','Correct search/trial fragments, but both lines terminate mid-clause (O and in) at the grammar bound; no usable complete comparison.'),
14:('withheld','none','not-useful','Unnecessary refusal; excerpt distinguishes peacetime consent from wartime law.'),
15:('supported','partial','limited','Accurately quotes the retained-rights rule but leaves its explanatory conclusion unfinished; the quoted rule does address the premise.'),
16:('withheld','full','useful','Correctly refuses current prison penalty absent from the historical search-rights excerpt.'),
17:('withheld','none','not-useful','Unnecessary refusal despite explicit hands-free recommendation.'),
18:('withheld','none','not-useful','No synthesis of extra food and emergency shelter despite both excerpts.'),
19:('withheld','none','not-useful','Refuses supported extreme-weather clothing guidance.'),
20:('supported','none','not-useful','Generic lighting information has no brand or battery comparison and does not explicitly acknowledge missing evidence.'),
21:('unsupported','none','not-useful','Transfers Valley-specific 2500-foot elevation gain and most-crowded status to Tuolumne; dual citations do not support those relations.'),
22:('withheld','none','not-useful','Refuses snow, river and current-condition planning synthesis despite both sources.'),
},'qwen25-1.5b':{},'qwen3-1.7b':{}}
