#!/usr/bin/env python3
"""Execute admission policy regressions for default, host and Android macro builds."""
from pathlib import Path
import subprocess,tempfile,json
R=Path(__file__).resolve().parents[3]
with tempfile.TemporaryDirectory(prefix='pocketlore-host-policy-') as d:
 d=Path(d);source=d/'test.cpp'
 source.write_text('#include "resource_budget.h"\nint main(){bool rejected=false;try{requireNativeBudget(3ULL*1024*1024*1024,0,0);}catch(const std::runtime_error&){rejected=true;}return rejected==EXPECT_REJECT?0:1;}\n')
 for name,flags,reject in [('default',[],1),('host',['-DPOCKETLORE_HOST_SCREEN'],0),('android-even-with-host-flag',['-DPOCKETLORE_HOST_SCREEN','-D__ANDROID__'],1)]:
  exe=d/name;subprocess.run(['g++','-I',str(R/'android/app/src/main/cpp'),f'-DEXPECT_REJECT={reject}',*flags,str(source),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
 print(json.dumps({'status':'PASS','behavior':'3 GiB model buffers rejected by default and Android; accepted only by explicit non-Android host screen'}))
