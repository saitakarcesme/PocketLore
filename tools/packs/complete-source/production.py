#!/usr/bin/env python3
"""Single-writer bounded source producer. Never grants source admission."""
import argparse, datetime, fcntl, hashlib, json, math, os, resource, signal, sqlite3
import stat, sys, time, uuid, zlib
from pathlib import Path
import compact as c

RESERVE=100*1024**3
MARGIN=512*1024**2
CUTOFF=1791269964  # 2026-10-06T06:59:24Z; CLI requires an explicit <= cutoff.
SCHEMA=c.SCHEMA.replace('CREATE TABLE candidates(page INTEGER PRIMARY KEY,sequence INTEGER,payload BLOB);','')+'''
CREATE TABLE progress(id INTEGER PRIMARY KEY CHECK(id=1),last_sequence INTEGER,chain TEXT);
INSERT INTO progress VALUES(1,-1,'');
CREATE TABLE blocked(page INTEGER PRIMARY KEY,reason TEXT);
CREATE TABLE original_bindings(sequence INTEGER PRIMARY KEY,binding TEXT NOT NULL);
'''
BASE_PROJECTION=c.Projection

class Stopped(BaseException):pass

def sync_json(path,value):
    temp=path.with_suffix(path.suffix+'.tmp')
    with temp.open('wb') as f:f.write(c.canonical(value)+b'\n');f.flush();os.fsync(f.fileno())
    os.replace(temp,path)
    fd=os.open(path.parent,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)

def disk_free(path):
    s=os.statvfs(path);return s.f_bavail*s.f_frsize

def process_memory():
    d={}
    for line in Path('/proc/self/status').read_text().splitlines():
        if line.startswith(('VmRSS:','VmSize:','VmSwap:')):d[line.split(':')[0]]=int(line.split()[1])*1024
    d['ru_maxrss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    return d

def disk_sample(out,db=None):
    seen=set();logical=allocated=0;files={}
    paths=list(out.iterdir())
    if (out/'events').exists():paths.extend((out/'events').iterdir())
    for p in paths:
        if not p.is_file():continue
        s=p.stat();key=(s.st_dev,s.st_ino)
        if key not in seen:logical+=s.st_size;allocated+=s.st_blocks*512;seen.add(key)
        files[p.name]={'logical':s.st_size,'allocated':s.st_blocks*512}
    # SQLite may unlink temp files while open. Account owned etilqs descriptors too.
    for fd in Path('/proc/self/fd').iterdir():
        try:
            target=os.readlink(fd);s=fd.stat();key=(s.st_dev,s.st_ino)
            if 'etilqs_' in target and stat.S_ISREG(s.st_mode) and key not in seen:
                logical+=s.st_size;allocated+=s.st_blocks*512;seen.add(key);files['sqlite_temp_fd_'+fd.name]={'logical':s.st_size,'allocated':s.st_blocks*512}
        except (FileNotFoundError,OSError):pass
    result={'logical_bytes':logical,'allocated_bytes':allocated,'files':files,'free_host_bytes':disk_free(out)}
    if db is not None:
        result['page_count']=db.execute('PRAGMA page_count').fetchone()[0]
        result['freelist_count']=db.execute('PRAGMA freelist_count').fetchone()[0]
        result['page_size']=db.execute('PRAGMA page_size').fetchone()[0]
    return result

class Guard:
    def __init__(self,seconds,cutoff,root,free=disk_free):
        self.deadline=min(time.monotonic()+seconds,time.monotonic()+cutoff-time.time())
        self.root=root;self.free=free;self.reason=None;self.phase='preflight';self.last_disk=0;self.signals={};self.armed=False;self.seen_phases=set();self.last_logged=-2
    def check(self,write=False):
        if self.reason:raise Stopped(self.reason)
        if time.monotonic()>=self.deadline:self.reason='deadline during '+self.phase;raise Stopped(self.reason)
        if write or time.monotonic()-self.last_disk>.25:
            self.last_disk=time.monotonic()
            if self.free(self.root)<RESERVE+MARGIN:self.reason='100GiB disk reserve plus bounded write margin';raise Stopped(self.reason)
    def progress(self):
        try:self.check();return 0
        except Stopped:return 1
    def install(self):
        def stop(sig,frame):
            self.reason='signal '+signal.Signals(sig).name+' during '+self.phase
            # A second alarm is a hard stop if SQLite rollback/filesystem stalls.
            signal.setitimer(signal.ITIMER_REAL,10)
            signal.signal(signal.SIGALRM,lambda *_:os._exit(124))
            raise Stopped(self.reason)
        for s in [signal.SIGTERM,signal.SIGINT,signal.SIGXCPU,signal.SIGALRM]:self.signals[s]=signal.signal(s,stop)
        signal.setitimer(signal.ITIMER_REAL,max(.001,self.deadline-time.monotonic()));self.armed=True
    def close(self):
        if self.armed:
            signal.setitimer(signal.ITIMER_REAL,0)
            for s,h in self.signals.items():signal.signal(s,h)
            self.armed=False

def cgroup_limits():
    relative=next(x.split(':',2)[2] for x in Path('/proc/self/cgroup').read_text().splitlines() if x.startswith('0::'))
    path=Path('/sys/fs/cgroup')/relative.lstrip('/')
    result={'path':str(path)}
    for name in ['memory.max','memory.swap.max','memory.current','memory.peak','cpu.max','pids.max','pids.current']:
        result[name]=(path/name).read_text().strip()
    return result

def verify_long_limits(limits):
    c.require(limits['memory.max']!='max' and int(limits['memory.max'])<=512*1024**2,'long MemoryMax not enforced')
    c.require(limits['memory.swap.max']=='0','long swap0 not enforced')
    quota,period=limits['cpu.max'].split();c.require(quota!='max' and int(quota)<=4*int(period),'long CPU quota not enforced')
    c.require(limits['pids.max']!='max' and int(limits['pids.max'])<=32,'long TasksMax not enforced')

def row_binding(row):
    return c.sha(c.canonical(list(row[:10]))+(c.sha(row[10]).encode() if row[10] is not None else b'oversized'))

def read_batch(stage,start,ceiling,guard,rows=64,byte_limit=8*1024**2):
    """No source transaction/cursor survives return; transform only after close."""
    db=sqlite3.connect('file:'+str(stage)+'?mode=ro',uri=True,timeout=.2)
    db.execute('PRAGMA cache_size=-2048');db.set_progress_handler(guard.progress,1000)
    sql='SELECT * FROM records WHERE sequence>=? AND sequence<=?';args=[start,ceiling]
    if db.execute("SELECT 1 FROM sqlite_master WHERE name='oversized'").fetchone():
        sql+=" UNION ALL SELECT sequence,member,member_offset,raw_bytes,raw_sha256,NULL,NULL,NULL,NULL,'oversized original',NULL FROM oversized WHERE sequence>=? AND sequence<=?";args.extend([start,ceiling])
    sql+=' ORDER BY sequence LIMIT ?';args.append(rows);batch=[];size=0
    try:
        for row in db.execute(sql,args):
            guard.check();batch.append(row);size+=len(row[10]) if row[10] else 0
            if size>=byte_limit:break
    finally:db.close()
    return batch

def phase_receipt(out,state,guard,phase,db=None):
    guard.phase=phase;state['phase']=phase;state['memory']=process_memory();state['storage']=disk_sample(out,db)
    state['updated_epoch']=time.time();state['source_admission_established']=False;state['distribution_ready']=False
    if phase not in guard.seen_phases:
        (out/'events').mkdir(exist_ok=True);event=out/'events'/('event-'+str(time.time_ns())+'.json');sync_json(event,state);guard.seen_phases.add(phase)
    through=state.get('committed_through',-1)
    if through!=guard.last_logged:
        with (out/'progress.jsonl').open('ab') as f:f.write(c.canonical({'epoch':time.time(),'phase':phase,'committed_through':through,'chain':state.get('chain'),'storage':state['storage'],'memory':state['memory']})+b'\n');f.flush();os.fsync(f.fileno())
        guard.last_logged=through
    sync_json(out/'status.json',state)
    guard.check()

def block(db,page,reason):
    if type(page)==int and 0<page<2**63:
        db.execute('INSERT OR REPLACE INTO blocked VALUES(?,?)',(page,reason));db.execute('DELETE FROM articles WHERE page=?',(page,))
        db.execute('UPDATE latest SET conflict=1 WHERE page=?',(page,))

def process_record(db,row,guard):
    seq,member,offset,size,digest,page,rev,title,license_json,metadata_error,blob=row
    ident={'sequence':seq,'member':member,'member_offset':offset,'raw_bytes':size,'raw_sha256':digest}
    outcome='excluded';reason='';raw_page=None
    try:
        guard.check()
        if blob is None:
            outcome='oversized_unverified';raise ValueError('Original archive range retained; no bounded raw bytes/page identity')
        raw=c.inflate(blob,c.RAW_MAX);c.require(len(raw)==size and c.sha(raw)==digest,'original raw digest/length mismatch')
        d=json.loads(raw,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
        c.require(isinstance(d,dict),'JSON root is not object');raw_page=d.get('identifier')
        c.require(isinstance(d.get('version'),dict),'malformed revision metadata')
        c.require(d.get('identifier')==page and d['version'].get('identifier')==rev and d.get('name')==title and json.loads(license_json)==d.get('license') and not metadata_error,'staged metadata mismatch')
        c.require(type(page)==int and type(rev)==int and 0<page<2**63 and 0<rev<2**63,'invalid numeric identity')
        choice=c.choose(db,page,rev,str(d.get('date_modified','')),digest,seq)
        if choice=='conflicting same revision':block(db,page,choice);outcome='conflict';reason=choice
        elif choice!='latest':outcome='duplicate';reason=choice
        else:
            db.execute('DELETE FROM articles WHERE page=?',(page,))
            capsule=c.transform(raw,ident);packed=c.pack_capsule(capsule);c.require(len(packed)<=c.CAPSULE_MAX,'capsule bound');guard.check(write=True)
            if db.execute('SELECT 1 FROM blocked WHERE page=?',(page,)).fetchone():outcome='quarantined';reason='Prior conflicting/unverifiable original'
            else:
                db.execute('INSERT INTO articles VALUES(?,?,?,?,?,?,?,?,?)',(page,rev,seq,title,capsule['metadata']['license'][0]['identifier'],digest,c.sha(packed),zlib.compress(packed,6),int(not capsule['dispositions'])))
                outcome='transformed';reason='; '.join(capsule['dispositions'])
    except (ValueError,KeyError,TypeError,UnicodeError,RecursionError,zlib.error) as e:
        reason=type(e).__name__+': '+str(e)
        # Both identities are implicated by untrusted metadata; never revive stale content.
        block(db,page,reason);block(db,raw_page,reason)
        if outcome!='oversized_unverified':outcome='excluded'
    db.execute('INSERT INTO dispositions VALUES(?,?,?,?,?,?,?,?,?)',(seq,page,rev,member,offset,size,digest,outcome,reason))
    db.execute('INSERT INTO original_bindings VALUES(?,?)',(seq,row_binding(row)))
    return outcome

def ready_identity(acquisition,stage_status,count):
    return (acquisition.get('status')=='identity_verified' and stage_status.get('status')=='raw_stage_complete'
        and acquisition.get('bytes')==stage_status.get('source_bytes')==140267048582
        and acquisition.get('md5')==stage_status.get('source_md5')=='2276dbb8db3bc93eabc90a505117e373'
        and isinstance(acquisition.get('sha256'),str) and len(acquisition['sha256'])==64
        and acquisition['sha256']==stage_status.get('source_sha256') and stage_status.get('records_received')==count)

def hash_file(path,guard):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while True:
            guard.check();b=f.read(1024*1024)
            if not b:break
            h.update(b);guard.check()
    return h.hexdigest()

def original_for_capsule(stage,cap):
    """Retrieve exact original bytes/HTML; missing originals never imply fidelity."""
    db=sqlite3.connect('file:'+str(stage)+'?mode=ro',uri=True)
    try:row=db.execute('SELECT * FROM records WHERE sequence=?',(cap['identity']['sequence'],)).fetchone()
    finally:db.close()
    c.require(row is not None,'original unavailable');seq,member,offset,size,digest,page,rev,title,lic,err,blob=row
    c.require({'sequence':seq,'member':member,'member_offset':offset,'raw_bytes':size,'raw_sha256':digest}==cap['identity'],'original locator changed')
    raw=c.inflate(blob,c.RAW_MAX);c.require(len(raw)==size and c.sha(raw)==digest,'original digest');d=json.loads(raw)
    c.require(d['identifier']==page==cap['metadata']['identifier'] and d['version']['identifier']==rev==cap['metadata']['version']['identifier'],'original identity')
    c.require(d['license']==cap['metadata']['license'] and d['date_modified']==cap['metadata']['date_modified'],'original license/date')
    source=d['article_body']['html'];c.require(c.sha(source.encode())==cap['html_sha256'],'original HTML digest');c.validate_capsule(cap,source)
    return {'raw':raw,'html':source,'metadata':d,'scope':'Host exact-original retrieval, not installed Android source availability'}

def apply_limits(args):
    remaining=max(1,math.ceil(min(args.seconds,args.cutoff-time.time())))
    used=math.ceil(resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime)
    _,old_hard=resource.getrlimit(resource.RLIMIT_CPU)
    hard=used+remaining+10 if old_hard==resource.RLIM_INFINITY else min(old_hard,used+remaining+10)
    resource.setrlimit(resource.RLIMIT_CPU,(min(used+remaining,hard-1),hard))
    _,old_as=resource.getrlimit(resource.RLIMIT_AS);address=384*1024**2 if old_as==resource.RLIM_INFINITY else min(old_as,384*1024**2)
    resource.setrlimit(resource.RLIMIT_AS,(address,address));os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:1])
    return {'cpu_soft_hard_seconds':resource.getrlimit(resource.RLIMIT_CPU),'address_space_limit_bytes':address,'cpu_affinity':sorted(os.sched_getaffinity(0))}

def run_owned(args,guard=None):
    out=Path(args.out);stage=Path(args.stage);out.parent.mkdir(parents=True,exist_ok=True)
    c.require(args.mode in ['short','long'],'mode');c.require(args.seconds>0 and (args.mode=='long' or args.seconds<=180),'short wall limit')
    c.require(args.cutoff<=CUTOFF and args.cutoff>time.time(),'absolute cutoff expired/invalid')
    limits=apply_limits(args)
    guard=guard or Guard(args.seconds,args.cutoff,out.parent)
    code={p.name:c.file_sha(p) for p in [Path(__file__),Path(c.__file__)]}
    owner=out/'owner.json';old=None
    if args.resume:
        old=json.loads((out/'status.json').read_text());owned=json.loads(owner.read_text())
        c.require(old['phase'] in ['ingest','wait_source','failure'] and old.get('resume_ingest_allowed',False),'finalization interrupted; no silent replay')
        c.require(owned['code']==code and owned['stage']==str(stage.resolve()) and owned['mode']==args.mode and owned['ceiling']==args.ceiling and owned['follow']==args.follow,'resume identity/config mismatch')
    else:sync_json(owner,{'code':code,'stage':str(stage.resolve()),'mode':args.mode,'ceiling':args.ceiling,'follow':args.follow,'created_epoch':time.time()})
    state={'run_id':uuid.uuid4().hex,'status':'RUNNING','mode':args.mode,'pid':os.getpid(),'code':code,'stage':str(stage.resolve()),'ceiling':args.ceiling,'follow':args.follow,'source_admission_established':False,'distribution_ready':False,'resume_ingest_allowed':True,'previous_run':old['run_id'] if old else None,'process_limits':limits,'workers':1}
    db=None;original_projection=c.Projection
    class CheckedProjection(BASE_PROJECTION):
        def emit(self,*a):guard.check();return super().emit(*a)
        def handle_starttag(self,*a):guard.check();c.require(len(self.stack)<256,'HTML nesting bound');return super().handle_starttag(*a)
    try:
        phase_receipt(out,state,guard,'preflight');state['cgroup']=cgroup_limits()
        if args.mode=='long':verify_long_limits(state['cgroup'])
        memory={l.split(':')[0]:int(l.split()[1])*1024 for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith(('MemAvailable:','MemTotal:'))}
        c.require(memory['MemAvailable']>=768*1024**2,'host memory preflight');state['host_memory']=memory
        guard.install();c.Projection=CheckedProjection
        db=sqlite3.connect(out/'index.sqlite',timeout=.2);db.execute('PRAGMA cache_size=-8192');db.execute('PRAGMA synchronous=FULL');db.set_progress_handler(guard.progress,1000)
        def text(blob):guard.check();x=c.unpack_capsule(c.inflate(blob,c.CAPSULE_MAX));guard.check();return x['text']
        db.create_function('capsule_text',1,text,deterministic=True)
        if not args.resume:db.executescript(SCHEMA);db.commit()
        last,chain=db.execute('SELECT last_sequence,chain FROM progress').fetchone();state['committed_through']=last
        while True:
            phase_receipt(out,state,guard,'ingest',db)
            ceiling=args.ceiling if not args.follow else 2**63-1
            batch=read_batch(stage,last+1,ceiling,guard)
            if not batch:
                if not args.follow:c.require(last==args.ceiling,'fixed prefix incomplete');break
                a=json.loads(Path(args.acquisition).read_text());s=json.loads(Path(args.stage_status).read_text())
                if ready_identity(a,s,last+1):break
                if a.get('status') in ['failed','stopped_incomplete'] or s.get('status')=='provisional_stopped':raise Stopped('original acquisition/stage stopped incomplete')
                phase_receipt(out,state,guard,'wait_source',db);time.sleep(.25);continue
            db.execute('BEGIN IMMEDIATE')
            for row in batch:
                guard.check(write=True);c.require(row[0]==last+1,'source sequence gap')
                process_record(db,row,guard);last=row[0];chain=c.sha(chain.encode()+row_binding(row).encode())
                db.execute('UPDATE progress SET last_sequence=?,chain=? WHERE id=1',(last,chain))
            db.commit();state['committed_through']=last;state['chain']=chain;del batch
            if not args.follow and last==args.ceiling:break
        # Freeze coverage by re-reading every locator in short snapshots, not one pinned BEGIN.
        state['resume_ingest_allowed']=False;phase_receipt(out,state,guard,'coverage',db)
        checked=0;chain2=''
        while checked<=last:
            batch=read_batch(stage,checked,last,guard)
            c.require(batch,'coverage gap')
            for row in batch:
                guard.check();c.require(row[0]==checked,'coverage sequence gap')
                binding=row_binding(row);c.require(db.execute('SELECT binding FROM original_bindings WHERE sequence=?',(checked,)).fetchone()==(binding,),'original mutated across snapshots')
                chain2=c.sha(chain2.encode()+binding.encode());checked+=1
            del batch
        c.require(chain2==chain and db.execute('SELECT count(*) FROM dispositions').fetchone()[0]==last+1,'all-record accounting incomplete')
        state['all_record_bindings_rechecked']=checked
        a=json.loads(Path(args.acquisition).read_text()) if args.acquisition else {};s=json.loads(Path(args.stage_status).read_text()) if args.stage_status else {}
        state['whole_original_identity_matched']=ready_identity(a,s,checked)
        state['full_source_admission_established']=False
        state['complete_original_coverage_not_rights']=state['whole_original_identity_matched'] and db.execute("SELECT count(*) FROM dispositions WHERE status IN ('oversized_unverified','excluded','conflict','quarantined')").fetchone()[0]==0
        state['archive_receipts']={'acquisition':a,'stage':s}
        phase_receipt(out,state,guard,'index',db)
        pid=0
        for page,title,blob in db.execute('SELECT page,title,payload FROM articles ORDER BY page'):
            guard.check(write=True);cap=c.unpack_capsule(c.inflate(blob,c.CAPSULE_MAX))
            db.execute('INSERT INTO search(rowid,title,body) VALUES(?,?,?)',(page,title,cap['text']))
            for begin,end,h in c.passages(cap['text']):
                guard.check();pid+=1;db.execute('INSERT INTO passages VALUES(?,?,?,?,?)',(pid,page,begin,end,h))
            if pid%100<10:db.commit()
        db.commit();phase_receipt(out,state,guard,'fts_integrity',db)
        db.execute("INSERT INTO search(search,rank) VALUES('integrity-check',1)");db.commit()
        phase_receipt(out,state,guard,'sqlite_integrity',db);c.require(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
        state['counts']={t:db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ['dispositions','latest','blocked','articles','passages']}
        state['dispositions']=dict(db.execute('SELECT status,count(*) FROM dispositions GROUP BY status'))
        state['licenses']=dict(db.execute('SELECT license,count(*) FROM articles GROUP BY license'))
        state['flag_free_not_admitted']=db.execute('SELECT count(*) FROM articles WHERE candidate=1').fetchone()[0]
        state['storage_before_hash']=disk_sample(out,db);db.close();db=None
        phase_receipt(out,state,guard,'hash');state['index_sha256']=hash_file(out/'index.sqlite',guard)
        state['status']='PROVISIONAL_COMPLETE';phase_receipt(out,state,guard,'complete')
        return state
    except BaseException as e:
        # Keep committed batch boundary, never commit a partially handled record on cancellation.
        if db:
            db.set_progress_handler(None,0);db.rollback()
            if db.execute("SELECT 1 FROM sqlite_master WHERE name='progress'").fetchone():state['committed_through'],state['chain']=db.execute('SELECT last_sequence,chain FROM progress').fetchone()
            else:state['committed_through']=-1
        state.update(status='STOPPED_RETAINED',error=guard.reason or type(e).__name__+': '+str(e),failed_phase=guard.phase,memory=process_memory(),source_admission_established=False,distribution_ready=False)
        sync_json(out/('failure-'+state['run_id']+'.json'),state);sync_json(out/'status.json',state)
        raise
    finally:
        if db:db.close()
        c.Projection=original_projection;guard.close()

def run(args,guard=None):
    # Hold ownership before any status read/write, across rollback and final hash.
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    if not args.resume:
        c.require(not out.exists(),'existing output retained; explicit resume only');out.mkdir()
    c.require(out.is_dir(),'resume output missing')
    fd=os.open(out/'.producer.lock',os.O_CREAT|os.O_RDWR,0o600)
    try:
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('owned producer already active; concurrent resume denied')
        return run_owned(args,guard)
    finally:os.close(fd)

def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['short','long'],required=True);p.add_argument('--stage',required=True);p.add_argument('--out',required=True);p.add_argument('--ceiling',type=int,default=-1);p.add_argument('--follow',action='store_true');p.add_argument('--seconds',type=int,required=True);p.add_argument('--cutoff',type=float,required=True);p.add_argument('--acquisition');p.add_argument('--stage-status');p.add_argument('--resume',action='store_true');a=p.parse_args()
    c.require((a.follow and a.acquisition and a.stage_status) or (not a.follow and a.ceiling>=0),'explicit fixed prefix or follow contract required')
    try:print(json.dumps(run(a),indent=2))
    except BaseException as e:print(type(e).__name__+': '+str(e),file=sys.stderr);return 1
    return 0
if __name__=='__main__':sys.exit(main())
