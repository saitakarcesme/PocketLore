#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/../.."
status=0
python3 tools/evaluation/review-bound-generation/check.py || status=1
python3 tools/evaluation/general-generation-repair/verify_device.py || status=1
python3 tools/evaluation/general-generation/verify.py || status=1
python3 tools/evaluation/cross-model-support/verify.py || status=1
exit "$status"
