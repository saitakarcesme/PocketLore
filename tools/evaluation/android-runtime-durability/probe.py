import pathlib,subprocess,json,hashlib,datetime
ROOT=pathlib.Path(__file__).resolve().parents[3]
OUT=ROOT/'downloads/android-runtime-durability'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');OUT.mkdir(parents=True)
ADB=['/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb','-s','emulator-5564']
def run(name,args):
 p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=40);(OUT/(name+'.txt')).write_bytes(p.stdout);(OUT/(name+'.json')).write_text(json.dumps({'command':args,'exit':p.returncode,'sha256':hashlib.sha256(p.stdout).hexdigest()}));return p.stdout
run('core',['coredumpctl','--no-pager','info','2116975'])
for name,command in {'boot':'cat /proc/sys/kernel/random/boot_id','package':'dumpsys package org.pocketlore.app','data':'su 0 ls -la /data/user/0/org.pocketlore.app','databases':'su 0 ls -la /data/user/0/org.pocketlore.app/databases','app-paths':'su 0 find /data/app -name base.apk','assets':'su 0 du -ak /data/user/0/org.pocketlore.app','pm':'pm list packages -u org.pocketlore','capacity':'cat /proc/meminfo; df -k /data','package-restrictions':"su 0 sh -c 'grep -F org.pocketlore.app /data/system/users/0/package-restrictions.xml'"}.items():run(name,ADB+['shell',command])
print(OUT)
