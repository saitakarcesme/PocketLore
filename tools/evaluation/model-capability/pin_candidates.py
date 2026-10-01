import urllib.request,json,pathlib
out=pathlib.Path('downloads/model-capability/acquisition');out.mkdir(parents=True,exist_ok=True)
for tag,repo,filename,base in [('qwen3-4b','Qwen/Qwen3-4B-GGUF','Qwen3-4B-Q4_K_M.gguf','Qwen/Qwen3-4B'),('phi35-mini','bartowski/Phi-3.5-mini-instruct-GGUF','Phi-3.5-mini-instruct-Q4_K_M.gguf','microsoft/Phi-3.5-mini-instruct')]:
 def fetch(url):return urllib.request.urlopen(url,timeout=60).read()
 meta=json.loads(fetch('https://huggingface.co/api/models/'+repo+'?blobs=true'));(out/(tag+'-meta.json')).write_text(json.dumps(meta,indent=2))
 item=next(x for x in meta['siblings'] if x['rfilename']==filename)
 bm=json.loads(fetch('https://huggingface.co/api/models/'+base));(out/(tag+'-base-meta.json')).write_text(json.dumps(bm,indent=2))
 card=fetch('https://huggingface.co/'+repo+'/resolve/'+meta['sha']+'/README.md');(out/(tag+'-README.md')).write_bytes(card)
 license=fetch('https://huggingface.co/'+base+'/resolve/'+bm['sha']+'/LICENSE');(out/(tag+'-LICENSE.txt')).write_bytes(license)
 pin={'repo':repo,'revision':meta['sha'],'filename':filename,'sha256':item['lfs']['sha256'],'bytes':item['size'],'license':bm.get('cardData',{}).get('license'),'base_repo':base,'base_revision':bm['sha'],'license_url':'https://huggingface.co/'+base+'/resolve/'+bm['sha']+'/LICENSE','source_url':'https://huggingface.co/'+repo+'/resolve/'+meta['sha']+'/'+filename}
 (out/(tag+'.json')).write_text(json.dumps(pin,indent=2)+'\n');print(json.dumps(pin),flush=True)
