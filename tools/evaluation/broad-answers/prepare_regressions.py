#!/usr/bin/env python3
from pathlib import Path
import json
R=Path(__file__).resolve().parents[3]
for row in json.loads((R/'docs/evidence/broad-answers/shared-property-regressions.json').read_text())['cases']:
 p=R/'downloads/broad-answers/regressions'/row['id'];p.mkdir(parents=True,exist_ok=True)
 for key,value in [('question',row['question']),('draft',row['resolved_raw'])]:(p/key).write_text(value)
 for i,source in enumerate(row['selected']):
  (p/('title'+str(i))).write_text(source['title']);(p/('excerpt'+str(i))).write_text(source['excerpt'])
