#!/usr/bin/env bash
# Online provisioning only. No research-time downloads.
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
source "$root/tools/answers/model.env"
cache="$root/downloads/answers/model"
mkdir -p "$cache"
if [[ ! -f "$cache/$MODEL_FILENAME" ]]; then
  curl --fail --location --retry 3 "https://huggingface.co/$MODEL_REPOSITORY/resolve/$MODEL_REVISION/$MODEL_FILENAME" -o "$cache/$MODEL_FILENAME.partial"
  echo "$MODEL_SHA256  $cache/$MODEL_FILENAME.partial" | sha256sum --check
  mv "$cache/$MODEL_FILENAME.partial" "$cache/$MODEL_FILENAME"
fi
echo "$MODEL_SHA256  $cache/$MODEL_FILENAME" | sha256sum --check
[[ $(stat -c %s "$cache/$MODEL_FILENAME") == "$MODEL_BYTES" ]]
