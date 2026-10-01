#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
mkdir -p "$root/downloads/distribution"
bash "$root/tools/android-build.sh" pocketloreDistributionDependencies -I "$root/tools/distribution/resolved.gradle" > "$root/downloads/distribution/current-resolution.log" 2>&1
python3 "$root/tools/distribution/verify.py"
