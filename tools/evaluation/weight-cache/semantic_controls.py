"""Frozen task539 mutations and separate recorded-delta replay; synthetic only."""
import json,copy,re,base64,hashlib,gzip
from auxiliary import need,Refused,mutation_packet

def bind(run,key,value):
 raw=value.encode();run['observations'][key]=value;run['raw_bytes'][key]={'sha256':hashlib.sha256(raw).hexdigest(),'base64':base64.b64encode(raw).decode()}
def alter_snapshot(run,key,change):
 x=json.loads(run['observations'][key]);change(x);bind(run,key,json.dumps(x))
def event_text(raw,key,value):return re.sub(r'^'+key+r' \d+$',key+' '+str(value),raw,flags=re.M)
def controls(r,validate):
 rows=[]
 cases=[('exact-oom-kill','events-new-failure'),('new-max','events-new-failure'),('event-missing','events-keys'),('event-unknown','events-keys'),('event-negative','events-format'),('event-malformed','events-format'),('event-decrease','events-monotonic'),('event-cgroup','events-cgroup'),('event-before-missing','events-boundaries'),('event-final-failure','events-new-failure'),('exact-duplicate-pressure','pages-unique'),('pressure-out-of-range','pages-range'),('pressure-cardinality','pages-cardinality'),('pressure-missing','snapshot-required'),('pressure-pid','snapshot-pid'),('pressure-vma','snapshot-vma'),('pressure-time','snapshot-chronology'),('pressure-no-touched-rss','pressure-resident'),('tail-duplicate-pages','pages-unique'),('tail-wrong-logical-length','snapshot-range'),('remap-wrong-range','snapshot-range'),('remap-missing-old','snapshot-required'),('remap-cursor','remap-cursor')]
 for family in ['tail','remap','no-progress','mincore-failure','advice-failure','lifecycle','fault_controls']:cases.append(('missing-verified:'+family,'verified-required'))
 cases += [('duplicate-verified','verified-required'),('reordered-verified','verified-order'),('wrong-verified-state','verified-state')]
 for case,guard in cases:
  validate(r,current=False);b=copy.deepcopy(r);life=b['lifecycle']['run'];pressure=b['runs']['mincore-failure'];tail=b['runs']['tail'];remap=b['runs']['remap'];key='mincore-failure-before-injection.json'
  if case in ['exact-oom-kill','new-max']:
   field='oom_kill' if case=='exact-oom-kill' else 'max';s=life['samples'][0];old=int(re.search(r'^'+field+r' (\d+)$',s['memory.events'],re.M)[1]);s['memory.events']=event_text(s['memory.events'],field,old+1)
  elif case=='event-missing':life['samples'][0]['memory.events']=re.sub(r'^oom_kill .*\n','',life['samples'][0]['memory.events'],flags=re.M)
  elif case=='event-unknown':life['samples'][0]['memory.events']+='unexpected 0\n'
  elif case in ['event-negative','event-malformed']:life['samples'][0]['memory.events']=event_text(life['samples'][0]['memory.events'],'oom',-1 if case=='event-negative' else 'NaN')
  elif case=='event-decrease':
   for s in [life['kernel_before'],*life['samples'],life['kernel_after']]:s['memory.events']=event_text(s['memory.events'],'low',1)
   life['samples'][1]['memory.events']=event_text(life['samples'][1]['memory.events'],'low',0)
  elif case=='event-cgroup':life['samples'][0]['group_identity']['inode']+=1
  elif case=='event-before-missing':del life['kernel_before']
  elif case=='event-final-failure':life['kernel_after']['memory.events']=event_text(life['kernel_after']['memory.events'],'oom_kill',999)
  elif case=='exact-duplicate-pressure':alter_snapshot(pressure,key,lambda x:x.update(cached_pages=[0]*4096))
  elif case=='pressure-out-of-range':alter_snapshot(pressure,key,lambda x:x['cached_pages'].__setitem__(-1,8192))
  elif case=='pressure-cardinality':alter_snapshot(pressure,key,lambda x:x['owner']['regions'][0].update(cache_present_pages=999))
  elif case=='pressure-missing':del pressure['observations'][key];del pressure['raw_bytes'][key]
  elif case=='pressure-pid':alter_snapshot(pressure,key,lambda x:x['owner'].update(pid=999999))
  elif case=='pressure-vma':alter_snapshot(pressure,key,lambda x:x['owner'].update(smaps=x['owner']['smaps'].replace('r--s','rw-s')))
  elif case=='pressure-no-touched-rss':alter_snapshot(pressure,key,lambda x:x['owner'].update(smaps=re.sub(r'^Rss:.*$', 'Rss: 0 kB',x['owner']['smaps'],flags=re.M)))
  elif case=='pressure-time':alter_snapshot(pressure,key,lambda x:x['owner'].update(monotonic_ns=pressure['end_ns']+1))
  elif case=='tail-duplicate-pages':alter_snapshot(tail,'tail-tail.json',lambda x:x['cached_pages'].append(x['cached_pages'][-1]))
  elif case=='tail-wrong-logical-length':alter_snapshot(tail,'tail-tail.json',lambda x:x['owner']['regions'][0].update(bytes=33553375))
  elif case=='remap-wrong-range':alter_snapshot(remap,'remap-remap-new.json',lambda x:x['owner']['regions'][0].update(bytes=33554432))
  elif case=='remap-missing-old':del remap['observations']['remap-remap-old.json'];del remap['raw_bytes']['remap-remap-old.json']
  elif case=='remap-cursor':alter_snapshot(remap,'remap-remap-old.json',lambda x:x['cache'].update(cursor=0))
  else:
   family=case.split(':')[1] if ':' in case else 'tail';run=b[family]['run'] if family in b else b['runs'][family];tk=next(k for k in run['observations'] if '-trace-' in k);es=[json.loads(l) for l in run['observations'][tk].splitlines()]
   if case.startswith('missing-verified'):es=[e for e in es if e['operation']!='verified']
   elif case=='duplicate-verified':es.insert(2,copy.deepcopy(es[1]))
   elif case=='reordered-verified':es[1],es[2]=es[2],es[1]
   else:es[1]['outcome']='unknown'
   for i,e in enumerate(es):e['sequence']=i
   bind(run,tk,'\n'.join(json.dumps(e) for e in es)+'\n')
  try:validate(b,current=False)
  except Refused as e:
   need(str(e)==guard,'semantic-wrong-guard:'+case+':'+str(e));packet=mutation_packet(r,b)
   rows.append({'case':case,'expected_guard':guard,'actual_guard':str(e),'positive_revalidated':True,'mutated_packet':packet,'mutated_packet_sha256':packet['reconstructed_sha256']});continue
  raise Refused('semantic-counterexample-accepted:'+case)
 return rows

def reconstruct_controls(r,rows,validate):
 """Decode persisted deltas independently of the producer's equality assertion."""
 base=hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest();out=[]
 for row in rows:
  validate(r);z=row['mutated_packet'];need(z['format']=='structural-delta-v1' and z['base_sha256']==base,'replay-base')
  changes=json.loads(gzip.decompress(base64.b64decode(z['patch_gzip_base64'],validate=True)));b=copy.deepcopy(r)
  for edit in changes:
   target=b
   for key in edit['path'][:-1]:target=target[key]
   key=edit['path'][-1]
   if edit.get('delete'):del target[key]
   else:target[key]=edit['value']
  digest=hashlib.sha256(json.dumps(b,sort_keys=True).encode()).hexdigest();need(digest==z['reconstructed_sha256']==row['mutated_packet_sha256'],'replay-sha')
  try:validate(b)
  except Refused as e:
   need(str(e)==row['expected_guard']==row['actual_guard'],'replay-guard');out.append({'case':row['case'],'family':row.get('family'),'sha256':digest,'guard':str(e)});continue
  raise Refused('replay-accepted')
 return out

def historical_counter_control(r,validate):
 # Constructed-only boundary: unchanged prior counters must not be attributed
 # to this child. The actual kernel receipts remain untouched and distinct.
 validate(r,current=False);b=copy.deepcopy(r);run=b['lifecycle']['run']
 for s in [run['kernel_before'],*run['samples'],run['kernel_after']]:
  for key in ['high','max','oom','oom_kill','oom_group_kill']:s['memory.events']=event_text(s['memory.events'],key,7)
 validate(b,current=False)
 return {'kind':'constructed historical cumulative boundary, not an actual kernel event','accepted_unchanged_history':True,'mutated_packet':mutation_packet(r,b)}
