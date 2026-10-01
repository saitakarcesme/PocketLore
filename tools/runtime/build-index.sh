#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
python3 "$root/tools/runtime/fetch-index.py" --verify-only
toolchain=${POCKETLORE_TOOLCHAIN:-/home/isa/Android/atlas-toolchain}
for abi in arm64-v8a x86_64; do
  build="$root/downloads/sqlite/build-$abi"
  "$toolchain/cmake-3.22.1/bin/cmake" -S "$root/android/index-native" -B "$build" \
    -DCMAKE_TOOLCHAIN_FILE="$toolchain/android-ndk-r27c/build/cmake/android.toolchain.cmake" \
    -DANDROID_ABI="$abi" -DANDROID_PLATFORM=android-28 -DANDROID_STL=c++_static \
    -DCMAKE_BUILD_TYPE=Release -DSQLITE_SOURCE="$root/downloads/sqlite/sqlite-amalgamation-3530400"
  "$toolchain/cmake-3.22.1/bin/cmake" --build "$build" --parallel 2
  mkdir -p "$root/android/app/build/generated/nativeLibs/$abi"
  cp "$build/libpocketlore_index.so" "$root/android/app/build/generated/nativeLibs/$abi/"
  "$toolchain/android-ndk-r27c/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip" --strip-unneeded "$root/android/app/build/generated/nativeLibs/$abi/libpocketlore_index.so"
done
