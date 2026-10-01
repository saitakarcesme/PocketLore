#!/usr/bin/env bash
set -euo pipefail
project_root=$(cd "$(dirname "$0")/.." && pwd)
toolchain=${POCKETLORE_TOOLCHAIN:-/home/isa/Android/atlas-toolchain}
export JAVA_HOME=${JAVA_HOME:-$toolchain/jdk}
export ANDROID_HOME=${ANDROID_HOME:-$toolchain/sdk}
export GRADLE_USER_HOME=${GRADLE_USER_HOME:-$toolchain/gradle-user}
# Keep development signing reproducible within this checkout and inside the sandbox.
# This standard debug credential is not a production key and must never be committed.
debug_dir="$project_root/downloads/android-debug"
mkdir -p "$debug_dir"
chmod 700 "$debug_dir"
if [[ ! -f "$debug_dir/debug.keystore" ]]; then
  "$JAVA_HOME/bin/keytool" -genkeypair -keystore "$debug_dir/debug.keystore" \
    -storepass android -keypass android -alias androiddebugkey -keyalg RSA \
    -keysize 2048 -validity 10000 -dname "CN=Android Debug,O=Android,C=US"
  chmod 600 "$debug_dir/debug.keystore"
fi
arguments=("$@")
if (( $# == 0 )); then arguments=(assembleDebug); fi
network_arguments=(--offline)
if [[ ${POCKETLORE_GRADLE_ONLINE:-0} == 1 ]]; then network_arguments=(); fi
"$toolchain/gradle-8.13/bin/gradle" -p "$project_root/android" "${network_arguments[@]}" --console=plain --init-script "$project_root/tools/release/debug-signing.gradle" "${arguments[@]}"

# Deterministic candidate packaging is part of every successful build invocation.
python3 "$project_root/tools/release/finalize_apk.py"
