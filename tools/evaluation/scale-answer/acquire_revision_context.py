"""Bounded exact-revision review context only; never changes source/admission ledgers."""
import pathlib,json,hashlib,urllib.request,time,re
ROOT=pathlib.Path(__file__).resolve().parents[3];sha=lambda b:hashlib.sha256(b).hexdigest()
report=json.loads((ROOT/'docs/evidence/scale-answer/strategy-change/source-dossier.json').read_text());receipts=[]
for row in report['dispositions']:
 if 'revision' not in row:continue
 revision=row['revision'];url='https://en.wikipedia.org/w/index.php?oldid='+revision
 path=ROOT/'downloads/scale-answer'/('original-'+str(row['id'])+'-'+revision+'.html');t=time.monotonic();receipt={'id':row['id'],'revision':revision,'url':url,'limit_bytes':4194304}
 try:
  earlier=ROOT/'downloads/scale-answer/ascii-1306300730-original.html'
  if row['id']==586 and earlier.exists():path=earlier
  if path.exists():body=path.read_bytes();receipt['cache_reused']=True
  else:
   request=urllib.request.Request(url,headers={'User-Agent':'PocketLoreSourceReview/0.1 (bounded public development source verification)'})
   with urllib.request.urlopen(request,timeout=20) as response:
    body=response.read(4194305);receipt['http_status']=response.status;receipt['final_url']=response.url
   if len(body)>4194304:raise ValueError('Source exceeds declared byte cap')
   path.write_bytes(body)
  text=body.decode('utf-8');observed=re.search(r'"wgRevisionId":(\d+)',text);article=re.search(r'"wgArticleId":(\d+)',text)
  if not observed or observed.group(1)!=revision or not article or int(article.group(1))!=row['id']:raise ValueError('Response is not requested article revision')
  receipt.update(status='identity_verified_not_rights_cleared',path=str(path.relative_to(ROOT)),bytes=len(body),sha256=sha(body),license_links=re.findall(r'<link rel="license" href="([^"]+)"',text))
 except Exception as e:receipt.update(status='failed',error=type(e).__name__+': '+str(e))
 receipt['elapsed_seconds']=time.monotonic()-t;receipts.append(receipt)
 (ROOT/'docs/evidence/scale-answer/strategy-change/revision-context.json').write_text(json.dumps({'policy':'Seven bounded historical pages for source adjudication; license links are not source-specific approval. No corpus replacement or generation.','receipts':receipts},indent=2)+'\n')
 print(row['id'],receipt['status'],flush=True)
