# Integrated candidate regression — task390

The bounded integration check passes for the accepted task310/330/340/350/360/370/380 application, rebuilt and installed as one exact APK: **9c71a32dbc2deac3d650c6849a335379bd2b005c1516437c613bcd0fcff7dd70**, **22,702,878 bytes**. Production application sources are unchanged from `8f23811bcd32aaf6cd9fc6364d1dd7afa540ba48`; repairs affect validation readiness, guard baselines and missing cross-feature tests. This is not release, quality, physical-device or competitive acceptance.

## Execution and evidence

`bash tools/android-build.sh` passes with installed offline tooling, configured Gradle maximum2 workers and2GiB heap. This configuration is not a measurement of the whole build process tree's peak RAM. `bash tools/evaluation/check_integrated_candidate.sh` executes seven existing behavioral lanes serially; its explicit `--reuse <run>` mode reuses only complete passing lanes with the identical APK and installed identity, preserving original times. Final assembly reused completed runs rather than repeating recognition or successful UI checks. `bash tools/evaluation/check_integrated_candidate.sh downloads/integrated-candidate/20261002T012806Z` verifies the frozen run without any device work.

Complete raw output: `downloads/integrated-candidate/20261002T012806Z`, with301 hash-bound files in its manifest. Text receipts are committed under `integrated-candidate/passing/`; screenshots remain in the ignored raw run and original UI run with their hashes retained. No APK, model or binary input payload is committed. Mutation tests on disposable copies reject a changed report, missing report and wrong candidate identity. ELF inspection, assets, raw behavior results, installed APK hashes, actual storage and historical failures are not replaced by file-presence checks.

The existing source-backed competitor matrix at `scale-workers/competitor-features/repo/output` was inspected. It is a static planning inventory with unresolved claim evidence/acquisition/snapshot limitations, not installed rival behavior or a matched comparison. No competitor code or branding was reused.

| Lane and existing emulator | Actual current-candidate coverage | Result |
|---|---|---|
| Product UI,5560 | Default and2× font, keyboard/Back, edit/result restoration, source reading, notebook/bookmark/export persistence, genuinely blocked provider write cancellation, source access while blocked, exact retry, Activity destruction and cold restart |112 assertions in each of3 passes; no generated research answer |
| Personal documents,5560 | TXT/MD/quotedCSV/JSON/textPDF extraction/provenance; actual Library→personal import→return→immediate search; source reader, exact export/reimport, corruption/cancellation and restart |82 checks plus restart; explicitly unloaded model and verified `invokedModel=false` |
| Attachments,5560 | Existing real local OCR/WAV engine controls, absent/error/noise/cancellation and microphone boundaries; added actual Research→recognizer→edited-result→question handoff for both image and WAV |73 checks; recognized input stays editable, unsubmitted and labeled not source evidence |
| Model management,5560 | Pinned provider import, optional1.5B native load/selection, baseline restoration, actual failed native GGUF preflight rollback and missing selection, retained-object storage |11 import and10 selection checks; generation explicitly disabled, no token output, zero live generation contexts |
| Nearby travel,5560 | Existing diverse-place searches and manual/GPS interfaces, reviewed three-city six-field cards, exact source readers/portable exports and rejection controls |98 checks; no new fields, positive diet data, live hours, routing or corpus-wide rights claimed |
| Verified cache,5562 | Existing full31-shard catalog, actual28,440,308-byte raw block, cold/warm verified reader, cancellation, eviction, unchanged ordered lexical results and corruption control |185 checks; cold3118.32ms, warm1.59/1.54ms; warm temporary disk0 bytes |
| Specialist collection,5562 | Exact eight-document/64-section archive, original formula/code reconstruction, source/rights hashes and offsets, combined search, eight real readers, corruption/cancel/export/disable and restart |50 import and19 restart checks; reader opens32–151ms; no generated-answer qualification |

The OCR handoff contains actual `OFFLINE LIBRARY` / `Review every word.` recognition; the WAV handoff contains the real pinned JFK sample transcription. Tests append a visible edit and verify that exact edited string reaches the question field without research submission. They do not pass canned input off as recognition. Recognition jobs run serially under existing bounded CPU settings. No language-model generation, new research inference, downloads, corpus expansion, private holdout, service/runtime changes or interference with the protected inference process occurred. Native model loading is deliberately tested separately from generation.

## Concrete repairs and preserved failures

1. Initial preflight wrongly required `model-selection` on5562. That emulator legitimately uses the supported legacy `files/model.gguf` path. Both the legacy state and pointer-selected5560 state are now recorded and preserved; no migration or model change was forced.
2. The task310 structural guard still compared NativePanel and ScaleWiki against the pre350/pre370 base. It now pins the accepted integrated base, while retaining byte-identical protected-code assertions, permission checks and contrast/control checks. The old failure is retained.
3. UI testing clicked the brief control during model initialization after Activity recreation. An explicit enabled-control readiness wait fixes the test; the original personal-evidence/no-quote assertion remains. Fresh screenshot inspection shows the unavailable result with no unrelated quotes; large-font screenshots use the scrollable content and two-row navigation.
4. The new document-test unload call initially failed Java compilation because reflection threw a checked exception inside a Runnable. Reflection now occurs before that Runnable; the failed compiler log remains.
5. The new recognition handoff originally attempted to open its child before the parent library initialized. The repaired test records `handoff_initial_importing=true`, `handoff_initial_engine_missing=true`, then waits for library and foreground readiness before exercising the real visible control. It retains actual recognition, editing, result delivery and non-submission assertions.

These were concrete integration-test assumptions, not changes to answer support or production behavior. Failures are retained under `integrated-candidate/failures/` and raw run locations. No historical failure was relabeled passed. Successful lanes were reused only after verifying the same current application identity.

## Identities, storage and memory

All lanes rebuilt the same candidate, and each installed APK hash matched it. Current actual ELF LOAD/RELRO and uncompressed APK16KB offsets pass for all three native libraries on both ARM64 and x86_64 (`passing/alignment.json`). This is binary alignment evidence, not fresh API37 execution:5564 remained untouched. Actual execution here is API35 x86_64 on5560/5562; native ARM64, modern5564 load/inference and physical16KB behavior remain separately gated.

The production pin remains Qwen2.5 0.5B Q4_K_M,491,400,032 bytes, SHA256 `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`.5560 selects the retained object via `model-selection`;5562 has the legacy file and no pointer. Before/after model, pack-catalog and bulk-catalog hashes match. The optional1.5B object is loaded only on5560, then removed by its owned fixture cleanup; it is not deployed or counted as installed on the full-corpus device. Native failure reports `Cannot preflight GGUF model` followed by exact baseline reload. Optional load7681ms; loaded-process PSS1,197,857KiB; this is a load snapshot, not generation memory or quality.

Both emulators have actual hash-verified optional recognition assets: English Tesseract4,113,088 bytes (SHA7d4322bd…70b2) and whisper tiny.en77,704,715 bytes (SHA921e4cf8…0b1f), totaling81,817,803 bytes. Exact full digests are in `passing/storage-audit/*recognition-hashes.txt` and existing `tools/attachments/models.json`. Catalog snapshots retain exact edition/shard pins; current cache reads verify their source blocks/records. This task did not rehash every byte of the unchanged41GB corpus or grant rights based on its hashes.

| Current observed footprint |5560 subset |5562 full existing corpus |
|---|---:|---:|
| Final app tree apparent/logical bytes (`du -sb`, directory sizes included) |3,220,762,842 |41,702,932,510 |
| Final app tree allocated bytes (`du -sk` ×1024) |3,227,152,384 |41,705,693,184 |
| Final logical app tree + APK bytes |3,243,465,720 |41,725,635,388 |
| Final allocated app tree + installed package directory |3,249,872,896 |41,728,413,696 |
| Largest sampled allocated app + package + test-provider tree |4,368,457,728 |41,756,803,072 |

Installed package directory is22,720,512 allocated bytes on each emulator. The full-corpus sample peak includes real oversized reader temporary storage; the subset sample peak includes the temporary optional model transaction. Test-provider storage is labeled separately in raw samples and included in the last row; unrelated Android/OS/services and host source caches are not application assets. The observed full-corpus envelope is below45GB target/50GB hard cap. These are sampled observations of the current operations, **not** a new full shard-update peak or proof that every future model combination fits. Prior303/API35 receipts are historical and are not transferred to this candidate or5564.

There are63 samples per serial in the final merged sampling record.5560 has62 complete logical/allocated samples: one logical measurement is missing at01:25:41Z during model management; the original sampler did not retain its error output, and no cause/value is invented. Future failures record command output. Sampling occurs nominally every3 seconds plus sequential command time, not continuously; peaks may occur between samples. Reused samples retain their original timestamps and source run.

Recognition PSS maximum among251 samples:298,255KiB. Full-reader PSS snapshots41,227–41,499KiB; specialist reader/reload snapshots62,892/73,508KiB. These are emulator process measurements, not host RAM relabeled as phone RAM, and are not simultaneous loaded-model/KV/reader peak or thermal evidence.

## Remaining gates

Physical Android/GrapheneOS and ARM64 execution, current API37 runtime qualification, TalkBack/human usability, sustained combined model/KV/readers, complete update/install peaks, clean-machine reproduction, signing ownership and final release remain open. Generated-answer support/usefulness, independent unseen topic/source-held-out evaluation and matched named-rival/frontier comparisons remain open; development regressions do not establish generalization. Bulk wiki/place rights remain limited/browse-only; three reviewed GeoNames records and eight specialist documents do not clear the bulk corpus or failed302 line. No model-role changes, quality tuning, production key, publication, push, main advancement or orchestration changes occurred. Stop after this bounded checkpoint; independent criticism of its exact source and reports is recorded separately.
