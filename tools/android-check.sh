#!/usr/bin/env bash
set -euo pipefail
project_root=$(cd "$(dirname "$0")/.." && pwd)
toolchain=${POCKETLORE_TOOLCHAIN:-/home/isa/Android/atlas-toolchain}
check_dir=$(mktemp -d)
trap 'rm -rf "$check_dir"' EXIT
"$toolchain/jdk/bin/javac" -d "$check_dir" "$project_root/android/app/src/main/java/org/pocketlore/app/ResearchEngine.java" "$project_root/android/app/src/test/java/org/pocketlore/app/ResearchEngineCheck.java"
"$toolchain/jdk/bin/java" -cp "$check_dir" org.pocketlore.app.ResearchEngineCheck "$project_root/android/app/src/main/assets/water-science.tsv"
