# Compatible model management — task350 repair-1

The required build and model-management behavior check pass on **API35 x86_64 emulator-5560**. This is a model-storage/runtime feature, not a stronger-model quality selection, physical-device qualification or competitive result. Failed checkpoint7f6137b and its missing native-failure coverage remain historical evidence.

## Implementation and identity

Settings now offers a pinned local model catalog, explicit external-browser setup/download confirmation, local GGUF import, installed-model selection, current name/hash/runtime display, inactive deletion and active removal. Research retains no INTERNET permission and no GMS dependency; the separate browser uses its own network only after a user action. No downloader, global model preference, service or production model.env was changed.

The catalog pins the existing licensed Qwen2.5 0.5B Q4_K_M demo baseline, Qwen2.5 1.5B Q4_K_M and Qwen3 1.7B Q8_0 optional experiments. Exact repository revisions, filenames, bytes, SHA-256 and Apache-2.0 identity are in `ModelCatalog.java`, matching existing model pins/notices; no new weights were downloaded. The 4B host candidate is not offered or relabeled deployed. Catalog inclusion is not independent answer-quality or phone admission approval.

Import copies through the existing cancellable DocumentInput/ModelImport path, verifies a known size and exact pinned hash, then executes native GGUF/template/resource validation before promotion. Only a successfully loaded model changes the atomic selection record. Previous files remain retained; failed native selection releases the failed session and reloads the prior selection, unless cancellation, destruction or memory suspension requests otherwise. Missing/invalid saved selection fails closed. Original external model files are not deleted.

An initial hard-link design failed under Android SELinux (`link` denied). It was replaced with an `AtomicFile` identity record pointing to retained files, with no duplicate active weight. Existing `files/model.gguf` remains the legacy baseline file. Removing the active model also deletes its retained bytes; clearing selection alone is not advertised as removal. A failed deletion can leave an inactive file that remains removable through the catalog.

The bounded native profile is unchanged: one session, two CPU threads, 2048 context tokens and existing model/KV/compute admission checks. Storage admission counts app data and APK, retains all model copies, budgets incoming stage plus a conservative equal-size provider copy and a256MiB reserve, distinguishes the45GB target from the50GB hard rejection, and checks actual free space. This accounting is not a measurement of all external provider implementations, ART/OS storage or full-candidate update peaks.

## Actual validation

[Passing raw run](model-management/passing/receipt.json), [import report](model-management/passing/import.json), [selection report](model-management/passing/select.json), [required build](model-management/build-required.log) and [checker output](model-management/check-repair.log) are preserved. The checker hashes real assets and receipts and rejects changed/missing run artifacts; it does not use file presence as success.

| Observation | Result |
|---|---|
| Integrated APK | SHA-256 `aac939137e42123b748276600e40ce984ba21bb863afe45084e7ba8e565c6249`; installed hash matches the built candidate. |
| Baseline | `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`,491,400,032 bytes; real local provider import, native load, checksum and retained selection checked. |
| Optional1.5B | `6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e`,1,117,320,736 bytes; existing rig asset transferred once into the app catalog, verified and actually selected through NativePanel. |
| Load timing |7,980ms from selection call through identity verification, native loading and completed UI callback; includes hashing, not pure native load time. |
| Bounded execution | One local chat token returned `Hello`; unverified runtime smoke output, not a supported research answer or usefulness score. |
| Native-load rollback | An existing truncated GGUF reaches the actual post-identity native transaction boundary; `NativeRuntime.load` returns `Cannot preflight GGUF model`, the prior baseline is reloaded and its identity/selection remain unchanged. |
| Other negatives | Changed checksum, hard-budget overflow, cancelled copy/stage cleanup, missing installed model; inactive model deletion and baseline reselection pass. |
| Observed memory | Optional loaded process PSS1,199,687KiB; final baseline PSS590,472KiB. Snapshots, not allocation maxima or phone measurements. Native resource counters show no live generation context at the pre-generation sample and must not be interpreted as zero model memory. |
| Observed app data | With optional model4,326,654,154 unique bytes; after test-owned optional removal3,209,333,418 bytes. APK bytes are separate in the receipt; these are the existing5560 subset, not the full31-shard inventory. |
| Retention/offline | Saved baseline, active pack catalog and OCR/speech assets retain exact before/after hashes; installed package has no INTERNET permission. |

The native-failure regression deliberately enters the same transaction after the normal checksum boundary so a malformed file can exercise native failure. It is not an admissible catalog artifact or a claim that a corrupt file passes import verification. Production paths continue to verify pins before that transaction. The optional file is pre-positioned to avoid two1.1GB provider/staging copies on this small emulator; actual provider import is exercised with the baseline. Catalog control reachability is tested; external browser networking and the full Android picker journey are not newly qualified by this test.

The original public protocol is retained, with a separate [repair amendment](../../tools/evaluation/model-management/repair-protocol.json). Earlier import assertions, SELinux failure, shell disk-query permission failure, and receipt-resume variable failure remain in raw logs. The missing-file rollback test is retained separately from the new real JNI-failure regression. No historical inference matrix was regenerated.

## Reuse, review and open gates

The requested competitor output was found at the same worker's `repo/output/COMPETITOR-FEATURE-MATRIX.md`, rather than the absent top-level output directory. It describes source-inspected model-selection/setup journeys, explicitly not tested competitor behavior. No competitor source, branding or assets were copied. Its exact SHA is retained with the evidence manifest.

Independent implementation review identified the active-file deletion problem; the repair removes retained bytes rather than only a link. Final independent criticism is recorded separately when available. Builder tests do not replace canonical review, human acceptance or unseen evaluation.

Remaining work: distinct frozen supported-output and independent quality qualification before promoting an optional model; physical ARM64/GrapheneOS and exact-candidate API37 load/cancel/reload; actual full-catalog storage/update measurement including external provider copies and code overhead; final distribution/release identity. Qwen3 1.7B is cataloged but not loaded in this task. Provider-open/regular-file stalls remain inherited platform limits. This task does not waive the12GB phone RAM or50GB installed limit.

[Independent read-only criticism](model-management/independent-review.json) of checkpoint1dbf9bf found no blocking defect in the bounded source/receipt review; it explicitly leaves optional-model quality, full-capacity storage and physical-device memory qualification unproven. This is not canonical promotion or human acceptance.
