# Public personal-document behavior fixtures

These are constructed format tests, not factual corpus or held-out quality data. All original fixture hashes are frozen in `docs/evidence/documents/fixtures.json`. Existing ignored bytes live in `downloads/documents-fixtures`; checks never regenerate them.

To recreate missing fixture bytes on the rig:

```sh
UV_CACHE_DIR=/tmp/pocketlore-uv-cache uv venv downloads/documents-tools
UV_CACHE_DIR=/tmp/pocketlore-uv-cache uv pip install --python downloads/documents-tools/bin/python -r tools/evaluation/documents/fixture-requirements.txt
downloads/documents-tools/bin/python tools/evaluation/documents/fixtures.py
bash tools/android-build.sh
bash tools/evaluation/check_documents.sh
```

Default serial is emulator-5560, Android15/API35. `POCKETLORE_DOCUMENTS_SERIAL` changes only this checker. It requires an existing project model and pack catalog to measure preservation; no emulator launch, wipe, service change or downloads occur in the check. The test APK's provider exposes only constructed fixture files. No provider component is included in the product APK.

Each run has a new ignored `downloads/documents-runs/<UTC>/` directory, test-library directory and raw receipt. Do not delete old failed runs or overwrite immutable receipts. Fixture hashes are checked before uploading, and altered/missing copies are deliberately rejected. Actual Android assertions exercise extraction, exact spans, malformed input, forged PDF extraction with recomputed hashes, corruption/limits, cross-instance transactions, stalled input/output cancellation, Activity recreation, search/source controls, export/reimport and process restart. A pass marker alone is insufficient: the host checks required assertion names, current APK identities, preserved model/catalog hashes, manifest permissions and restarted retrieval. Final permission/DEX inspection rejects INTERNET and Google Play Services references.

The UI import/export test drives Activity result handling with a real local content provider rather than automating the system file-picker's file selection. It temporarily adds one known public fixture collection, opens its actual source dialog, then removes that exact addition and requires the original catalog hash. Library tests use isolated directories. Failure before cleanup needs explicit inspection/recovery of the known fixture, never an app data reset. `DocumentsRestartInstrumentation` preserves the bounded recovery used for the recorded test crash; ordinary checks use the main instrumentation's restart phase.
