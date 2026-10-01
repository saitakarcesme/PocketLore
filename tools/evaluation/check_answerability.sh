#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
exec python3 "$root/tools/evaluation/evaluate_answerability.py"
