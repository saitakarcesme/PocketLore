#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
tc=${POCKETLORE_TOOLCHAIN:-/home/isa/Android/atlas-toolchain}
python3 tools/evaluation/complete-claims/prepare_regressions.py
mkdir -p downloads/complete-claims/unit
"$tc/jdk/bin/javac" -d downloads/complete-claims/unit android/app/src/main/java/org/pocketlore/app/{ResearchEngine,EvidencePrompt,AnswerEngine,NativeRuntime}.java tools/evaluation/complete-claims/CompleteClaimCheck.java android/app/src/test/java/org/pocketlore/app/TemporalScopeCheck.java
"$tc/jdk/bin/java" -cp downloads/complete-claims/unit org.pocketlore.app.CompleteClaimCheck downloads/complete-claims/regressions
"$tc/jdk/bin/java" -cp downloads/complete-claims/unit org.pocketlore.app.TemporalScopeCheck tools/evaluation/regressions/temporal-scope
python3 tools/evaluation/complete-claims/verify.py
