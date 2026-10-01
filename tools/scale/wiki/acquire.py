#!/usr/bin/env python3
"""Serial resumable pinned acquisition; 8 MiB streaming, receipts, bounded retries."""
import datetime, hashlib, json, os, pathlib, sys, time, urllib.request, urllib.error

def atomic(path, obj):
    path = pathlib.Path(path)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(obj, indent=2) + '\n')
    os.replace(temp, path)

def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(8*1024*1024), b''): h.update(b)
    return h.hexdigest()

def download(url, path, expected=None, size=None):
    path = pathlib.Path(path)
    receipt = path.with_suffix(path.suffix + '.receipt.json')
    if path.exists():
        actual = digest(path)
        if (expected and actual != expected) or (size and path.stat().st_size != size):
            raise RuntimeError('Existing immutable file mismatch: ' + str(path))
        return actual
    part = path.with_suffix(path.suffix + '.part')
    start = time.monotonic()
    for attempt in range(3):
        offset = part.stat().st_size if part.exists() else 0
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'PocketLore/0.1 (https://github.com/saitakarcesme/PocketLore; offline research corpus)', 'Range':f'bytes={offset}-'} if offset else {'User-Agent':'PocketLore/0.1 (https://github.com/saitakarcesme/PocketLore; offline research corpus)'})
            with urllib.request.urlopen(req, timeout=120) as r:
                if offset and (r.status != 206 or not r.headers.get('Content-Range','').startswith(f'bytes {offset}-')):
                    raise RuntimeError('Server did not honor recovery range; preserved partial')
                with part.open('ab' if offset else 'wb') as f:
                    while b := r.read(8*1024*1024): f.write(b)
                    f.flush(); os.fsync(f.fileno())
            actual = digest(part)
            if (expected and actual != expected) or (size and part.stat().st_size != size):
                raise RuntimeError('Downloaded size/hash mismatch; preserved partial')
            os.replace(part,path)
            atomic(receipt, {'url':url,'sha256':actual,'bytes':path.stat().st_size,'acquired_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-start,'resumed_from':offset})
            return actual
        except Exception as e:
            with path.with_suffix(path.suffix+'.failures.jsonl').open('a') as f:
                f.write(json.dumps({'time':time.time(),'attempt':attempt+1,'offset':offset,'error':str(e)})+'\n')
            if attempt == 2 or isinstance(e,RuntimeError): raise
            time.sleep(min(60,15*2**attempt))

if __name__ == '__main__':
    lane=pathlib.Path(sys.argv[1]); inv=json.loads(pathlib.Path(sys.argv[2]).read_text())
    for i,item in enumerate(inv['files']):
        url=f"https://huggingface.co/datasets/HuggingFaceFW/finewiki/resolve/{inv['revision']}/{item['path']}?download=true"
        target=lane/'bulk'/pathlib.Path(item['path']).name
        sha=download(url,target,item['lfs']['oid'],item['size'])
        atomic(lane/'acquisition-state.json',{'revision':inv['revision'],'completed_through':i,'file':str(target),'sha256':sha,'total_shards':len(inv['files'])})
        print(json.dumps({'completed':i+1,'file':target.name,'sha256':sha}),flush=True)
