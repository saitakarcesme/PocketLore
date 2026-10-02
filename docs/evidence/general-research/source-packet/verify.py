#!/usr/bin/env python3
"""Offline validation of original source bodies; no device or network work."""
import hashlib, importlib.util, json, pathlib, sys, tempfile
ROOT=pathlib.Path(__file__).resolve().parents[4]
BASE=pathlib.Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def validate(base=BASE):
    manifest=json.loads((base/'manifest.json').read_text())
    assert manifest['total_bytes']==sum(x['bytes'] for x in manifest['files'])
    assert len({x['file'] for x in manifest['files']})==len(manifest['files'])
    for item in manifest['files']:
        p=base/item['file'];data=p.read_bytes()
        assert p.resolve().is_relative_to(base.resolve())
        assert len(data)==item['bytes'] and sha(data)==item['sha256'],item['file']
    historical={x['path']:x for x in json.loads((ROOT/'docs/evidence/general-research/original-artifacts.json').read_text())}
    for item in manifest['files']:
        if 'original_path' in item:
            old=historical[item['original_path']]
            assert (item['bytes'],item['sha256'])==(old['bytes'],old['sha256'])
    sys.path.insert(0,str(ROOT/'tools/packs/research-primary'))
    import build,prepare
    assert pathlib.Path(build.__file__).resolve()==ROOT/'tools/packs/research-primary/build.py'
    assert pathlib.Path(prepare.__file__).resolve()==ROOT/'tools/packs/research-primary/prepare.py'
    oldcache=prepare.CACHE;oldbuild=build.CACHE
    try:
        prepare.CACHE=base/'originals';build.CACHE=base/'originals'
        # Re-extract original rendered paragraphs/wikitext and reapply exact dispositions.
        packet=prepare.prepare()
        assert packet==json.loads((base/'review-packet.json').read_text())
        lock=json.loads((ROOT/'tools/packs/research-primary/sources.lock.json').read_text())
        assert sha((base/'review-packet.json').read_bytes())==lock['review_packet_sha256']
        with tempfile.TemporaryDirectory() as temp:
            out=pathlib.Path(temp)/'edition.plpack';result=build.build(out)
            candidate=json.loads((ROOT/'docs/evidence/general-research/candidate.json').read_text())
            assert sha(out.read_bytes())==candidate['corpus_sha256']
            assert len(result['documents'])==7 and result['passage_count']==22
    finally:
        prepare.CACHE=oldcache;build.CACHE=oldbuild
    return {'files':len(manifest['files']),'source_bytes':manifest['total_bytes'],'documents':7,'spans':22}
def check():
    result=validate()
    # Virtual copies link immutable files; replace/unlink only task-owned temporary paths.
    rejected=[]
    targets=['originals/1376037819.json','originals/wiki-current.json','originals/CC-BY-SA-4.0.txt','originals/1376037819-footer.html','originals/1376037819-history.html']
    for target in targets:
        for mode in ['missing','changed']:
            with tempfile.TemporaryDirectory() as temp:
                base=pathlib.Path(temp)
                for item in json.loads((BASE/'manifest.json').read_text())['files']:
                    dest=base/item['file'];dest.parent.mkdir(parents=True,exist_ok=True);dest.symlink_to(BASE/item['file'])
                # Copy actual bytes where needed; symlink paths are not accepted by validation.
                for p in list(base.rglob('*')):
                    if p.is_symlink():data=p.read_bytes();p.unlink();p.write_bytes(data)
                (base/'manifest.json').write_bytes((BASE/'manifest.json').read_bytes())
                p=base/target;p.unlink()
                if mode=='changed':p.write_bytes(b'corrupted source evidence')
                try:validate(base)
                except (AssertionError,FileNotFoundError,ValueError):rejected.append(mode+':'+target)
                else:raise AssertionError('Source evidence mutation accepted')
    result['negative_controls']=rejected;result['status']='PASS';print(json.dumps(result));return result
if __name__=='__main__':check()
