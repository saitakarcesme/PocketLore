#!/usr/bin/env bash
# Behavioral emulator check: no model download and no success based only on file presence.
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
source "$root/tools/runtime/pins.env"
toolchain=${POCKETLORE_TOOLCHAIN:-/home/isa/Android/atlas-toolchain}
adb="$toolchain/sdk/platform-tools/adb"
serial=${POCKETLORE_EMULATOR_SERIAL:-emulator-5560}
[[ "$serial" == emulator-* ]] || { echo 'This check requires an explicitly selected emulator, not physical hardware.' >&2; exit 1; }
out="$root/downloads/runtime/verify-$(date -u +%Y%m%dT%H%M%S)-$$"
mkdir -p "$out"
exec > >(tee "$out/verify.log") 2>&1
trap 'code=$?; echo "verification_exit=$code evidence=$out"' EXIT
model="$root/downloads/runtime/$MODEL_FILENAME"
echo "$MODEL_SHA256  $model" | sha256sum --check
[[ $(stat -c %s "$model") == "$MODEL_BYTES" ]]
[[ $("$adb" -s "$serial" shell getprop ro.product.cpu.abi | tr -d '\r') == x86_64 ]]
bash "$root/tools/android-build.sh" assembleDebug assembleDebugAndroidTest > "$out/build.log" 2>&1
apk="$root/android/app/build/outputs/apk/debug/app-debug.apk"
testapk="$root/android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk"
sha256sum "$apk" "$testapk" "$model" "$root"/android/app/build/generated/nativeLibs/*/*.so > "$out/hashes.txt"
"$toolchain/sdk/build-tools/35.0.0/aapt" dump permissions "$apk" > "$out/permissions.txt"
if grep -q 'android.permission.INTERNET' "$out/permissions.txt"; then echo 'Unexpected network permission'; exit 1; fi
python - "$apk" <<'PY'
import sys, zipfile
with zipfile.ZipFile(sys.argv[1]) as apk:
    for abi in ['arm64-v8a', 'x86_64']:
        data=apk.read(f'lib/{abi}/libpocketlore.so')
        assert data[:4] == b'\x7fELF'
        assert int.from_bytes(data[18:20], 'little') == {'arm64-v8a':183,'x86_64':62}[abi]
    assert b'MIT License' in apk.read('assets/licenses/llama.cpp.txt')
PY
"$adb" -s "$serial" install -r "$apk"
"$adb" -s "$serial" install -r "$testapk"
"$adb" -s "$serial" shell svc wifi disable
"$adb" -s "$serial" shell svc data disable
"$adb" -s "$serial" shell am force-stop org.pocketlore.app
"$adb" -s "$serial" shell run-as org.pocketlore.app mkdir -p files
"$adb" -s "$serial" shell run-as org.pocketlore.app rm -f files/runtime-result.json
"$adb" -s "$serial" shell 'run-as org.pocketlore.app sh -c "cat > files/runtime-smoke.gguf"' < "$model"
"$adb" -s "$serial" shell getprop > "$out/emulator-properties.txt"
# Keep all logs from this time onward without clearing other processes' logs.
"$adb" -s "$serial" logcat -T 1 -v threadtime > "$out/logcat.txt" &
logpid=$!
trap 'code=$?; kill "$logpid" 2>/dev/null || true; echo "verification_exit=$code evidence=$out"' EXIT
timeout 300 "$adb" -s "$serial" shell am instrument -w org.pocketlore.app.test/org.pocketlore.app.NativeSmokeInstrumentation > "$out/instrumentation.txt"
"$adb" -s "$serial" exec-out run-as org.pocketlore.app cat files/runtime-result.json > "$out/result.json"
python - "$out/result.json" <<'PY'
import json, sys
x=json.load(open(sys.argv[1]))
assert x['status']=='pass', x
expected={'real_load','real_generation','deterministic_reuse','corrupt_model','missing_model','generation_without_model','context_overflow','invalid_output_limit','callback_exception','reset_while_busy','cross_thread_cancel','cancel_before_generation','reuse_after_cancel','close_during_generation','closed_handle','cancel_before_load','low_storage','truncated_import','oversized_import','cancelled_import','wrong_magic','bounded_import','source_prompt_generation'}
assert expected == set(x['checks']), x
assert x['abi']=='x86_64'
assert x['sampled_peak_pss_kib'] > 0
assert len(x['generation'])==2
assert all(r['tokens']>0 and r['first_token_ms']>0 and r['total_ms']>=r['first_token_ms'] and r['text'].strip() for r in x['generation'])
print(json.dumps(x, indent=2))
PY
"$adb" -s "$serial" shell dumpsys meminfo org.pocketlore.app > "$out/meminfo-after.txt"
"$adb" -s "$serial" shell run-as org.pocketlore.app du -ak files > "$out/app-files.txt"
echo 'PASS: measured x86_64 emulator JNI behavior; ARM64 compiled only. No physical-device acceptance.'
