#!/usr/bin/env python3
"""Exercise compiled resource admission and prevent host caps leaking into Android."""
from pathlib import Path
import subprocess,tempfile
R=Path(__file__).resolve().parents[3]
code=r'''
#include "resource_budget.h"
int main(){
 if(pocketloreModelLimit!=EXPECTED_FILE || pocketloreModelBufferLimit!=EXPECTED_BUFFER || pocketloreContextTokens!=EXPECTED_CONTEXT || pocketloreOutputTokens!=EXPECTED_OUTPUT)return 1;
 requireNativeBudget(EXPECTED_BUFFER,805306368ULL,1073741824ULL);
 int rejected=0;
 try{requireNativeBudget(EXPECTED_BUFFER+1,0,0);}catch(const std::runtime_error&){rejected++;}
 try{requireNativeBudget(0,805306369ULL,0);}catch(const std::runtime_error&){rejected++;}
 try{requireNativeBudget(0,0,1073741825ULL);}catch(const std::runtime_error&){rejected++;}
 return rejected==3?0:2;
}
'''
with tempfile.TemporaryDirectory(prefix='pocketlore-scale-profile-') as tmp:
 t=Path(tmp);(t/'test.cpp').write_text(code)
 profiles=[('android',['__ANDROID__','POCKETLORE_HOST_SCREEN','POCKETLORE_SCALE_SCREEN','POCKETLORE_SCALE_BUFFER_V2'],2147483648,2147483648,2048,256),('host-v1',['POCKETLORE_SCALE_SCREEN'],6000000000,6000000000,4096,512),('host-v2',['POCKETLORE_SCALE_SCREEN','POCKETLORE_SCALE_BUFFER_V2'],6000000000,9000000000,4096,512)]
 for name,defines,file,buffer,context,output in profiles:
  subprocess.run(['c++','-std=c++17','-I',str(R/'android/app/src/main/cpp'),*[f'-D{d}=1' for d in defines],f'-DEXPECTED_FILE={file}ULL',f'-DEXPECTED_BUFFER={buffer}ULL',f'-DEXPECTED_CONTEXT={context}',f'-DEXPECTED_OUTPUT={output}',str(t/'test.cpp'),'-o',str(t/name)],check=True)
  subprocess.run([t/name],check=True)
print('PASS three compiled profiles, exact-boundary acceptance and nine over-budget rejections; no OS OOM claim')
