#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
python3 "$root/tools/attachments/prepare.py"
toolchain=${POCKETLORE_TOOLCHAIN:-/home/isa/Android/atlas-toolchain}
cmake="$toolchain/cmake-3.22.1/bin/cmake"
for abi in arm64-v8a x86_64; do
 prefix="$root/downloads/attachments/install-$abi"
 mkdir -p "$prefix"
 compiler=aarch64-linux-android28-clang
 [[ "$abi" == x86_64 ]] && compiler=x86_64-linux-android28-clang
 bin="$toolchain/android-ndk-r27c/toolchains/llvm/prebuilt/linux-x86_64/bin"
 "$bin/$compiler" -fPIC -O2 -c "$toolchain/android-ndk-r27c/sources/android/cpufeatures/cpu-features.c" -o "$prefix/cpufeatures.o"
 "$bin/llvm-ar" rcs "$prefix/libcpufeatures.a" "$prefix/cpufeatures.o"
 common=(-DCMAKE_TOOLCHAIN_FILE="$toolchain/android-ndk-r27c/build/cmake/android.toolchain.cmake" -DANDROID_ABI="$abi" -DANDROID_PLATFORM=android-28 -DANDROID_STL=c++_static -DCMAKE_BUILD_TYPE=Release -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DBUILD_SHARED_LIBS=OFF)
 "$cmake" -S "$root/downloads/attachments/leptonica" -B "$root/downloads/attachments/lept-$abi" "${common[@]}" -DCMAKE_INSTALL_PREFIX="$prefix" -DBUILD_PROG=OFF -DENABLE_ZLIB=OFF -DENABLE_PNG=OFF -DENABLE_GIF=OFF -DENABLE_JPEG=OFF -DENABLE_TIFF=OFF -DENABLE_WEBP=OFF -DENABLE_OPENJPEG=OFF
 "$cmake" --build "$root/downloads/attachments/lept-$abi" --parallel 2 > "$root/downloads/attachments/lept-$abi.log" 2>&1
 "$cmake" --install "$root/downloads/attachments/lept-$abi" > "$root/downloads/attachments/lept-install-$abi.log"
 "$cmake" -S "$root/android/attachments-native" -B "$root/downloads/attachments/native-$abi" "${common[@]}" -DCMAKE_PREFIX_PATH="$prefix" -DATTACHMENT_SOURCE="$root/downloads/attachments" -DATTACHMENT_CPU_FEATURES="$prefix/libcpufeatures.a"
 "$cmake" --build "$root/downloads/attachments/native-$abi" --target pocketlore_attachments --parallel 2 > "$root/downloads/attachments/native-$abi.log" 2>&1
 mkdir -p "$root/android/app/build/generated/nativeLibs/$abi"
 cp "$root/downloads/attachments/native-$abi/libpocketlore_attachments.so" "$root/android/app/build/generated/nativeLibs/$abi/"
 "$toolchain/android-ndk-r27c/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip" --strip-unneeded "$root/android/app/build/generated/nativeLibs/$abi/libpocketlore_attachments.so"
done
