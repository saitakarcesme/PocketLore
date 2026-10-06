#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
# The model sample is a separately recorded one-time operation. Never silently
# rehash/replay it when receipts are stale or missing.
timeout --signal=TERM --kill-after=5s 90s python3 tools/evaluation/native-cache/check.py
