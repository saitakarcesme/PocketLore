#!/usr/bin/env bash
# Foreground, isolated task AVD. Does not modify any existing AVD or service.
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
toolchain=${POCKETLORE_TOOLCHAIN:-/home/isa/Android/atlas-toolchain}
serial_port=${POCKETLORE_EMULATOR_PORT:-5560}
export ANDROID_HOME="$toolchain/sdk"
export ANDROID_AVD_HOME="$root/downloads/runtime/android-user/avd"
avd="$root/downloads/runtime/android-user/pocketlore_runtime_api35.avd"
if "$ANDROID_HOME/platform-tools/adb" devices | grep -q "emulator-$serial_port[[:space:]]"; then
  echo "Port $serial_port already has an emulator; use that instance or choose a different port." >&2
  exit 1
fi
mkdir -p "$ANDROID_AVD_HOME" "$avd"
if [[ ! -f "$avd/config.ini" ]]; then
  cat > "$ANDROID_AVD_HOME/pocketlore_runtime_api35.ini" <<INI
avd.ini.encoding=UTF-8
path=$avd
target=android-35
INI
  cat > "$avd/config.ini" <<'INI'
avd.ini.encoding=UTF-8
abi.type=x86_64
hw.cpu.arch=x86_64
hw.cpu.ncore=2
hw.ramSize=2048
hw.lcd.width=1080
hw.lcd.height=2400
hw.lcd.density=420
hw.keyboard=yes
hw.gpu.enabled=yes
hw.gpu.mode=swiftshader_indirect
hw.audioInput=no
hw.audioOutput=no
hw.sdCard=no
disk.dataPartition.size=4G
image.sysdir.1=system-images/android-35/default/x86_64/
tag.id=default
target=android-35
PlayStore.enabled=no
INI
fi
exec "$ANDROID_HOME/emulator/emulator" -avd pocketlore_runtime_api35 -port "$serial_port" \
  -no-window -no-audio -no-snapshot -no-boot-anim -gpu swiftshader_indirect -memory 2048 -cores 2
