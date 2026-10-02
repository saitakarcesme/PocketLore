#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
mkdir -p downloads/android-16kb
exec 9>downloads/android-16kb/serial-5564.lock
flock -n 9 || { echo 'Existing 5564 compatibility check owns the serial'; exit 1; }
exec python3 tools/evaluation/modern-integrated/check.py "$@"
