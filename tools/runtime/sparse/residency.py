"""Strict Linux smaps accounting; mapped size is never a resident estimate."""
import re
HEADER=re.compile(r'^([0-9a-f]+)-([0-9a-f]+)\s+([-rwxps]+)\s+[0-9a-f]+\s+([0-9a-f]+:[0-9a-f]+)\s+(\d+)(?:\s+.*)?$')
FIELDS=('Rss','Pss','Anonymous','Swap')
def parse_smaps(text, model_device, model_inode):
    if model_inode <= 0: raise ValueError('Missing model inode')
    rows=[]; row=None
    for line in text.splitlines():
        match=HEADER.match(line)
        if match:
            if row is not None: rows.append(row)
            row={'device':match[4],'inode':int(match[5]),'permission':match[3]}; continue
        if row is None: raise ValueError('Missing mapping header')
        key=line.split(':',1)[0]
        if key in FIELDS:
            m=re.fullmatch(r'([A-Za-z]+):\s+(\d+) kB',line)
            if not m or key in row: raise ValueError('Malformed or duplicate units')
            row[key]=int(m[2])*1024
    if row is not None: rows.append(row)
    if not rows: raise ValueError('Empty smaps')
    result=dict(rss=0,pss=0,anonymous=0,model_file_rss=0,other_file_rss=0,swap=0)
    for r in rows:
        if any(k not in r for k in FIELDS) or r['Pss']>r['Rss'] or r['Anonymous']>r['Rss']: raise ValueError('Incomplete mapping counters')
        result['rss']+=r['Rss'];result['pss']+=r['Pss'];result['anonymous']+=r['Anonymous'];result['swap']+=r['Swap']
        file_rss=r['Rss']-r['Anonymous']
        if r['device']==model_device and r['inode']==model_inode:
            if 'w' in r['permission']: raise ValueError('Model mapping is writable')
            result['model_file_rss']+=file_rss
        else: result['other_file_rss']+=file_rss
    return result

def validate_window(samples, start, end, expected_pid, expected_startticks, expected_model):
    if not start<end or len(samples)<3: raise ValueError('Missing window')
    if expected_model['sha256']!='96b9c0af5c77a4ecaabe3983175112b5ece763261c1ece12b2494b692a70dad7' or expected_model['bytes']!=12290628576 or expected_model['inode']<=0: raise ValueError('Unbound exact model identity')
    previous=start-1; loaded=[]
    for s in samples:
        if s['pid']!=expected_pid or expected_pid<=0 or s['startticks']!=expected_startticks or expected_startticks<=0: raise ValueError('Changed process identity')
        if not start<=s['monotonic_ns']<=end or s['monotonic_ns']<=previous: raise ValueError('Stale or unordered sample')
        previous=s['monotonic_ns']
        if (s['model_device'],s['model_inode'])!=(expected_model['device'],expected_model['inode']): raise ValueError('Model identity changed within window')
        m=parse_smaps(s['smaps'],s['model_device'],s['model_inode'])
        if s['hwm_bytes']<m['rss'] or m['swap']: raise ValueError('Contradictory HWM or swap')
        if s['phase']=='loaded':
            if not m['model_file_rss']: raise ValueError('No observed model pages')
            loaded.append((s,m))
    if len(loaded)<2 or loaded[-1][0]['monotonic_ns']-loaded[0][0]['monotonic_ns']<100000000: raise ValueError('Missing loaded hold coverage')
    return {'sample_count':len(samples),'loaded_samples':len(loaded),'loaded_max_rss':max(m['rss'] for _,m in loaded),'loaded_max_pss':max(m['pss'] for _,m in loaded),'kernel_hwm_max':max(s['hwm_bytes'] for s in samples),'scope':'Per-process sampled residency only; aggregate kernel/OS and generation gates separate'}
