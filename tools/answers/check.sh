#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
toolchain=${POCKETLORE_TOOLCHAIN:-/home/isa/Android/atlas-toolchain}
build=$(mktemp -d)
trap 'rm -rf "$build"' EXIT
src="$root/android/app/src/main/java/org/pocketlore/app"
"$toolchain/jdk/bin/javac" -d "$build" "$src/ResearchEngine.java" "$src/NativeRuntime.java" "$src/EvidencePrompt.java" "$src/AnswerEngine.java" "$root/android/app/src/test/java/org/pocketlore/app/AnswerEngineCheck.java"
"$toolchain/jdk/bin/java" -cp "$build" org.pocketlore.app.AnswerEngineCheck "$root/android/app/src/main/assets/water-science.tsv"
