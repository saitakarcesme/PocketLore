#!/usr/bin/env python3
"""Measure current production pre-model routing on frozen public development questions."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,zipfile
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'downloads/gap-review/gate';OUT.mkdir(parents=True,exist_ok=True)
fixture=ROOT/'evaluation/retrieval/development.json';cases=json.loads(fixture.read_text())['cases'];pack=ROOT/'downloads/packs/english-reference.plpack'
with zipfile.ZipFile(pack) as z:(OUT/'passages.tsv').write_bytes(z.read('passages.tsv'))
(OUT/'queries.tsv').write_text(''.join(c['id']+'\t'+c['question']+'\n' for c in cases))
tc=Path(os.environ.get('POCKETLORE_TOOLCHAIN','/home/isa/Android/atlas-toolchain'));src=ROOT/'android/app/src/main/java/org/pocketlore/app'
sources=[src/(n+'.java') for n in ['ResearchEngine','EvidencePrompt','AnswerEngine','NativeRuntime']]+[ROOT/'tools/evaluation/AnswerGateAudit.java']
subprocess.run([str(tc/'jdk/bin/javac'),'-d',str(OUT),*map(str,sources)],check=True)
raw=subprocess.check_output([str(tc/'jdk/bin/java'),'-cp',str(OUT),'org.pocketlore.app.AnswerGateAudit',str(OUT/'passages.tsv'),str(OUT/'queries.tsv')],text=True)
rows=[]
for line,c in zip(raw.splitlines(),cases,strict=True):
 ident,kind,reason,ms=line.split('\t');assert ident==c['id']
 rows.append(dict(id=ident,question=c['question'],expected_coverage=c['expected_coverage'],kind=kind,reason=reason,reaches_model_availability=reason=='No local model is loaded.',host_routing_ms=float(ms)))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'scope':'LLMRig host production pre-model routing with null generator; no inference or answer-quality measurement; token-budget/model gates are not exercised','fixture_sha256':sha(fixture),'pack_sha256':sha(pack),'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sources},'cases':rows}
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'docs/evidence/release-gap-review/current-answer-gate.json');args=parser.parse_args()
args.output.write_text(json.dumps(report,indent=2)+'\n')
print({label:sum(not r['reaches_model_availability'] for r in rows if r['expected_coverage']==label) for label in ['present','absent']})
