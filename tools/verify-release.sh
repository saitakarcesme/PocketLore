#!/usr/bin/env bash
# Offline artifact/behavior verification; fresh destructive emulator demo is separate.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
exec python3 "$root/tools/release/verify.py" "$@"
