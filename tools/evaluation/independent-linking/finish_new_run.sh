#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
run=downloads/independent-linking/run-20261001T125143Z
while [[ ! -f "$run/receipt.json" ]]; do sleep 5; done
python3 tools/evaluation/independent-linking/prepare.py "$run" downloads/independent-linking/scoring-1
downloads/independent-linking/venv/bin/python tools/evaluation/independent-linking/score.py downloads/independent-linking/scoring-1
/home/isa/Android/atlas-toolchain/jdk/bin/java -cp downloads/independent-linking/scoring-1/classes org.pocketlore.app.LinkHarness downloads/independent-linking/scoring-1/inputs downloads/independent-linking/scoring-1/final downloads/independent-linking/scoring-1/scores.tsv
