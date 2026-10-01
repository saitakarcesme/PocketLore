#!/usr/bin/env python3
"""Prepare public source excerpts for actual builder review; never auto-approve semantics."""
import json,importlib.util
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3];STAGE=ROOT/'downloads/broad-reference/html-v2'
s=importlib.util.spec_from_file_location('edition',P/'build.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
candidates=json.loads((P/'semantic-candidates.json').read_text())['areas'];bytitle={}
for p in (STAGE/'extracted').glob('*.json'):
 d=json.loads(p.read_text())
 if m.eligible(d) is None:bytitle[d['title']]=d
packet={}
for area,titles in candidates.items():
 packet[area]=[]
 for title in titles:
  if title not in bytitle:continue
  d=bytitle[title];packet[area].append({'id':d['id'],'title':title,'html_sha256':d['html_sha256'],'revision':d['revision'],'source_url':'https://en.wikipedia.org/w/index.php?oldid='+str(d['revision']['revid']),'license':'CC-BY-SA-4.0','attribution':title+' — Wikipedia contributors','source_notices':d['attribution_notices'],'support_text':d['blocks'][0]['text'],'section_samples':list(dict.fromkeys(b['section'] for b in d['blocks']))[:15]})
(STAGE/'review-packet.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in packet.items()})
