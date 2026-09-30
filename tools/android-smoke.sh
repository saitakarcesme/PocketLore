#!/usr/bin/env bash
# Task 020 acceptance: real JNI model + production Activity + actual file-picker UI.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
toolchain=${POCKETLORE_TOOLCHAIN:-/home/isa/Android/atlas-toolchain}
source "$root/tools/answers/model.env"
adb="$toolchain/sdk/platform-tools/adb"
serial=${POCKETLORE_EMULATOR_SERIAL:-emulator-5560}
[[ "$serial" == emulator-* ]] || { echo 'Emulator serial required'; exit 1; }
out="$root/downloads/answers/smoke-$(date -u +%Y%m%dT%H%M%S)-$$"
mkdir -p "$out"
exec > >(tee "$out/smoke.log") 2>&1
trap 'code=$?; echo "smoke_exit=$code evidence=$out"' EXIT
[[ $("$adb" -s "$serial" shell getprop sys.boot_completed | tr -d '\r') == 1 ]]
[[ $("$adb" -s "$serial" shell getprop ro.product.cpu.abi | tr -d '\r') == x86_64 ]]
model="$root/downloads/answers/model/$MODEL_FILENAME"
echo "$MODEL_SHA256  $model" | sha256sum --check
bash "$root/tools/answers/check.sh"
bash "$root/tools/android-check.sh"
bash "$root/tools/android-build.sh" assembleDebug assembleDebugAndroidTest -PpocketloreTestRunner=org.pocketlore.app.AnswerSmokeInstrumentation > "$out/build.log" 2>&1
apk="$root/android/app/build/outputs/apk/debug/app-debug.apk"
testapk="$root/android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk"
sha256sum "$apk" "$testapk" "$model" "$root/tools/answers/development-cases.json" > "$out/hashes.txt"
"$toolchain/sdk/build-tools/35.0.0/aapt" dump permissions "$apk" > "$out/permissions.txt"
if grep -q android.permission.INTERNET "$out/permissions.txt"; then echo 'Unexpected network permission'; exit 1; fi
"$adb" -s "$serial" install -r "$apk"
"$adb" -s "$serial" install -r "$testapk"
"$adb" -s "$serial" shell svc wifi disable
"$adb" -s "$serial" shell svc data disable
python3 "$root/tools/answers/ui-smoke.py" --adb "$adb" --serial "$serial" --model "$model" --out "$out/ui"
"$adb" -s "$serial" shell am force-stop org.pocketlore.app
"$adb" -s "$serial" shell run-as org.pocketlore.app rm -f files/answer-result.json
"$adb" -s "$serial" shell 'run-as org.pocketlore.app sh -c "cat > files/answer-development-cases.json"' < "$root/tools/answers/development-cases.json"
timeout 300 "$adb" -s "$serial" shell am instrument -w org.pocketlore.app.test/org.pocketlore.app.AnswerSmokeInstrumentation > "$out/instrumentation.txt"
"$adb" -s "$serial" exec-out run-as org.pocketlore.app cat files/answer-result.json > "$out/result.json"
python3 - "$out/result.json" "$root/tools/answers/development-cases.json" "$MODEL_SHA256" <<'PY'
import hashlib,json,sys
r=json.load(open(sys.argv[1]));print(json.dumps(r,indent=2))
assert r['status']=='pass',r.get('error')
assert r['development_cases_sha256']==hashlib.sha256(open(sys.argv[2],'rb').read()).hexdigest()
assert r['model_sha256']==sys.argv[3]
assert r['generated_case_count']>=1
expected={'saved_model_load','real_answer_flow','unsupported_abstention','partial_coverage_abstention','new_question_clears_answer','cancel_real_generation','recreation_cancels_generation','reuse_after_recreation','source_inspection_opened'}
assert expected==set(r['checks'])
assert len(r['cases'])==4
PY
"$adb" -s "$serial" shell settings get global wifi_on > "$out/wifi.txt"
"$adb" -s "$serial" shell settings get global mobile_data > "$out/mobile-data.txt"
"$adb" -s "$serial" shell run-as org.pocketlore.app du -ak files > "$out/app-files.txt"
echo 'PASS: real emulator answer, citation integrity, abstention, cancellation, import and lifecycle checks. No physical-device or factual-quality acceptance.'
