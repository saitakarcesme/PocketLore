#!/usr/bin/env bash
set -euo pipefail
project_root=$(cd "$(dirname "$0")/.." && pwd)
toolchain=${POCKETLORE_TOOLCHAIN:-/home/isa/Android/atlas-toolchain}
export JAVA_HOME=${JAVA_HOME:-$toolchain/jdk}
export ANDROID_HOME=${ANDROID_HOME:-$toolchain/sdk}
export GRADLE_USER_HOME=${GRADLE_USER_HOME:-$toolchain/gradle-user}
arguments=("$@")
if (( $# == 0 )); then arguments=(assembleDebug); fi
network_arguments=(--offline)
if [[ ${POCKETLORE_GRADLE_ONLINE:-0} == 1 ]]; then network_arguments=(); fi
exec "$toolchain/gradle-8.13/bin/gradle" -p "$project_root/android" "${network_arguments[@]}" --console=plain "${arguments[@]}"
