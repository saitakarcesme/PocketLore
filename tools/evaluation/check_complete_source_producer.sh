#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 tools/packs/complete-source/test_compact.py
python3 tools/packs/complete-source/test_producer.py
python3 tools/evaluation/verify_complete_source_producer.py
