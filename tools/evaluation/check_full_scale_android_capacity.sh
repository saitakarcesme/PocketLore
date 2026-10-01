#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
# Reproduction: run full-capacity/run.py on the dedicated emulator to generate
# measurements. Verification never replaces existing immutable failures or reruns inference.
python3 tools/evaluation/full-capacity/verify.py
