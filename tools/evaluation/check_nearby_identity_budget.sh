#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONDONTWRITEBYTECODE=1
timeout 60s python3 tools/evaluation/nearby-identity-budget/check.py
