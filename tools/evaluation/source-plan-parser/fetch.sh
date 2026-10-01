#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
root=downloads/source-plan-parser
mkdir -p "$root"
python3.12 -m venv "$root/venv"
"$root/venv/bin/pip" install -r tools/evaluation/source-plan-parser/requirements.lock
python3 - <<'PY'
from pathlib import Path
import urllib.request,hashlib
p=Path('downloads/source-plan-parser/en_core_web_sm-3.7.1-py3-none-any.whl')
expected='86cc141f63942d4b2c5fcee06630fd6f904788d2f0ab005cce45aadb8fb73889'
if not p.exists():p.write_bytes(urllib.request.urlopen('https://huggingface.co/spacy/en_core_web_sm/resolve/8fb6f8155286360bf5486fe399e2738d1df7ded2/en_core_web_sm-any-py3-none-any.whl').read())
assert hashlib.sha256(p.read_bytes()).hexdigest()==expected,'Changed model artifact'
PY
"$root/venv/bin/pip" install --no-deps "$root/en_core_web_sm-3.7.1-py3-none-any.whl"
