#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
run=downloads/fact-frames/run-20261001T133400Z
while [[ ! -f "$run/receipt.json" ]]; do sleep 5; done
python3 tools/evaluation/fact-frames/prepare.py "$run" downloads/fact-frames/replay-1
