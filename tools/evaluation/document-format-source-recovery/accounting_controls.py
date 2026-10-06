"""Explicit one-time pure filesystem accounting tests; read-only replay thereafter."""
import pathlib,json,hashlib
import accounting as A
OUT=A.ROOT/'downloads/document-format-source-recovery-554/accounting-controls'
def guard(call,expected):
 try:call()
 except ValueError as e:A.need(str(e)==expected,'wrong-accounting-guard');return str(e)
 raise ValueError('accepted-accounting-corruption')
def execute():
 policy=json.loads((A.BASE/'accounting-policy.json').read_text());A.controls();OUT.mkdir()
 roots=(OUT/'retained',OUT/'successor')
 for p in roots:p.mkdir()
 sentinel=roots[0]/'sentinel';sentinel.write_text(policy['sentinel_utf8']);before=A.scan(roots,roots);n=sum(v['bytes'] for v in before.values());A.need(n==len(policy['sentinel_utf8'].encode()),'sentinel-exact')
 results={}
 for name,candidate in [('wrong',(A.CONTROL_ROOTS[0],A.CONTROL_ROOTS[1].with_name('wrong-root'))),('omitted',A.CONTROL_ROOTS[:1]),('third-omitted',A.CONTROL_ROOTS[:2]),('fourth-omitted',A.CONTROL_ROOTS[:3])]:
  A.controls();results[name]=guard(lambda:A.controls(candidate),'required-root-roster');A.controls()
 A.scan(roots,roots);missing=(OUT/'absent',);results['missing']=guard(lambda:A.scan(missing,missing),'required-root-missing');A.scan(roots,roots)
 with sentinel.open('a') as f:f.write(policy['growth_utf8'])
 grown=A.scan(roots,roots);A.need(sum(v['bytes'] for v in grown.values())-n==len(policy['growth_utf8'].encode()),'growth-exact')
 failed=roots[1]/'failed-review.json';failed.write_text(policy['failed_review_utf8']);final=A.scan(roots,roots);A.need(sum(v['bytes'] for v in final.values())==n+len(policy['growth_utf8'].encode())+len(policy['failed_review_utf8'].encode()),'failure-charged')
 # Kernel's existing root alias resolves to our owned fixture; refuse before traversal.
 link=pathlib.Path('/proc/self/root')/str(roots[0]).lstrip('/');results['symlink']=guard(lambda:A.scan((link,),(link,)),'root-symlink');A.scan(roots,roots)
 receipt={'before':before,'grown':grown,'final':final,'guards':results,'actual_control_root_count':len(A.controls()),'policy_sha256':hashlib.sha256((A.BASE/'accounting-policy.json').read_bytes()).hexdigest()}
 (OUT/'receipt.json').write_text(json.dumps(receipt,sort_keys=True)+'\n')
def validate():
 policy=json.loads((A.BASE/'accounting-policy.json').read_text());r=json.loads((OUT/'receipt.json').read_text());A.need(r['policy_sha256']==hashlib.sha256((A.BASE/'accounting-policy.json').read_bytes()).hexdigest(),'accounting-policy')
 roots=(OUT/'retained',OUT/'successor');A.need(A.scan(roots,roots)==r['final'],'accounting-final-version')
 A.need((roots[0]/'sentinel').read_text()==policy['sentinel_utf8']+policy['growth_utf8'] and (roots[1]/'failed-review.json').read_text()==policy['failed_review_utf8'],'accounting-bytes')
 for phase,expected in [('before',len(policy['sentinel_utf8'].encode())),('grown',len((policy['sentinel_utf8']+policy['growth_utf8']).encode())),('final',len((policy['sentinel_utf8']+policy['growth_utf8']+policy['failed_review_utf8']).encode()))]:A.need(sum(v['bytes'] for v in r[phase].values())==expected,'accounting-stage-count')
 for candidate in [(A.CONTROL_ROOTS[0],A.CONTROL_ROOTS[1].with_name('wrong-root')),A.CONTROL_ROOTS[:1],A.CONTROL_ROOTS[:2],A.CONTROL_ROOTS[:3]]:
  A.controls();guard(lambda:A.controls(candidate),'required-root-roster');A.controls()
 missing=(OUT/'absent',);guard(lambda:A.scan(missing,missing),'required-root-missing');A.scan(roots,roots)
 link=pathlib.Path('/proc/self/root')/str(roots[0]).lstrip('/');guard(lambda:A.scan((link,),(link,)),'root-symlink');A.controls()
 return r['guards']
if __name__=='__main__':execute();print(validate())
