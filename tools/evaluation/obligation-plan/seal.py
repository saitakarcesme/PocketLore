"""Copy one completed run and explicit source assessments; never regenerate answers."""
from pathlib import Path
import json,hashlib,shutil,sys,base64,tempfile,subprocess
from assess import seal
R=Path(__file__).resolve().parents[3];E=R/'docs/evidence/obligation-ledger'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
run=Path(sys.argv[1]);notes=json.loads(Path(sys.argv[2]).read_text());receipt=json.loads((run/'receipt.json').read_text());assert receipt['exit_code']==0 and not receipt['killed'];assert not (E/'run').exists()
shutil.copytree(run,E/'run',ignore=shutil.ignore_patterns('classes'));labels={}
for key,note in notes.items():
 v=json.loads((run/'results'/(key+'.json')).read_text());a=dict(note);reasons=a.pop('claim_reasons',[]);assert len(reasons)==len(v['claims']);a['claims']=[{'text':c['text'],**({'supported':a['supported'],'reason':reason} if isinstance(reason,str) else reason)} for c,reason in zip(v['claims'],reasons)];labels[key]=a
seal(E/'run',labels)
apk=R/'android/app/build/outputs/apk/debug/app-debug.apk';(E/'build.json').write_text(json.dumps({'apk':str(apk.relative_to(R)),'sha256':sha(apk),'bytes':apk.stat().st_size,'exit_code':0},indent=2)+'\n')
samples=json.loads((run/'memory.json').read_text());values=[json.loads(p.read_text()) for p in sorted((run/'results').glob('q[0-9][0-9].json'))];times={}
for stage in ['plan','draft']:
 stages=[v[stage] for v in values if v[stage]['tokens']];times[stage]={'calls':len(stages),'tokens':sum(s['tokens'] for s in stages),'total_ms':sum(s['total_ms'] for s in stages),'first_token_ms':[s['first_token_ms'] for s in stages],'max_prompt_tokens':max(s['prompt_tokens'] for s in stages)}
resource={'stage':'Six-thread CPU host; not Android','wall_seconds':receipt['elapsed_s'],'max_rss_kib':max(int(s.get('VmRSS','0').split()[0]) for s in samples),'max_swap_kib':max(int(s.get('VmSwap','0').split()[0]) for s in samples),'timings':times,'generation_budget_per_question':512,'max_actual_generated_tokens':max(v['plan']['tokens']+v['draft']['tokens'] for v in values)}
with tempfile.TemporaryDirectory(prefix='ledger-plans-') as tmp:
 t=Path(tmp);enc=lambda s:base64.b64encode(s.encode()).decode();rows=[]
 for v in values:rows.append('\t'.join([v['id'],enc(v['question']),enc(v['plan']['raw']),str(v['plan']['tokens']),enc(v['draft']['raw']),str(v['draft']['tokens']),enc(v['plan']['failure']),enc(v['draft']['failure'])]))
 (t/'stages.tsv').write_text('\n'.join(rows)+'\n');manifest=json.loads((run/'manifest.json').read_text());sources=[R/p for p in manifest['sources'] if p.endswith('.java')]+[R/'tools/evaluation/obligation-plan/PlanReceipt.java'];tc=Path('/home/isa/Android/atlas-toolchain/jdk/bin');subprocess.run([tc/'javac','-d',t,*sources],check=True);subprocess.run([tc/'java','-cp',t,'org.pocketlore.app.PlanReceipt',run/'inputs',t/'stages.tsv',E/'plans.json'],check=True)
(E/'resources.json').write_text(json.dumps(resource,indent=2)+'\n')
paths=[p for p in E.rglob('*') if p.is_file() and p.name!='SHA256SUMS']+[R/'tools/evaluation/obligation-plan'/n for n in ['controls.json','ReplayLedger.java','PlanReceipt.java','Behavior.java','verify.py','assess.py','seal.py']]
(E/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(R))+'\n' for p in sorted(paths)))
