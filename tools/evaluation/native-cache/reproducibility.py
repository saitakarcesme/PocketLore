"""Independent metadata-context and lossless-finalization regression controls."""
import hashlib,json,pathlib,subprocess,sys,tempfile,time
from contract import ROOT,sha
from run import BASE
sys.path.insert(0,str(ROOT/'tools/runtime/sparse'))
from build_identity import apply

def command(args,cwd):
 return subprocess.check_output(args,cwd=cwd,text=True,stderr=subprocess.STDOUT,timeout=30)
def main():
 out=pathlib.Path(tempfile.mkdtemp(prefix='metadata-',dir=BASE));source=out/'archive';(source/'ggml').mkdir(parents=True);(source/'cmake').mkdir()
 upstream=ROOT/'downloads/runtime/llama.cpp'
 raw=(upstream/'ggml/CMakeLists.txt').read_text();a=raw.index('find_program(GIT_EXE');b=raw.index('\ninclude(CheckIncludeFileCXX)')
 original=raw[a:b]+'\ninclude("'+str(source/'cmake/build-info.cmake')+'")\nfile(WRITE "${CMAKE_CURRENT_BINARY_DIR}/observed.txt" "${GGML_BUILD_COMMIT}|${BUILD_COMMIT}|${BUILD_NUMBER}|${BUILD_COMPILER}|${BUILD_TARGET}")\n'
 (source/'ggml/CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.22)\nproject(metadata C)\n'+original)
 (source/'cmake/build-info.cmake').write_bytes((upstream/'cmake/build-info.cmake').read_bytes())
 command(['git','init',str(out)],ROOT);(out/'note').write_text('one')
 def commit(msg):
  command(['git','add','note'],out);command(['git','-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m',msg],out)
 def observe(label):
  build=out/label;log=command(['/home/isa/Android/atlas-toolchain/cmake-3.22.1/bin/cmake','-S',str(source/'ggml'),'-B',str(build)],out)
  return {'value':(build/'observed.txt').read_text(),'log':log}
 commit('first');first=observe('old-first');(out/'note').write_text('two');commit('second');second=observe('old-second');assert first['value']!=second['value']
 identity=apply(source,'bb4caa7540188872173c44d161602d9271386413','f'*64)
 # apply replaces common build-info too; retain the fixture's observation suffix.
 fixed=observe('fixed-first');(out/'note').write_text('dirty');dirty=observe('fixed-dirty');commit('third');later=observe('fixed-later');assert fixed['value']==dirty['value']==later['value'] and identity in fixed['value']
 from check import collect_runs,atomic_packet
 inputs=out/'receipts';inputs.mkdir()
 for name in ['fixture','model']:
  p=inputs/(name+'.json');p.write_text(json.dumps({'kind':name,'original':'retained'}));(inputs/(name+'-receipt-path.txt')).write_text(str(p))
 runs,originals,errors=collect_runs(inputs,['fixture','model']);assert not errors
 target=out/'review.json';positive={'runs':runs,'original_receipts':originals,'status':'PASS'};atomic_packet(target,positive);positive_hash=sha(target)
 failure={'runs':runs,'original_receipts':originals,'status':'FAIL','failure':'engineered binary/source mismatch'};atomic_packet(target,failure)
 assert json.loads(target.read_text())['runs']['model']==runs['model'] and (out/'observations'/(positive_hash+'.json')).exists()
 (inputs/'fixture.json').write_text('corrupt');r,o,e=collect_runs(inputs,['fixture','model']);assert 'fixture' in e and r['model']==runs['model'] and o['model']==originals['model']
 (inputs/'model-receipt-path.txt').write_text(str(inputs/'absent'));r,o,e=collect_runs(inputs,['fixture','model']);assert 'model' in e
 packet={'status':'PASS_METADATA_AND_FINALIZATION_CONTROLS','old_first':first,'old_second':second,'fixed':fixed,'dirty':dirty,'later':later,'positive_preserved_sha256':positive_hash,'finalization_cases':['binary/source failure retains both','malformed fixture retains model','missing model refused'],'source':{p:sha(ROOT/p) for p in ['tools/runtime/sparse/build_identity.py','tools/evaluation/native-cache/check.py',str(pathlib.Path(__file__).relative_to(ROOT))]}}
 (BASE/'metadata-controls.json').write_text(json.dumps(packet,indent=2));print(packet['status'])
if __name__=='__main__':main()
