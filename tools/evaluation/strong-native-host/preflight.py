import pathlib,os,time,json
C=pathlib.Path('/sys/fs/cgroup'+pathlib.Path('/proc/self/cgroup').read_text().strip().split('::')[1])
def capture():
 r={'epoch':time.time(),'monotonic_ns':time.monotonic_ns(),'pid':os.getpid(),'affinity':sorted(os.sched_getaffinity(0)),'cgroup':str(C),'kernel':{},'meminfo':pathlib.Path('/proc/meminfo').read_text(),'source_job_ownership':[]}
 for n in ['memory.max','memory.swap.max','memory.current','memory.peak','memory.events','cpu.max','pids.max','cgroup.procs']:r['kernel'][n]=(C/n).read_text()
 for p in C.parent.glob('*source*.service'):
  r['source_job_ownership'].append({'path':str(p),'processes':(p/'cgroup.procs').read_text()})
 v=os.statvfs('.');r['free_bytes']=v.f_bavail*v.f_frsize
 assert int(r['kernel']['memory.max'])<=9*1024**3 and r['kernel']['memory.swap.max'].strip()=='0'
 assert len(r['affinity'])<=4 and r['free_bytes']>=100*1024**3
 return r
if __name__=='__main__':print(json.dumps(capture(),indent=2))
