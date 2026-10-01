#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
tc=${POCKETLORE_TOOLCHAIN:-/home/isa/Android/atlas-toolchain}
python3 tools/evaluation/broad-answers/prepare_regressions.py
mkdir -p downloads/broad-answers/unit
"$tc/jdk/bin/javac" -d downloads/broad-answers/unit android/app/src/main/java/org/pocketlore/app/{ResearchEngine,EvidencePrompt,AnswerEngine,NativeRuntime}.java tools/evaluation/broad-answers/SharedPropertyCheck.java android/app/src/test/java/org/pocketlore/app/TemporalScopeCheck.java
"$tc/jdk/bin/java" -cp downloads/broad-answers/unit org.pocketlore.app.SharedPropertyCheck downloads/broad-answers/regressions
"$tc/jdk/bin/java" -cp downloads/broad-answers/unit org.pocketlore.app.TemporalScopeCheck tools/evaluation/regressions/temporal-scope
python3 tools/evaluation/broad-answers/verify.py
