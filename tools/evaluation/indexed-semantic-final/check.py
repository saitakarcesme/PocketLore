"""Pure final validator: no capture, finalization, worker, or build dispatch."""
import sys,json,copy,subprocess,pathlib
import core as C
import guards,authorization
R=C.R;S=C.S

def validate(p):
 C.need(p['format']=='indexed-semantic-final-547','packet-format');source=C.freeze(p['source_commit']);C.need(p['sources']==source,'packet-source')
 C.need(set(p['files'])=={str(x.relative_to(C.ROOT)) for x in C.RUN.rglob('*') if x.is_file()},'inventory-roster')
 for path,d in p['files'].items():C.need(path==d['path'],'inventory-path');C.verify_artifact(d)
 e=R.consume(p['files'][str((C.RUN/'delta.json').relative_to(C.ROOT))],True)
 C.need(e['status']=='PASS' and e['errors']==[] and e['sources_before']==e['sources_after']==source and e['source_commit']==p['source_commit'],'delta-source');S.samples(e['samples']);C.need(e['authorization']==authorization.verify(p['source_commit']),'parent-authorization');C.need(e['semantic_controls']==guards.controls(),'semantic-control-reconstruction')
 C.need(e['historical']==C.history(),'historical-replay');C.need(e['descriptor_controls']==C.reference_controls(),'descriptor-controls')
 C.need(e['extra_reference_controls']==C.additional_reference_controls(R.manifest()['references']['authored']),'extra-reference-controls')
 context=e['context'];C.need(context['reference']==R.manifest()['references']['authored'],'context-authority');R.validate_context(context['raw'],context['reference'])
 bad=copy.deepcopy(context['raw']);old=bad['version']['inode'];bad['version']['inode']+=1;bad['fdinfo']=bad['fdinfo'].replace('ino:\t'+str(old),'ino:\t'+str(old+1))
 try:R.validate_context(bad,context['reference'])
 except R.Refused as x:C.need(str(x)==e['context_guard']=='context-authority-version','context-mutant-guard')
 else:raise R.Refused('context-mutant-accepted')
 C.need(e['race_guard']=='reference-replaced' and e['race_authority']['sha256']==R.sha(R.canonical({'original':True})+b'\n'),'race-authority')
 current=R.consume(p['files'][str((C.RUN/'race.json').relative_to(C.ROOT))],True);C.need(current=={'replacement':True} and R.version(C.RUN/'race.json')!=e['race_authority']['version'],'race-replacement')
 C.need([q['query'] for q in e['queries']]==R.POLICY['queries'],'query-roster')
 for q in e['queries']:S.V.validate_hits(S.A,q['hits'],S.F.oracle_rows(8),q['query'])
 S.V.validate_hits(S.A,e['pagination'],S.F.oracle_rows(8),'Common');C.need(e['refusals']=={'short':'indexed-query-length','cancel':'cancelled'},'query-refusals')
 guards.export_identity(R.consume(p['files'][str((C.RUN/'export/original.wikitext').relative_to(C.ROOT))]),R.consume(p['files'][str((C.RUN/'export/metadata.json').relative_to(C.ROOT))],True),e['export'],e['pagination'][0])
 C.need(set(e['workers'])=={'positive','pidfd'},'worker-roster')
 for name,d in e['workers'].items():
  C.need(d==p['files'][d['path']],'worker-authority');w=R.consume(d,True);C.need(w['sources_before']==w['sources_after']==source,'worker-source');C.worker(w,name)
 C.need(e['storage_guard']=='storage-reservation','storage-guard')
 b=R.consume(p['files'][str((C.RUN/'build.json').relative_to(C.ROOT))],True);C.need(b['exit']==0 and b['sources']==source and b['apk_sha256']==R.hash_file(C.ROOT/b['apk'],128*1024**2),'build-binding');R.consume(b['log']);S.samples(b['samples'])
 i=C.initial()
 for d in i['old546_files']:
  if d.get('kind')=='historical-symlink-control':
   path=C.ROOT/d['path'];C.need(path.is_symlink() and __import__('os').readlink(path)==d['target'] and path.lstat().st_ino==d['link_inode'] and path.lstat().st_ctime_ns==d['link_ctime_ns'],'historical-symlink')
  else:R.consume(d)
 for d in i['old546_git']:C.need(len(R.git_bytes(d['commit'],d['path'],d['sha256']))==d['bytes'],'historical-git-size')
 C.reserve(0)
 return {'status':'PASS_COMPACT_DELTA_AND_EXPLICIT_HISTORICAL_REPLAY','incremental_bytes':C.used(),'old544':i['old544_bytes'],'old545':i['old545_bytes'],'old546':i['old546_bytes'],'failed543':i['failed543_debt'],'global_bytes':C.used()+i['old544_bytes']+i['old545_bytes']+i['old546_bytes']+i['failed543_debt']}
def main():
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=C.ROOT,text=True).strip();seal=json.loads(R.git_bytes(head,'tools/evaluation/indexed-semantic-final/seal.json'));p=R.consume(seal['packet'],True);print(json.dumps(validate(p),sort_keys=True))
if __name__=='__main__':
 try:main()
 except BaseException as e:print(type(e).__name__+': '+str(e));sys.exit(1)
