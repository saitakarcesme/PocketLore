#!/usr/bin/env python3
"""Host structural guardrails, not Android rendering or device acceptance."""
from pathlib import Path
import hashlib,json,subprocess,xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[2]
# Task390 preserves the accepted integrated baseline, including task350 model
# selection and task370 cache changes; task310's older baseline is historical.
base='8f23811bcd32aaf6cd9fc6364d1dd7afa540ba48'
java=root/'android/app/src/main/java/org/pocketlore/app'
protected=['AnswerEngine.java','EvidencePrompt.java','ResearchEngine.java','NativePanel.java','PackLibrary.java','ScaleLibrary.java','ScaleWiki.java','ScalePlaces.java','ImportRecovery.java','TravelCatalog.java','EvidenceAvailability.java','ResearchBrief.java','PersonalDocuments.java','PersonalDocumentsActivity.java','PersonalText.java','AttachmentEngine.java','AttachmentsActivity.java','AttachmentAssets.java']
checks=[]
for name in protected:
    path=java/name
    before=subprocess.check_output(['git','show',f'{base}:{path.relative_to(root)}'],cwd=root)
    assert before==path.read_bytes(),name+' changed outside UI scope'
    checks.append(name+' byte-identical to base')
manifest=ET.parse(root/'android/app/src/main/AndroidManifest.xml').getroot()
assert {p.attrib['{http://schemas.android.com/apk/res/android}name'] for p in manifest.findall('uses-permission')}=={'android.permission.RECORD_AUDIO','android.permission.ACCESS_FINE_LOCATION','android.permission.ACCESS_COARSE_LOCATION'}
checks.append('Optional microphone and task360 foreground GPS only; no INTERNET or background location')
styles=ET.parse(root/'android/app/src/main/res/values/styles.xml').getroot()
for name,minimum in [('ReaderButton',48),('ReaderInput',56)]:
    style=next(s for s in styles if s.attrib['name']==name)
    assert next(i.text for i in style if i.attrib['name']=='android:minHeight')==f'{minimum}dp'
checks.append('Native control minimum dimensions declared')
def luminance(color):
    values=[int(color[i:i+2],16)/255 for i in (0,2,4)]
    values=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values]
    return sum(v*w for v,w in zip(values,[.2126,.7152,.0722]))
ratios={}
for foreground in ['202621','245B43','59635B']:
    for background in ['F7F4EC','EEEEE5']:
        values=sorted([luminance(foreground),luminance(background)])
        ratio=(values[1]+.05)/(values[0]+.05)
        assert ratio>=4.5
        ratios[foreground+'/'+background]=round(ratio,2)
checks.append('All declared reading/accent colors exceed 4.5:1 on both surfaces')
print(json.dumps({'status':'PASS','kind':'host structural checks only','checks':checks,'contrast':ratios,'runtime':'See canonical product-ui evidence; these checks alone do not establish Android acceptance'},indent=2))
