#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
source "$root/tools/runtime/pins.env"
export JAVA_HOME=${POCKETLORE_TOOLCHAIN:-/home/isa/Android/atlas-toolchain}/jdk
source_dir="$root/downloads/runtime/llama.cpp"
[[ $(git -C "$source_dir" rev-parse HEAD) == "$LLAMA_REVISION" ]]
[[ -z $(git -C "$source_dir" status --porcelain) ]]
"${POCKETLORE_TOOLCHAIN:-/home/isa/Android/atlas-toolchain}/cmake-3.22.1/bin/cmake" -S "$root/tools/runtime/host" -B "$root/downloads/model-capability/host-build" -DPROJECT_ROOT="$root" -DLLAMA_SOURCE="$source_dir" -DPOCKETLORE_REVISION="$LLAMA_REVISION" -DCMAKE_BUILD_TYPE=Release
"${POCKETLORE_TOOLCHAIN:-/home/isa/Android/atlas-toolchain}/cmake-3.22.1/bin/cmake" --build "$root/downloads/model-capability/host-build" --target pocketlore -j 4
