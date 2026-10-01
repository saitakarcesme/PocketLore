"""Reject insufficient persistent Android capacity before repeating subset work.

Passing this prerequisite never establishes full installation or update safety.
"""
import re

def capacity(df_output, installed_lower_bound):
    if not isinstance(installed_lower_bound, int) or installed_lower_bound <= 0:
        raise ValueError('Invalid installed-byte requirement')
    rows=[]
    for line in df_output.splitlines():
        fields=line.split()
        if len(fields)==6 and fields[0].startswith('/dev/') and re.fullmatch(r'\d+%',fields[4]):
            try:total,used,free=map(int,fields[1:4])
            except ValueError:continue
            if fields[5] not in ('/data','/data/user/0'):continue
            if total<=0 or min(used,free)<0 or used>total or free>total:
                raise ValueError('Invalid filesystem accounting')
            rows.append((fields[0],total*1024,free*1024))
    if len(rows)!=1:raise ValueError('Cannot identify one persistent /data filesystem')
    device,total,free=rows[0]
    return dict(filesystem=device,total_bytes=total,available_bytes=free,
                installed_lower_bound_bytes=installed_lower_bound,
                prerequisite_met=total>=installed_lower_bound,
                meaning='Capacity prerequisite only; installed hashes, update peak and runtime checks remain required')
