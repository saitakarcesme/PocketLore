"""Preserve command evidence before callers assess success; no device selection."""
import json
import subprocess
import time

def capture(command, output, *, cwd, timeout=300, data=None):
    command=list(map(str,command));start=time.monotonic()
    receipt={'command':command,'timeout_seconds':timeout}
    try:
        result=subprocess.run(command,cwd=cwd,input=data,stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,timeout=timeout)
        raw=result.stdout;receipt.update(returncode=result.returncode,timed_out=False)
    except subprocess.TimeoutExpired as error:
        raw=error.stdout or b''
        receipt.update(returncode=None,timed_out=True,error='TimeoutExpired')
    except OSError as error:
        raw=b''
        receipt.update(returncode=None,timed_out=False,error=type(error).__name__,detail=str(error))
    receipt['elapsed_seconds']=time.monotonic()-start
    output.write_bytes(raw)
    output.with_name(output.name+'.command.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return raw,receipt
