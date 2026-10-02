#!/usr/bin/env python3
"""One fixed host development observation, never device or usefulness acceptance."""
import base64,hashlib,json,pathlib,subprocess,time,uuid,zipfile,sys
ROOT=pathlib.Path(__file__).resolve().parents[3];HERE=pathlib.Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=ROOT/'downloads/reference-expansion'/('host-'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'-'+uuid.uuid4().hex[:6]);out.mkdir();print(out,flush=True)
 pack=ROOT/'downloads/reference-expansion/reference-expansion.plpack';cases=HERE/'development.json'
 assert sha(cases)=='7ffc25a4adfcd04a19ec09dd37e23efa0c2c42ede53115986771aeb06d76d20d'
 with zipfile.ZipFile(pack) as z:
  m=json.loads(z.read('manifest.json'));rows=z.read('passages.tsv').decode().splitlines()
 provenance={p['id']:'Edition SHA-256: '+sha(pack)+'; source SHA-256: '+d['raw_sha256']+'; rights review: '+d['rights_review_sha256'] for d in m['documents'] for p in d['passages']}
 source=[]
 for line in rows:
  r=line.split('\t');original=r[0];r[0]='p'+sha(pack)+'_'+original;source.append('\t'.join(r+[provenance[original]]))
 (out/'sources.tsv').write_text('\n'.join(source)+'\n');(out/'license.txt').write_text(m['licenses']['cc-by-sa-4']['text'])
 protocol=json.loads(cases.read_text());(out/'cases.tsv').write_text(''.join(c['id']+'\t'+c['question']+'\n' for c in protocol['cases']))
 java=ROOT/'android/app/src/main/java/org/pocketlore/app';inputs=[java/(n+'.java') for n in ['ResearchEngine','ResearchBrief','ResearchWorkspace','EvidenceAvailability']]+[HERE/'HostResearchCheck.java']
 jdk=pathlib.Path('/home/isa/Android/atlas-toolchain/jdk/bin')
 def run(cmd,name):
  p=subprocess.run(list(map(str,cmd)),cwd=ROOT,capture_output=True,timeout=90);(out/name).write_bytes(p.stdout);(out/(name+'.stderr')).write_bytes(p.stderr);(out/(name+'.command.json')).write_text(json.dumps(dict(command=list(map(str,cmd)),returncode=p.returncode)));assert p.returncode==0,(out/name,p.stderr.decode());return p.stdout
 run([jdk/'javac','-d',out/'classes',*inputs],'compile.txt')
 meter="import subprocess,sys,resource,json; p=subprocess.run(sys.argv[1:]); print(json.dumps({'child_maxrss_kib':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss}),file=sys.stderr); sys.exit(p.returncode)"
 raw=run([sys.executable,'-c',meter,jdk/'java','-Xmx256m','-XX:ActiveProcessorCount=2','-cp',out/'classes','org.pocketlore.app.HostResearchCheck',out/'sources.tsv',out/'cases.tsv',out/'license.txt'],'raw.tsv')
 records=[]
 for line in raw.decode().splitlines():
  ident,ns,ids,rendered=line.split('\t');records.append(dict(id=ident,host_total_ns=int(ns),source_ids=ids.split(',') if ids else [],rendered=base64.b64decode(rendered).decode(),generated=False,route='source_brief',source_level_relevance_completeness='pending inspection'))
 assert [r['id'] for r in records]==[c['id'] for c in protocol['cases']]
 (out/'outputs.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
 receipt=dict(environment='LLMRig host JVM; NOT Android; no model inference',configuration='2 active processors,256MiB Java heap; isolated Python wait reports Java child maximum RSS via getrusage',pack_sha256=sha(pack),source_files={str(p.relative_to(ROOT)):sha(p) for p in inputs},development_sha256=sha(cases),cases=len(records),absence_failures=[r['id'] for c,r in zip(protocol['cases'],records) if c['absent'] and r['source_ids']],files={p.name:sha(p) for p in out.iterdir() if p.is_file()},status='OBSERVED; quality and device gates separate')
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
