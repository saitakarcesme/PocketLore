#!/usr/bin/env bash
# Explicit online provisioning only. Build and verification never fetch assets.
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
source "$root/tools/runtime/pins.env"
cache="$root/downloads/runtime"
mkdir -p "$cache"
if [[ ! -d "$cache/llama.cpp/.git" ]]; then
  git init "$cache/llama.cpp"
  git -C "$cache/llama.cpp" remote add origin https://github.com/ggml-org/llama.cpp.git
  git -C "$cache/llama.cpp" fetch --depth 1 origin "$LLAMA_REVISION"
  git -C "$cache/llama.cpp" checkout --detach "$LLAMA_REVISION"
fi
[[ $(git -C "$cache/llama.cpp" rev-parse HEAD) == "$LLAMA_REVISION" ]]
[[ -z $(git -C "$cache/llama.cpp" status --porcelain --untracked-files=all) ]]
if [[ ${1:-} == --model ]]; then
  if [[ ! -f "$cache/$MODEL_FILENAME" ]]; then
    curl --fail --location --retry 3 "https://huggingface.co/$MODEL_REPOSITORY/resolve/$MODEL_REVISION/$MODEL_FILENAME" -o "$cache/$MODEL_FILENAME.partial"
    echo "$MODEL_SHA256  $cache/$MODEL_FILENAME.partial" | sha256sum --check
    mv "$cache/$MODEL_FILENAME.partial" "$cache/$MODEL_FILENAME"
  fi
  echo "$MODEL_SHA256  $cache/$MODEL_FILENAME" | sha256sum --check
fi
