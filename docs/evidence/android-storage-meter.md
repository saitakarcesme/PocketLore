# Task430: actual Android storage meter

The bounded check passes on **existing emulator-5560, API35, 4096-byte pages**. Production storage code is unchanged from accepted420; this task adds instrumentation and evidence validation. It does not accept400 or repair410's historical instrumentation provenance. No inference, recognition, new models, downloads, full-capacity suite, modern suite, service changes, reboot, uninstall or data clearing occurred.

## Exact execution binding

Successful invocation: `20261002T033350Z-02a52f97`, source checkpoint `a647d50`. Before building/installing, the checker captured the Git commit, SHA256 of tracked Android/tool inputs, JDK release and compile SDK JAR hashes, build configuration and run ID. Its [source manifest](android-storage-meter/run/source-inputs.json) SHA256 is `126835de90d832440c801ebde632b7692ff87ddca7ee60b99ad2877ee692f46e`. Inputs were checked unchanged after build and execution. The instrumented receipt echoes that exact manifest hash; compilation and both installed-package byte hashes bind the test to this invocation. This prospective binding does not manufacture an attestation for410.

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Production APK |22,702,878|`3dd57ac93d861878b35df3f4e7f978a32f1222dcd9bd6b1a23052219ef8716a2`|
| Instrumentation APK |416,198|`80e11cc5bba361c35ec9738943360c6857c2f8561ff362601adc3a5d1b47d7dd`|

Both installed hashes equal their freshly built hashes immediately after installation and after testing. Earlier installed identities are also recorded. Boot ID stayed `59ebd1a1-2fbf-4b25-aed7-2672c2d46604`; font stayed1.0. Transport returned0 with instrumentation completion-1 and a complete parsed receipt. Source/artifact/command manifests and raw stream are committed in the bounded evidence packet; no APK/model binaries are staged. Raw persistent-file path inventory stays in the original rig run to avoid publishing user-owned paths; its before/after digest is identical: `93b7b1f1fb0864e966fd60a48af9843c79c7fedd4911bd86c4aa7dc6edfb84c4` across1,211 records. See [retention receipt](android-storage-meter/retention.json).

## Independent filesystem reconciliation

The actual `StorageApplication` initialized the process ledger. Its real sampler measured app data, APKs and any extracted native-library root. Separate `/system/bin/stat` subprocesses, in batches of at most64 paths, emitted device/inode/logical-size/allocated-block rows. Python independently recomputes deduplicated totals from those raw rows; it does not accept the meter number alone. Directory enumeration is bounded. Snapshots immediately before and after each observation must agree exactly.

| Sample | Logical bytes | Allocated bytes | Sum of per-inode maximum / actual meter | Live reserved bytes |
| --- | ---: | ---: | ---: | ---: |
| Before fixture contents |3,270,789,852|3,279,458,304|3,279,465,246|0|
| During model-stage copy |3,270,793,968|3,279,474,688|3,279,481,630|1,056,768|
| After8192-byte stage / inode revisit |3,270,798,064|3,279,478,784|3,279,485,726|0|
| After bounded fixture operations |3,270,811,431|3,279,519,744|3,279,526,686|0|

The during-copy covered-byte increase was16,384 bytes, including filesystem allocation for the retained and staged fixtures; the final fixture-operation increase was61,440 bytes. The ledger's projected total includes live reservations, so reconciliation explicitly separates measured bytes from reserved bytes. The sum of per-inode maxima need not equal the maximum of aggregate logical/allocated totals. These are discrete observations, not continuous high-water measurements. After cleanup, app-directory `du -sk` reported3,180,416 KiB; this excludes APK/package roots and is not directly the covered-total column. `/data` available space was1,920,120 KiB.

Android denied creation of a distinct hard link. That failed fixture is preserved; no hard-link creation success is claimed. The production traversal was instead invoked twice on the same real file inode through ordinary and `./` paths using a shared seen set; the second contribution was zero. Actual missing-path measurement failed. An actual unsupported symlink caused the live global meter/admission to fail closed; the fixture symlink was then removed. These are device observations, not the host's simulated45/50GB boundaries.

## Lifecycle and retention

The successful receipt contains29 assertions. Two threads competed against the real current meter: only one could hold a1,696,698,368-byte reservation. **Those bytes were a virtual reservation only, never allocated.** Both threads released, and the ledger returned to zero.

Production `ModelImport.copy` held its1,056,768-byte reservation while writing an8192-byte fixture. Success, before-read cancellation and injected provider read failure released reservations; failure paths deleted their stage. A same-process retry succeeded. The retained tiny GGUF-magic fixture stayed byte-identical. It is not a usable model and was never loaded; existing real models were checked through persistent-file retention hashes.

Actual personal TXT conversion, PackLibrary installation and exact portable export ran under the real startup meter in the invocation-owned directory. Optional-asset installation rejected an invalid eight-byte asset and released its reservation. No optional recognition ran. All fixture content was removed only after this invocation successfully created its fresh directory; no preexisting path is eligible for cleanup. Final live reservations were zero and all original persistent file hashes matched. No Activity UI flow or stalled-provider cancellation latency is newly claimed.

## Failures preserved and approach changes

[Original artifact hashes](android-storage-meter/original-artifacts.json) cover every attempt, with actual failed receipts/build logs in `android-storage-meter/failures`:

- `032634Z-c032c00f`: ambiguous Java Process type; compilation failed before installation.
- `032708Z-d1272aae`: subprocess observation returned Permission denied; startup and owned cleanup passed, comparison incomplete.
- `032904Z-3dc09196` and `033004Z-e75ff656`: shell completion sentinel absent; no successful comparison claimed.
- `033116Z-29f8bbab`: direct stat established exact startup agreement, but the test incorrectly compared projected reservation bytes with measured filesystem bytes during copy; that assertion failed. Its during-sample numbers were not retained, and are not reconstructed as evidence.
- `033216Z-eb3b4fa6`: startup/during-copy reconciliation passed; Android denied hard-link creation and the invocation failed.

The observation path changed to direct stat execution; projection and measurement were separated; actual inode revisit replaced unavailable hard-link creation with its limitation visible. No production safety assertion was removed. All device-attempt failure receipts report owned fixture cleanup and zero final reservations. The later passing invocation does not replace them.

## Required checks and limits

`bash tools/android-build.sh` passes separately, as does `bash tools/evaluation/check_android_storage_meter.sh`. Builds use the existing two Gradle workers and2GiB heap; actual total build RSS was not measured. The behavioral checker binds fresh source/build/test/device identities, recomputes stat rows, verifies persistent retention, boot/font continuity and cleanup, and rejects missing raw transport, corrupt JSON, stale run and changed installed-test identity using copies of actual evidence. Negative controls never mutate original receipts or devices.

Current full corpus, providers, other apps, package-manager compiled artifacts outside covered roots, unreserved writers, update peaks, sustained operation, physical ARM64/GrapheneOS12GB RAM, observed traffic, generation quality, rights and human release remain open. Conservative double-accounting remains intentional. This roughly3.28GB subset observation is not303/390 full installed capacity, modern5564 evidence, whole-device enforcement or competitive proof. No further load or suite replay is needed for this bounded result.
