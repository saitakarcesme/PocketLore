"""Fixed local CPU NLI matrix. No network, truncation, seed or threshold search."""
from pathlib import Path
import json,hashlib,sys,time,os,base64,resource,platform,importlib.metadata
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer
R=Path(__file__).resolve().parents[3];F=Path(__file__).parent;M=R/'downloads/independent-linking/model'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def status():return {x.split(':')[0]:x.split(':',1)[1].strip() for x in Path('/proc/self/status').read_text().splitlines() if x.startswith(('VmRSS:','VmHWM:','VmSwap:','Threads:'))}
if __name__=='__main__':
 out=Path(sys.argv[1]);spec=json.loads((F/'protocol.json').read_text())['verifier'];receipt=json.loads((M/'receipt.json').read_text())
 for name,v in receipt['assets'].items():assert sha(M/name)==v['sha256']
 assert sha(M/spec['file'])==spec['sha256'] and (M/spec['file']).stat().st_size<=1024**3
 assert ort.__version__=='1.24.1';assert json.loads((M/'config.json').read_text())['id2label']=={'0':'contradiction','1':'entailment','2':'neutral'}
 opts=ort.SessionOptions();opts.intra_op_num_threads=6;opts.inter_op_num_threads=1;opts.execution_mode=ort.ExecutionMode.ORT_SEQUENTIAL
 start=time.monotonic();before=status();session=ort.InferenceSession(str(M/spec['file']),sess_options=opts,providers=['CPUExecutionProvider']);load_s=time.monotonic()-start
 tokenizer=Tokenizer.from_file(str(M/'tokenizer.json'));tokenizer.no_truncation();tokenizer.no_padding();pairs=json.loads((out/'prepared/pairs.json').read_text());rows=[];samples=[];failures=[]
 runtime={'python':sys.version,'platform':platform.platform(),'packages':{n:importlib.metadata.version(n) for n in ['onnxruntime','tokenizers','numpy']},'providers':session.get_providers(),'load_s':load_s,'memory_before':before,'memory_loaded':status(),'inputs':[{ 'name':i.name,'shape':i.shape,'type':i.type} for i in session.get_inputs()],'model_receipt':receipt,'source_hashes':{str(p.relative_to(R)):sha(p) for p in [F/'score.py',F/'protocol.json',F/'runtime-declaration.json']},'stage':'Host CPU independent entailment classification, not Android, not generation'}
 (out/'runtime.json').write_text(json.dumps(runtime,indent=2)+'\n')
 with (out/'scores.jsonl').open('x') as stream:
  for i,pair in enumerate(pairs):
   assert hashlib.sha256((pair['premise']+'\0'+pair['hypothesis']).encode()).hexdigest()==pair['key'];t=time.monotonic();encoded=tokenizer.encode(pair['premise'],pair['hypothesis']);tokens=len(encoded.ids);raw=[];probs=[0.,0.,1.];failure=''
   if tokens>512:failure='Pair exceeds512tokens; no truncation'
   else:
    values={'input_ids':encoded.ids,'attention_mask':encoded.attention_mask,'token_type_ids':encoded.type_ids};feed={x.name:np.asarray([values[x.name]],dtype=np.int64) for x in session.get_inputs()}
    try:
     raw=session.run(None,feed)[0][0].astype(float).tolist();e=np.exp(np.asarray(raw)-max(raw));probs=(e/e.sum()).tolist();assert len(probs)==3 and all(np.isfinite(probs))
    except Exception as e:failure=repr(e);failures.append({'key':pair['key'],'failure':failure})
   record={'key':pair['key'],'tokens':tokens,'logits':raw,'probabilities':probs,'failure':failure,'elapsed_s':time.monotonic()-t};stream.write(json.dumps(record)+'\n');stream.flush();rows.append(record)
   mem=status();samples.append({'pair':i,'elapsed_s':time.monotonic()-start,**mem})
   if int(mem.get('VmRSS','0').split()[0])*1024>8*1024**3 or time.monotonic()-start>7200:raise RuntimeError('Declared host resource bound exceeded; partial scores preserved')
   if i%50==0:print(i+1,'/',len(pairs),flush=True)
 (out/'scores.tsv').write_text(''.join('\t'.join([v['key'],*[str(x) for x in v['probabilities']],str(v['tokens']),base64.b64encode(v['failure'].encode()).decode()])+'\n' for v in rows))
 (out/'memory.json').write_text(json.dumps(samples,indent=2)+'\n');(out/'score-receipt.json').write_text(json.dumps({'pairs':len(rows),'failed_pairs':failures,'elapsed_s':time.monotonic()-start,'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'artifacts':{n:sha(out/n) for n in ['runtime.json','scores.jsonl','scores.tsv','memory.json','prepared/pairs.json','manifest.json','origins.json']}},indent=2)+'\n');print('DONE',len(rows),flush=True)
