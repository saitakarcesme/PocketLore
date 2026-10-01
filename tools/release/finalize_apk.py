#!/usr/bin/env python3
"""Re-emit debug DEX without incremental class checksums; align and sign exact candidate."""
from pathlib import Path
import hashlib,os,subprocess,tempfile,zipfile
ROOT=Path(__file__).resolve().parents[2]
TC=Path(os.environ.get('POCKETLORE_TOOLCHAIN','/home/isa/Android/atlas-toolchain'))
# AGP's pinned builder embeds the D8 version used by this project; no new compiler.
BUILDER_REL='caches/modules-2/files-2.1/com.android.tools.build/builder/8.9.2/f5879953ae9f284e5c6289f62e9960bf532fdb6/builder-8.9.2.jar'
def run(args):subprocess.run(list(map(str,args)),check=True)
def main():
    apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk'
    if not apk.exists():return
    builder=Path(os.environ.get('GRADLE_USER_HOME',TC/'gradle-user'))/BUILDER_REL
    if hashlib.sha256(builder.read_bytes()).hexdigest()!='7dc1d36d12ee81300c5b1672aaae336d1c3cfe90a7b26b2b551389604150e53b':raise ValueError('Unexpected pinned D8 builder jar')
    cache=ROOT/'downloads/release-finalize';cache.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=cache) as directory:
        temp=Path(directory);dex=temp/'dex';dex.mkdir();inputs=[]
        with zipfile.ZipFile(apk) as archive:
            entries={n:(archive.read(n),archive.getinfo(n).compress_type) for n in archive.namelist()}
        for name,(data,_) in entries.items():
            if name.startswith('classes') and name.endswith('.dex'):
                p=temp/name;p.write_bytes(data);inputs.append(p)
        if not inputs:raise ValueError('No DEX payloads')
        # D8 CLI defaults includeClassesChecksum=false. --debug keeps debug information;
        # unlike AGP debug archive builders, this does not opt into incremental checksums.
        run([TC/'jdk/bin/java','-cp',builder,'com.android.tools.r8.D8','--debug','--min-api','28','--output',dex,*sorted(inputs)])
        for name in list(entries):
            upper=name.upper()
            if (name.startswith('classes') and name.endswith('.dex')) or (upper.startswith('META-INF/') and upper.endswith(('.SF','.RSA','.DSA','.EC','MANIFEST.MF'))):del entries[name]
        for p in sorted(dex.glob('*.dex')):entries[p.name]=(p.read_bytes(),zipfile.ZIP_DEFLATED)
        unsigned=temp/'unsigned.apk';aligned=temp/'aligned.apk';signed=temp/'signed.apk'
        with zipfile.ZipFile(unsigned,'w') as out:
            for name,(data,compression) in sorted(entries.items()):
                info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=compression;info.external_attr=0o644<<16;out.writestr(info,data)
        run([TC/'sdk/build-tools/35.0.0/zipalign','-P','16','-f','4',unsigned,aligned])
        run([TC/'sdk/build-tools/35.0.0/apksigner','sign','--ks',ROOT/'downloads/android-debug/debug.keystore','--ks-key-alias','androiddebugkey','--ks-pass','pass:android','--key-pass','pass:android','--out',signed,aligned])
        run([TC/'sdk/build-tools/35.0.0/apksigner','verify',signed])
        signed.replace(apk)
        print('Final debug APK SHA-256:',hashlib.sha256(apk.read_bytes()).hexdigest())
if __name__=='__main__':main()
