#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 tools/packs/complete-source/safety/test_ownership.py
python3 tools/evaluation/verify_complete_source_ownership.py
