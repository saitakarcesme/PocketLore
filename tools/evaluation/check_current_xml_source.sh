#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
timeout 120s python3 tools/evaluation/current-xml/check.py
