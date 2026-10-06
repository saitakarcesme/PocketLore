#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
# Verification only. No automatic native/model execution or cache manipulation.
timeout --signal=TERM --kill-after=5s 90s python3 tools/evaluation/weight-fault/check.py
