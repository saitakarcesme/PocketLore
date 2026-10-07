#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
exec python3 -B "$root/tools/evaluation/ocr-publication-deadline/check.py"
