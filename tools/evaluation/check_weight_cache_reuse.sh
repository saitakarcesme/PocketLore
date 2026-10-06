#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
# Offline validation only. Never starts model or fixture execution.
timeout --signal=TERM --kill-after=5s 120s python3 tools/evaluation/weight-cache/check.py
