#!/usr/bin/env python3
"""Audit committed task481 transport/device receipts without any device commands."""
import hashlib,json,pathlib,shutil,sys,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[4]
PACKET=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools/evaluation/reference-expansion'))
from verify import verify_run
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def validate(base):
    success=base/'run-20261002T125014Z-45bccf'
    # The existing behavioral validator now consumes the COMMITTED packet,
    # rather than resolving missing observations from the downloads directory.
    manifest=verify_run(success)
    seal=json.loads((success/'invocation-seal.json').read_text())
    assert seal['status']=='PASS'
    for name,digest in seal['files'].items():
        if name.endswith('.plpack'):continue # Mutated archive payloads stay ignored.
        assert sha(success/name)==digest,('sealed receipt mismatch',name)
    for file in success.glob('*.command.json'):
        command=json.loads(file.read_text())
        assert command['returncode']==0 and not command.get('timed_out',False),file.name
        assert command['command'],file.name
    for phase in ['before','installed','final']:
        for role in ['app','test']:
            path=(success/(phase+'-path-'+role+'.txt')).read_text().strip()
            assert path.startswith('package:/data/app/')
            observed=(success/(phase+'-'+role+'.txt')).read_text().split()
            assert len(observed)==2 and observed[1]==path.removeprefix('package:')
            if phase!='before':assert observed[0]==manifest['apks'][role]['sha256']
    for run in ['run-20261002T124725Z-581c9c','run-20261002T124854Z-2063ab']:
        failed=base/run;receipt=json.loads((failed/'invocation-seal.json').read_text())
        assert receipt['status']=='FAIL' and json.loads((failed/'install.json').read_text())['status']=='FAIL'
        for name,digest in receipt['files'].items():
            if not name.endswith('.plpack'):assert sha(failed/name)==digest,(run,name)
    return manifest['run_id']

def main():
    run=validate(PACKET);rejected=[]
    # Mutations affect copies only. All original observations remain immutable.
    for mutation,file in [('missing-installed','installed-app.txt'),('changed-final','final-app.txt'),('missing-storage','logical-staged.txt'),('missing-continuity','boot-after.txt')]:
        with tempfile.TemporaryDirectory(prefix='task481-packet-') as temp:
            target=pathlib.Path(temp)/'packet';shutil.copytree(PACKET,target)
            output=target/run;path=output/file
            if mutation=='changed-final':path.write_text('0'*64+'  '+path.read_text().split()[1]+'\n')
            else:path.unlink()
            # Rehash/remove the outer binding to require cross-artifact checks,
            # not only detection of an outdated manifest.
            manifest=json.loads((output/'manifest.json').read_text())
            if path.exists():manifest['files'][file]=sha(path)
            else:manifest['files'].pop(file)
            (output/'manifest.json').write_text(json.dumps(manifest))
            try:validate(target)
            except (AssertionError,FileNotFoundError,KeyError,ValueError):rejected.append(mutation)
            else:raise AssertionError('Altered packet accepted: '+mutation)
    print(json.dumps({'status':'PASS','run_id':run,'scope':'Committed raw receipt completeness and bindings; no new device execution or product acceptance','negative_controls':rejected}))
if __name__=='__main__':main()
