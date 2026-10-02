"""Offline audit only: never invokes Android, builds, inference, or services."""
import base64
import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
PACKET = ROOT / 'docs/evidence/modern-receipt-audit'
RUN = '20261002T025132Z-be41f6a6'
CANDIDATE = '4e5652009485a86b80e04415cbce740b36472db7'
BASE = '5ea7a6d'
APK = '9c71a32dbc2deac3d650c6849a335379bd2b005c1516437c613bcd0fcff7dd70'
PHASES = {'default':'report.json', 'large':'report.json', 'cold':'report.json',
          'documents':'results.json', 'documents-cold':'restart.json',
          'native-cards-recognition':'report.json', 'probe-false':'report.json', 'probe-true':'report.json'}

def digest(value):
    return hashlib.sha256(value).hexdigest()

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

def validate(data, check_manifest=True):
    def text(name): return data[name].decode()
    def obj(name): return json.loads(data[name])
    m = obj('manifest.json')
    assert (m['run_id'], m['serial'], m['sdk'], m['page_size']) == (RUN, 'emulator-5564', 37, 16384)
    assert m['apk_sha256'] == APK and m['apk_bytes'] == 22702878
    assert {p['file'] for p in m['reports']} == {p+'/'+f for p,f in PHASES.items() if not p.startswith('probe')}
    if check_manifest:
        for name, pin in m['files'].items(): assert digest(data[name]) == pin, name
    for name in data:
        if name.endswith('.command.json'):
            c=obj(name)
            assert c['returncode'] == 0 and 'timeout_seconds' not in c, name
    summary = {}
    for phase, report in PHASES.items():
        expected = RUN + '-' + phase if phase.startswith('probe') else RUN
        raw=text(phase+'/runtime.txt')
        assert raw.count('INSTRUMENTATION_CODE: -1') == 1 and 'Process crashed' not in raw
        chunks={}; manifest=None; total=0
        for line in raw.splitlines():
            if line.startswith('INSTRUMENTATION_STATUS: pocketlore_chunk='):
                c=json.loads(line.split('=',1)[1]); assert c['run_id']==expected
                name=c['name']; assert pathlib.PurePosixPath(name).name==name and name not in ('.','..')
                assert type(c['index']) is int and type(c['count']) is int and 0<=c['index']<c['count']<=512
                value=base64.b64decode(c['data'],validate=True);total+=len(value)
                assert len(value)<=32768 and total<=64*1024*1024
                entry=chunks.setdefault(name,{'count':c['count'],'parts':{}})
                assert entry['count']==c['count'] and c['index'] not in entry['parts']
                entry['parts'][c['index']]=value
            elif line.startswith('INSTRUMENTATION_STATUS: pocketlore_manifest='):
                assert manifest is None
                manifest=json.loads(line.split('=',1)[1]);assert manifest['run_id']==expected
        assert manifest and set(manifest['files'])==set(chunks)
        for name,pin in manifest['files'].items():
            c=chunks[name];assert set(c['parts'])==set(range(c['count']))
            value=b''.join(c['parts'][i] for i in range(c['count']))
            assert len(value)==pin['bytes'] and digest(value)==pin['sha256']
            assert value==data[phase+'/'+name], 'Decoded stream differs: '+phase+'/'+name
        assert report in manifest['files']
        r=obj(phase+'/'+report);assert r['run_id']==expected and r['status']=='PASS'
        if phase.startswith('probe'):
            assert r['automation']==(phase=='probe-true')
            assert data[phase+'/boot-after.txt']==data['boot-id-before.txt']
        summary[phase]={'returncode':obj(phase+'/runtime.txt.command.json')['returncode'],
                        'elapsed_seconds':obj(phase+'/runtime.txt.command.json')['elapsed_seconds'],
                        'checks':len(r.get('checks',[])), 'streamed_files':len(chunks), 'decoded_bytes':total}
    assert data['boot-id-before.txt']==data['boot-id-after.txt']
    assert text('font-before.txt').strip()==text('font-final-value.txt').strip()=='1.0'
    assert data['assets-before.txt']==data['assets-after.txt']
    for name in ['apk-hash-before.txt','apk-hash-after.txt','installed-hash.txt']: assert text(name).split()[0]==APK
    for phase,scale in [('default',1),('large',2)]:
        r=obj(phase+'/report.json');assert r['sdk']==37 and r['activity_font_scale']==scale
        assert r['font_original']==r['font_restored']=='1.0'
        assert {'Research test invoked no model','Draft restored without relabeling previous answer','Retry destination matches exact source bytes','Activity destruction closes blocked writer','Source opening and note persistence survive blocked destination','Android Back closes keyboard without leaving Research'}<=set(r['checks'])
        assert 'EditText' in text(phase+'/research-keyboard-accessibility.txt')
        assert len(data[phase+'/research-keyboard.png'])>10000
    assert 'Bookmark and note survive process death' in obj('cold/report.json')['checks']
    d=obj('documents/results.json');assert d['api']==37
    assert {'live_catalog_restored_exactly','personal_library_return_does_not_infer','actual_source_dialog_offsets_owner_exact_text','blocked_export_cancelled'}<=set(d['checks'])
    d=obj('documents-cold/restart.json');assert d['api']==37 and d['retained_collections']==7
    n=obj('native-cards-recognition/report.json')
    assert n['sdk']==37 and n['page_size']==16384 and n['generation_performed'] is False
    assert n['model_sha256']=='74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db'
    assert n['model_bytes']==491400032 and {x['id'] for x in n['reviewed_cards']}=={'292223','292672','292968'}
    assert not n['ocr_asset_present'] and not n['speech_asset_present']
    assert {'Precancelled load rejected','Cancel reset close reload releases native state','Missing speech does not start microphone','Missing OCR fails explicitly before image recognition'}<=set(n['checks'])
    native=obj('native.json');assert native['apk_sha256']==APK
    assert len(native['libraries'])==6
    for lib in native['libraries']:
        assert lib['zip_offset']%16384==0 and lib['uncompressed']
        for seg in lib['loads']: assert seg['align']>=16384 and (seg['vaddr']-seg['offset'])%16384==0
        for seg in lib['relro']: assert (seg['vaddr']+seg['memsz'])%16384==0
    assert text('zipalign.txt').rstrip().endswith('Verification succesful')
    assert 'pageSizeCompat=0' in text('package-after.txt') and 'App compatibility' not in text('ui.xml')
    assert 'android.permission.INTERNET' not in text('permissions.txt')
    for name in ['logical-before.txt','logical-after.txt','allocated-before.txt','allocated-after.txt']:
        assert int(text(name).split()[0])>0
    return summary

def main():
    frozen=json.loads((PACKET/'frozen-artifacts.json').read_text())
    data={}
    for name,pin in frozen['files'].items():
        p=ROOT/name;value=p.read_bytes()
        assert len(value)==pin['bytes'] and digest(value)==pin['sha256'],name
        if name.startswith(frozen['run']+'/'):data[name[len(frozen['run'])+1:]]=value
    assert data['executed-check.py']==git('show',CANDIDATE+':tools/evaluation/modern-integrated/check.py')
    assert git('rev-parse',BASE+':android/app/src/main')==git('rev-parse',CANDIDATE+':android/app/src/main')
    lineage=json.loads((PACKET/'lineage.json').read_text())
    for name,pin in lineage['candidate_sources'].items():assert digest(git('show',CANDIDATE+':'+name))==pin
    summary=validate(data)
    for name,pin in json.loads((PACKET/'packet-files.json').read_text()).items():
        value=(PACKET/name).read_bytes()
        assert digest(value)==pin,name
        if name.startswith('receipts/') and not name.endswith('runtime-without-chunks.txt'):
            assert value==data[name[len('receipts/'):]],name
    negatives=[]
    for kind in ['stale-run','missing-phase','corrupt-chunk','corrupted-manifest-hash','boot-mismatch','font-mismatch','failed-transport']:
        changed=dict(data)
        if kind=='stale-run':
            r=json.loads(changed['default/report.json']);r['run_id']='stale';changed['default/report.json']=json.dumps(r).encode()
        elif kind=='missing-phase':del changed['large/runtime.txt']
        elif kind=='corrupt-chunk':
            raw=changed['default/runtime.txt'].decode().splitlines()
            for i,line in enumerate(raw):
                if line.startswith('INSTRUMENTATION_STATUS: pocketlore_chunk='):
                    c=json.loads(line.split('=',1)[1]);v=bytearray(base64.b64decode(c['data']));v[0]^=1
                    c['data']=base64.b64encode(v).decode();raw[i]='INSTRUMENTATION_STATUS: pocketlore_chunk='+json.dumps(c);break
            changed['default/runtime.txt']='\n'.join(raw).encode()
        elif kind=='corrupted-manifest-hash':
            m=json.loads(changed['manifest.json']);m['files']['default/report.json']='0'*64;changed['manifest.json']=json.dumps(m).encode()
        elif kind=='boot-mismatch':changed['boot-id-after.txt']=b'other-boot\n'
        elif kind=='font-mismatch':changed['font-final-value.txt']=b'2.0\n'
        else:changed['cold/runtime.txt.command.json']=b'{"returncode":255}'
        try:validate(changed,check_manifest=(kind=='corrupted-manifest-hash'))
        except (AssertionError,KeyError):negatives.append(kind)
        else:raise AssertionError('Accepted negative '+kind)
    result=json.loads((PACKET/'conclusion.json').read_text())
    assert result['classification']=='incomplete' and result['receipt_validation']=='supported'
    assert result['source_to_test_apk_attestation']=='missing' and result['product_acceptance'] is False
    print(json.dumps({'audit_check':'PASS','classification':result['classification'],'receipt_validation':'supported','phases':summary,'negative_controls':negatives},indent=2))

if __name__=='__main__':main()
