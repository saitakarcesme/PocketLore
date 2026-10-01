#!/usr/bin/env bash
# Explicit API37 serial; never changes shared defaults, device properties or services.
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$root"
tc=${POCKETLORE_TOOLCHAIN:-/home/isa/Android/atlas-toolchain}
adb="$tc/sdk/platform-tools/adb"
serial=emulator-5564
out="downloads/android-16kb/run-$(date -u +%Y%m%dT%H%M%S)-$$"
mkdir -p "$out"
exec 9>downloads/android-16kb/serial-5564.lock
flock -n 9 || { echo 'Another task305 test owns serial5564'; exit 1; }
exec > >(tee "$out/check.log") 2>&1
trap 'code=$?; echo "exit=$code evidence=$out"' EXIT
[[ $("$adb" -s "$serial" shell getprop sys.boot_completed | tr -d '\r') == 1 ]]
[[ $("$adb" -s "$serial" shell getprop ro.build.version.sdk | tr -d '\r') == 37 ]]
[[ $("$adb" -s "$serial" shell getconf PAGE_SIZE | tr -d '\r') == 16384 ]]
"$adb" -s "$serial" shell getprop > "$out/properties.txt"
"$adb" -s "$serial" shell dumpsys package org.pocketlore.app > "$out/package-before.txt"
bash tools/android-build.sh assembleDebug assembleDebugAndroidTest -PpocketloreTestRunner=org.pocketlore.app.PageSizeInstrumentation > "$out/build.log" 2>&1
python3 tools/evaluation/test_16kb_artifacts.py > "$out/mutations.log"
python3 tools/runtime/repack-16kb-candidate.py > "$out/overlay.log"
apk=${POCKETLORE_16KB_APK:-downloads/android-16kb/refined-ui-16kb.apk}
testapk=android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk
python3 tools/evaluation/verify_16kb_artifacts.py "$apk" > "$out/elf-zip.json"
"$tc/sdk/build-tools/35.0.0/zipalign" -c -P 16 -v 4 "$apk" > "$out/zipalign.log"
source tools/answers/model.env
model="downloads/answers/model/$MODEL_FILENAME"
echo "$MODEL_SHA256  $model" | sha256sum -c -
sha256sum "$apk" "$testapk" "$model" > "$out/identities.txt"
"$adb" -s "$serial" install --no-incremental -r "$apk"
"$adb" -s "$serial" install --no-incremental -r "$testapk"
"$adb" -s "$serial" shell dumpsys package org.pocketlore.app > "$out/package-after.txt"
# Require package manager to clear the previous automatic 4KB compatibility state.
grep -q 'pageSizeCompat=0' "$out/package-after.txt"
"$adb" -s "$serial" shell run-as org.pocketlore.app mkdir -p files/page-size-test
remote_hash=$("$adb" -s "$serial" shell run-as org.pocketlore.app sha256sum files/page-size-test/model.gguf 2>/dev/null | cut -d' ' -f1 || true)
if [[ "$remote_hash" != "$MODEL_SHA256" ]]; then
 "$adb" -s "$serial" shell 'run-as org.pocketlore.app sh -c "cat > files/page-size-test/model.gguf"' < "$model"
fi
"$adb" -s "$serial" shell run-as org.pocketlore.app rm -f files/page-size-test/result.json
"$adb" -s "$serial" shell am force-stop org.pocketlore.app
# Single bounded JNI job; visible scrcpy remains running and all other serials untouched.
timeout 240 "$adb" -s "$serial" shell am instrument -w org.pocketlore.app.test/org.pocketlore.app.PageSizeInstrumentation > "$out/instrumentation.txt"
"$adb" -s "$serial" exec-out run-as org.pocketlore.app cat files/page-size-test/result.json > "$out/result.json"
python3 - "$out/result.json" <<'PY'
import json,sys
r=json.load(open(sys.argv[1]));assert r['status']=='pass',r
assert r['page_size']==16384 and r['sdk']==37 and r['abi']=='x86_64'
assert r['model_sha256']=='74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db'
assert 0<r['tokens']<=24 and r['output'].strip() and 0<r['first_token_ms']<=r['generation_ms']
assert r['sampled_peak_pss_kib']>0
assert set(r['checks'])=={'process_page_size','both_jni_loads','native_index_query','baseline_model_hash','real_load','cancel_before_generation','real_generation_after_cancel','close_reload'}
print('Real API37/16384-byte-process JNI generation and index query pass; ARM64 compiled/ELF-checked only')
PY
"$adb" -s "$serial" shell dumpsys meminfo org.pocketlore.app > "$out/meminfo-after.txt"
"$adb" -s "$serial" shell am start -W -n org.pocketlore.app/.MainActivity > "$out/launch.txt"
"$adb" -s "$serial" shell uiautomator dump /sdcard/pocketlore-16kb-ui.xml > "$out/ui-dump.log"
"$adb" -s "$serial" exec-out cat /sdcard/pocketlore-16kb-ui.xml > "$out/ui.xml"
"$adb" -s "$serial" exec-out screencap -p > "$out/app.png"
python3 - "$out/ui.xml" <<'PY'
import sys
s=open(sys.argv[1]).read();assert 'App compatibility' not in s and 'page size compat' not in s.lower(),s
assert 'PocketLore' in s,s
PY
printf '%s\n' "$out" > downloads/android-16kb/latest-run.txt
