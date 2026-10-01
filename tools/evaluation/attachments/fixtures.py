"""Constructed public recognition controls; no factual corpus or held-out claims."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,random,wave,struct,shutil
root=Path(__file__).resolve().parents[3];out=root/'downloads/attachments/fixtures';out.mkdir(exist_ok=True)
font=ImageFont.truetype('/usr/share/fonts/liberation/LiberationSans-Regular.ttf',48)
image=Image.new('RGB',(1000,400),'white');d=ImageDraw.Draw(image);d.text((40,90),'OFFLINE LIBRARY',font=font,fill='black');d.text((40,175),'Review every word.',font=font,fill='black');image.save(out/'text.png');image.rotate(2,resample=Image.Resampling.BICUBIC,fillcolor='white').save(out/'tilted.png');Image.new('RGB',(800,400),'white').save(out/'blank.png');Image.new('RGB',(2100,2100),'white').save(out/'oversized.png');(out/'invalid.png').write_bytes(b'not an image')
shutil.copyfile(root/'downloads/attachments/whisper/samples/jfk.wav',out/'speech.wav')
random.seed(340)
for name,values in [('silence.wav',[0]*32000),('noise.wav',[random.randrange(-2000,2001) for _ in range(32000)])]:
 with wave.open(str(out/name),'wb') as w:w.setparams((1,2,16000,len(values),'NONE','not compressed'));w.writeframes(struct.pack('<'+'h'*len(values),*values))
(out/'invalid.wav').write_bytes(b'not a WAV')
manifest={'scope':'Public development; text/tilted fixtures are generated signs, not real camera photos; speech is pinned upstream JFK sample, not microphone capture','speech_source':'https://github.com/ggml-org/whisper.cpp/blob/a8d002cfd879315632a579e73f0148d06959de36/samples/jfk.wav','expectations':{'text.png':['OFFLINE LIBRARY','Review every word'],'tilted.png':['OFFLINE LIBRARY'],'blank.png':'empty','speech.wav':['country','ask'],'silence.wav':'empty','noise.wav':'record actual result; never submit automatically','invalid.png':'reject','oversized.png':'reject','invalid.wav':'reject'},'files':{p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(out.iterdir())}}
(root/'docs/evidence/attachments/fixtures.json').write_text(json.dumps(manifest,indent=2)+'\n')
