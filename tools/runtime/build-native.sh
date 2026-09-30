#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
source "$root/tools/runtime/pins.env"
toolchain=${POCKETLORE_TOOLCHAIN:-/home/isa/Android/atlas-toolchain}
src="$root/downloads/runtime/llama.cpp"
[[ $(git -C "$src" rev-parse HEAD) == "$LLAMA_REVISION" ]]
[[ -z $(git -C "$src" status --porcelain --untracked-files=all) ]]
cmp "$src/LICENSE" "$root/android/app/src/main/assets/licenses/llama.cpp.txt"
for abi in arm64-v8a x86_64; do
  build="$root/android/native-build/build/$abi"
  "$toolchain/cmake-3.22.1/bin/cmake" -S "$root/android/app/src/main/cpp" -B "$build" \
    -DCMAKE_TOOLCHAIN_FILE="$toolchain/android-ndk-r27c/build/cmake/android.toolchain.cmake" \
    -DANDROID_ABI="$abi" -DANDROID_PLATFORM=android-28 -DANDROID_STL=c++_static \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
    -DLLAMA_SOURCE="$src" -DPOCKETLORE_REVISION="$LLAMA_REVISION"
  "$toolchain/cmake-3.22.1/bin/cmake" --build "$build" --target pocketlore --parallel "${POCKETLORE_BUILD_JOBS:-4}"
  mkdir -p "$root/android/app/build/generated/nativeLibs/$abi"
  cp "$build/libpocketlore.so" "$root/android/app/build/generated/nativeLibs/$abi/"
done
