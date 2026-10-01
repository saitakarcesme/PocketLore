#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
downloads/source-plan-parser/venv/bin/python tools/evaluation/equation-plan/verify.py
