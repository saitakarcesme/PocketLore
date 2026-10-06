#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONDONTWRITEBYTECODE=1
exec timeout 180s python3 tools/evaluation/indexed-semantic-final/check.py
