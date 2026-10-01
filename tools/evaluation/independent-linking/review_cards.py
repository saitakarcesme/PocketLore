"""Source-review cards, not automatic semantic labels."""
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[3];E=R/'docs/evidence/independent-linking';v=json.loads(Path(sys.argv[1]).read_text());old=R/'docs/evidence/obligation-binding'
for case in v:
 if case['route']!='SCREEN_ELIGIBLE':continue
 print('\n###',case['id'],case['question']);print(case['rendered'])
 for i,c in enumerate(case['claims']):
  print('Claim',i+1,'subject',c['subject'],'qualifier',c['qualifier'])
  for ref in c['references']:print(ref['label'],ref['passage'],ref['text'])
