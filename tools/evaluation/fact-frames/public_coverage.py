"""Coverage denominators from frozen public fixtures, not inferred semantic truth."""
def measure(values, review, probes):
 byid={v['id']:v for v in values};groups={}
 for prefix,name,total in [('s','old',48),('n','previous_new',12),('l','independent_new',16),('f','frame_new',20)]:
  rows=[v for v in values if v['id'].startswith(prefix)]
  assert len(rows)==total
  eligible=[v for v in rows if v['route']=='SCREEN_ELIGIBLE']
  supported=sum(review['cases'][v['id']]['supported'] is True for v in eligible)
  complete=sum(review['cases'][v['id']]['complete'] is True for v in eligible)
  useful=sum(all(review['cases'][v['id']][k] is True for k in ['supported','complete','useful']) for v in eligible)
  groups[name]={'questions':total,'eligible':len(eligible),'supported_eligible':supported,'complete_eligible':complete,'useful_eligible':useful,'withheld':total-len(eligible),'eligible_support_precision':supported/len(eligible) if eligible else None,'useful_question_coverage':useful/total}
 for prefix,name,fixtures in probes:
  positive=sum(c['expected_probe_supported'] for c in fixtures);false_rejections=0;negative_eligible=0;eligible=0
  for c in fixtures:
   v=byid[prefix+c['id'][1:]];admitted=v['route']=='SCREEN_ELIGIBLE';eligible+=admitted
   false_rejections+=c['expected_probe_supported'] and not admitted
   negative_eligible+=not c['expected_probe_supported'] and admitted
  groups[name]={'probes':len(fixtures),'positive_probes':positive,'eligible':eligible,'positive_probe_rejections':false_rejections,'negative_probe_admissions':negative_eligible}
 return {'assessment':'Builder source judgments; public development only. Withholding is not a new factual judgment. Probe expectations were frozen; wrapper conflicts do not silently change their labels.','groups':groups}
