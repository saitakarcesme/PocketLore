#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
timeout --signal=TERM --kill-after=5s 90s python3 tools/evaluation/sparse-mapping/check.py
