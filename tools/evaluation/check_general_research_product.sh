#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
# Task460 remains an immutable historical candidate in its original checkpoint.
# Current product checks must bind the NEW candidate, never relabel old receipts.
if [[ "${1:-}" == "--historical-460" ]]; then
  shift
  exec python3 tools/evaluation/general-research/check.py "$@"
fi
if (( $# != 0 )); then
  echo 'Current candidate audit takes no device arguments; task480 device execution requires an explicit exclusive5564 lease.' >&2
  exit 2
fi
exec python3 tools/evaluation/reference-expansion/verify.py --general-research
