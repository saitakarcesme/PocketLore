#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
# Validation only: never silently launch or retry expensive model execution.
timeout --signal=TERM --kill-after=5s 90s python3 tools/evaluation/strong-native-host/check.py
