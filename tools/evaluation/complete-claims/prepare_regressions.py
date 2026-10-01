from pathlib import Path
import json,base64
R=Path(__file__).resolve().parents[3];out=R/'downloads/complete-claims/regressions';out.mkdir(parents=True,exist_ok=True)
cs={c['id']:c for c in json.loads((R/'tools/evaluation/model-capability/protocol.json').read_text())['cases']};enc=lambda s:base64.b64encode(s.encode()).decode()
def sources(name,rows):
 (out/(name+'.tsv')).write_text(''.join('\t'.join(enc(s[k]) for k in ['id','title','url','date','license','text'])+'\n' for s in rows))
reg=[]
for model,ids in [('qwen3-1.7b',['cap-13','cap-21']),('qwen3-4b',['cap-13']),('phi35-mini',['cap-01','cap-05','cap-09','cap-13','cap-15','cap-21'])]:
 for id in ids:
  row=json.loads((R/'docs/evidence/model-capability/run'/model/(id+'.json')).read_text());name=model+'-'+id;sources(name,cs[id]['sources']);reg.append(name+'\t'+enc(row['resolved_raw']))
(out/'regressions.tsv').write_text('\n'.join(reg)+'\n');absent=[]
for c in cs.values():
 if not c['answerable']:sources(c['id'],c['sources']);absent.append(c['id']+'\t'+enc(c['question']))
(out/'absent.tsv').write_text('\n'.join(absent)+'\n')
new=json.loads((R/'tools/evaluation/complete-claims/protocol.json').read_text());sources('positive',new['cases'][0]['sources'])
# Replay every task190 source-reviewed unsupported draft through today's controller.
replays=[]
ratings=json.loads((R/'docs/evidence/model-capability/builder-assessments.json').read_text())['rows']
for r in ratings:
 if r['raw_support']!='unsupported':continue
 name=r['model']+'-'+r['case'];row=json.loads((R/'docs/evidence/model-capability/run'/r['model']/(r['case']+'.json')).read_text());sources(name,cs[r['case']]['sources'])
 replays.append(name+'\t'+enc(cs[r['case']]['question'])+'\t'+enc(row['raw']))
(out/'unsupported.tsv').write_text('\n'.join(replays)+'\n')
