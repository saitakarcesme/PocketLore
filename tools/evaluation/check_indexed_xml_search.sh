#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
timeout 180s python3 tools/evaluation/indexed-xml/check.py
