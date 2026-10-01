import base64,hashlib,json,pathlib,subprocess,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[3];HERE=pathlib.Path(__file__).parent;OUT=ROOT/'docs/evidence/scale-answer'
def run():
 rows=json.loads((OUT/'snapshot-inputs.json').read_text())
 with tempfile.TemporaryDirectory(prefix='scale-adapter-') as tmp:
  tmp=pathlib.Path(tmp);lines=[]
  for row in rows:
   d=json.loads((ROOT/row['record_path']).read_text());cols=row['fields']+[d['text']];lines.append('\t'.join(base64.b64encode(c.encode()).decode() for c in cols)+'\t'+str(row['end_utf16']))
  (tmp/'input.tsv').write_text('\n'.join(lines)+'\n')
  cases=json.loads((HERE/'cases.json').read_text());(tmp/'cases.tsv').write_text(''.join(c['id']+'\t'+base64.b64encode(c['question'].encode()).decode()+'\t'+','.join(map(str,c['documents']))+'\t'+c['expected_route']+'\n' for c in cases))
  names=['ScaleAnswerAdapter','BoundAnswer','ObligationAnswer','ResearchEngine','EvidenceAvailability','EvidencePrompt','AnswerEngine','NativeRuntime']
  sources=[ROOT/'android/app/src/main/java/org/pocketlore/app'/f'{n}.java' for n in names]+[HERE/'AdapterCheck.java']
  subprocess.run(['javac','-d',str(tmp),*map(str,sources)],check=True)
  p=subprocess.run(['java','-Xmx256m','-cp',str(tmp),'org.pocketlore.app.AdapterCheck',str(tmp/'input.tsv'),str(tmp/'cases.tsv')],capture_output=True,text=True)
  if p.returncode:raise RuntimeError(p.stderr+p.stdout)
  return p.stdout
if __name__=='__main__':
 out=run();(OUT/'host-tests.log').write_text(out);print(out)
