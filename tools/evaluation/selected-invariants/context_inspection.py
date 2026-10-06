"""Read-only independent genuine source oracles; no source or rights promotion."""
import base64,copy,hashlib,importlib.util,json,pathlib,resource,shutil,sqlite3,sys,time,zlib
ROOT=pathlib.Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools/packs/selected-source'))
READER=pathlib.Path(sys.argv[2]) if len(sys.argv)>2 else ROOT/'tools/packs/selected-source/read.py'
spec=importlib.util.spec_from_file_location('context_reader',READER);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);InspectionReader=module.InspectionReader
PACKET=pathlib.Path('/home/isa/PocketLore-control/overnight-20261005/source-context-independent-prerequisites-20261006T0606Z')
PIN='0d9c8a7b8ef1efeb83812ff19922ffbd5ca063bbd3fafbcab4aae6e6479af701'
INDEX=ROOT/'downloads/selected-source-invariants/20261006T055216Z-efe85280/structure/candidate/index.sqlite'
INDEX_PIN='05d0b0b427d614c82c56b80b58af0fa2c610a3a5237541aee576240606c747eb'
def sha(b):return hashlib.sha256(b).hexdigest()
def reject(fn):
 try:fn()
 except (ValueError,KeyError,InterruptedError,sqlite3.Error,UnicodeError) as e:return {'rejected':True,'reason':str(e)}
 raise AssertionError('Required refusal was accepted')
def main(out):
 out.mkdir(parents=True);started=time.time();result={'status':'FAIL','source_admission_established':False,'android_execution':False,'positive':[],'negative':{},'start':started}
 try:
  assert sha((PACKET/'manifest.json').read_bytes())==PIN
  for name,entry in json.loads((PACKET/'manifest.json').read_text())['files'].items():assert sha((PACKET/name).read_bytes())==entry['sha256']
  oracles=json.loads((PACKET/'oracles.json').read_text());before=sha(INDEX.read_bytes());assert before==INDEX_PIN;reader=InspectionReader(INDEX,expected_index_sha256=INDEX_PIN);selected=[]
  for oracle in oracles:
   page,rev=oracle['metadata']['identifier'],oracle['metadata']['version']['identifier'];identity=reader.verify_source(page,rev,oracle)
   a,b=oracle['span_start16'],oracle['span_end16'];fragment=''.join(w['original_html'] for w in reader.source_windows(page,rev,a,b));assert fragment==oracle['exact_original_fragment'] and sha(fragment.encode())==oracle['fragment_sha256']
   observation={'id':oracle['id'],'identity':identity,'exact_oracle_sha256':sha(fragment.encode()),'rights_status':oracle['rights_status'],'generation_eligible':False}
   if oracle['id']=='disambiguation-negative':
    assert not oracle['generation_eligible'];observation['classification']='Multiple referents retained; no factual admission'
   else:
    candidates=[]
    for node, in reader.db.execute('SELECT node FROM contexts WHERE page=? AND revision=? AND start<? AND end>?',(page,rev,b,a)):
     context=reader.context(page,rev,node);root=context['root']
     if root[4]<=a and root[5]>=b:candidates.append((root[5]-root[4],node))
    assert candidates,'No complete enclosing context for '+oracle['id'];node=min(candidates)[1];envelope=reader.verified_context(page,rev,node,oracle)
    complete=''.join(w['original_html'] for w in reader.source_windows(page,rev,envelope['start16'],envelope['end16']))
    assert sha(complete.encode())==envelope['original_fragment_sha256'] and fragment in complete and not envelope['generation_eligible']
    observation['envelope']=envelope;selected.append((oracle,node))
   result['positive'].append(observation)
  oracle,node=selected[0];page,rev=oracle['metadata']['identifier'],oracle['metadata']['version']['identifier']
  for key in ('raw_sha256','html_sha256'):
   bad=copy.deepcopy(oracle);bad[key]='0'*64;result['negative']['changed-'+key]=reject(lambda:reader.verified_context(page,rev,node,bad))
  bad=copy.deepcopy(oracle);bad['metadata']['license'][0]['url']='https://invalid.example/';result['negative']['changed-license']=reject(lambda:reader.verify_source(page,rev,bad))
  result['negative']['missing-revision']=reject(lambda:reader.verify_source(page,rev+1,oracle))
  result['negative']['missing-node']=reject(lambda:reader.verified_context(page,rev,100000000,oracle))
  result['negative']['invalid-range']=reject(lambda:list(reader.source_windows(page,rev,-1,8)))
  reader.close();cancel=InspectionReader(INDEX,lambda:True);result['negative']['cancel-before-read']=reject(lambda:cancel.verify_source(page,rev,oracle));cancel.close()
  calls=[0]
  def cancel_mid():calls[0]+=1;return calls[0]>5
  cancel=InspectionReader(INDEX,cancel_mid);result['negative']['cancel-during-capsules']=reject(lambda:cancel.verify_source(page,rev,oracle));cancel.close()
  # Mutations affect only new task-owned small copies, never original candidate/data.
  for label,sql,args in [('missing-piece',"DELETE FROM pieces WHERE page=? AND revision=? AND kind='original' AND part=0",(page,rev)),('corrupt-capsule',"UPDATE capsules SET z=x'00' WHERE sha=(SELECT sha FROM pieces WHERE page=? AND revision=? AND kind='html' LIMIT 1)",(page,rev)),('changed-offset','UPDATE contexts SET start=start+1 WHERE page=? AND revision=? AND node=?',(page,rev,node)),('lost-table-context','UPDATE contexts SET context_root=node WHERE page=? AND revision=? AND node=?',(page,rev,node))]:
   path=out/(label+'.sqlite');shutil.copyfile(INDEX,path);d=sqlite3.connect(path);d.execute(sql,args);d.commit();d.close();result['negative'][label]=reject(lambda:InspectionReader(path,expected_index_sha256=INDEX_PIN))
  unbound=InspectionReader(INDEX);result['negative']['unpinned-context']=reject(lambda:unbound.verified_context(page,rev,node,oracle));unbound.close()
  changed=out/'changed-during-read.sqlite';shutil.copyfile(INDEX,changed);r=InspectionReader(changed,expected_index_sha256=INDEX_PIN)
  d=sqlite3.connect(changed);d.execute('UPDATE contexts SET heading=0 WHERE page=?',(page,));d.commit();d.close()
  result['negative']['changed-during-read']=reject(lambda:r.verified_context(page,rev,node,oracle));r.close()
  assert sha(INDEX.read_bytes())==before
  result.update(status='PASS',index_sha256=before,index_bytes=INDEX.stat().st_size,producer_execution='Reused exact historical seven-source candidate; no new producer or scale execution',reader_sha256=sha(READER.read_bytes()),test_sha256=sha(pathlib.Path(__file__).read_bytes()),independent_manifest_sha256=PIN,independently_generation_eligible_contexts=0)
 except BaseException as e:result['error']=type(e).__name__+': '+str(e)
 finally:
  result['end']=time.time();result['maxrss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024;(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
 return 0 if result['status']=='PASS' else 1
if __name__=='__main__':sys.exit(main(pathlib.Path(sys.argv[1])))
