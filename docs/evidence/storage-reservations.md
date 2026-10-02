# Task420 storage reservations

Implemented bounded same-process reservations for model, pack, personal-document and optional-asset staging. The required Android build and six-fixture behavioral check pass on LLMRig. **Validation is host JVM plus Android compilation, not Android execution or whole-device safety.** No device commands, inference, recognition, downloads, user-data deletion or service changes were used.

## Freeze and implementation

CF-01 was read from the authorized proposal. Six public cases were frozen at commit `2114235`, SHA256 `cc03dad2c6e839fbf4de37d56376fd2e03a3e9d6df7be3eef7de190724f54be5`, before controller changes. The fixtures and raw receipt copies are under [storage-reservations](storage-reservations/fixtures.json); exact source hashes and raw run path are in [host receipt](storage-reservations/host/receipt.json) and [identity](storage-reservations/identity.json).

`ResourceStorage.Ledger` samples and admits under one synchronized lock, tracks live tokens, uses checked arithmetic and idempotent close, and refuses unknown usage. Android startup installs a fresh meter of app data, APKs and extracted native libraries with bounded inode-deduplicated traversal and allocated/logical maximum accounting. No optimistic zero fallback exists. Model stage/copy, NativePanel promotion, optional assets, PackLibrary installation and personal conversion hold scoped reservations; existing checksum, cancellation, selected-model rollback, catalog transactions and provenance logic remain in place. A small host compatibility fixture was adapted to provide an explicit measured fixture meter instead of relying on absent Android initialization.

## Six behavioral results

| Frozen fixture | Observed result |
| --- | --- |
| Available-byte reserve |4096 bytes at268,439,552 available passes; one byte less refuses. |
|45GB target |Exact45,000,000,000 projected passes; one byte above refuses target. |
|50GB hard cap |50,000,000,001 projected refuses hard cap; negative/unknown usage and checked-overflow inputs refuse. |
|Concurrent callers |Two threads compete for8192 bytes of allowance; exactly one admits while its token is held, the other refuses; retry after release succeeds. |
|Cancellation/failure release |Real production ModelImport handles before-read and during-read cancellation and injected read failure; staged file is removed and tokens release. Double-close does not subtract twice. |
|Rollback/retry |Malformed GGUF leaves retained selected fixture unchanged; same-process valid-magic fixture retry copies and atomically replaces it. No real model load or inference is claimed. |

The successful retry's observed retained-plus-stage logical footprint is48 bytes, final fixture23 bytes. This is one bounded coexistence observation, **not a sampled high-water mark for every failure**. Huge boundaries are virtual byte snapshots; lifecycle files are real tiny host files. The512MiB pack journal/database reservation is not experimentally allocated. Runtime limits are unchanged.

Mutation controls compile modified production ResourceStorage in isolated ignored directories: omitting outstanding reservations fails concurrency; omitting release fails lifecycle accounting. Both return nonzero, with full stderr retained. The unmodified production classes pass. Legacy import/recovery host checks pass16 assertions. Tests use128MiB Java heap and two active processors; these are configuration limits, not measured total RSS.

## Build and budget identity

Final application APK SHA256 `3dd57ac93d861878b35df3f4e7f978a32f1222dcd9bd6b1a23052219ef8716a2`; exact size is in identity.json. `bash tools/android-build.sh` passes with the existing two Gradle workers and2GiB heap. No APK was installed and no model or corpus pin changed. Build total memory peak was not measured. Intermediate successful build logs remain ignored under downloads/storage-reservations; no failed run was discarded or relabeled.

Historical390 measured41,728,667,648 allocated app+package bytes and41,757,052,928 sampled app/package/provider peak remain historical evidence for their old APK/device. They are not current420 measurements. The new meter samples the actual current app/package baseline at each future reservation; this task did not execute that Android meter or remeasure installed capacity. Task303 full-scale and410 API37 subset receipts are not transplanted.

## Accounting inventory and limitations

The detailed formula, allowances and covered paths are documented in [RESOURCES.md](../RESOURCES.md). App-owned current index/cache/notebook/rollback files enter the measured baseline; future writes by those paths are not all reserved. Bulk shard updates remain on their previous separate admission policy. Reader decompression/preview caches, notebook/SAF exports, external provider-owned copies, package-manager compiled artifacts outside app data, other apps and update peaks have unresolved accounting. Missing or inaccessible covered files fail closed; unobservable external ownership remains explicitly unknown. Nested tokens may reject a feasible transaction conservatively. Unreserved or external writers can consume space after sampling; this contract cannot guarantee ENOSPC never occurs.

Android startup/sampler execution, full installed corpus on this candidate, actual update peak, physical12GB RAM/GrapheneOS, zero observed network traffic, sustained lifecycle behavior, model quality, source rights and human acceptance remain open. This task does not accept400, complete410's instrumentation provenance, repair302 or establish competitor parity. The next distinct validation need is a bounded Android meter/admission observation on an approved existing environment, not another artificial boundary load.
