#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 tools/evaluation/general-generation-repair/verify_device.py
exec python3 tools/evaluation/general-generation/verify.py
