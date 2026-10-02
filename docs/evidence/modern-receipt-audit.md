# Task410: existing API37 receipt audit

Conclusion: **incomplete source-to-test-binary binding; supported existing run receipts**. This is an offline evidence audit, not task400 acceptance or a new compatibility run. No device commands, builds, recognition, inference, downloads or services were invoked. Accepted390 checkpoint `5ea7a6d` remains the product baseline; candidate `4e5652009485a86b80e04415cbce740b36472db7` was inspected through Git only.

## Freeze and provenance

The original `downloads/modern-integrated/20261002T025132Z-be41f6a6` and explicitly authorized check log were SHA256-frozen before content analysis: 259 files, recorded in [frozen-artifacts.json](modern-receipt-audit/frozen-artifacts.json). The required check log hash is `d450580cc216eb6fe0d68c805c022c9c22edf95682652654b4bd9b091634dca9`; its PASS refers to this run, not the earlier reboot failure. Original raw streams and screenshots remain at those paths; decoded receipts and transport text without binary chunks are included in the bounded packet. `packet-files.json` pins those copies; the audit independently reconstructs every streamed file and compares exact bytes to the original decoded files, including screenshots.

The captured executed checker SHA256 `9b4bc3f85ede866548848db7670d5aa525540e39689394daab11edbace249f32` exactly matches the candidate Git blob. [lineage.json](modern-receipt-audit/lineage.json) pins the candidate's changed Android/test/tool sources and parent. The production `android/app/src/main` Git tree is identical to accepted390. The successful build receipt prints application APK SHA256 `9c71a32dbc2deac3d650c6849a335379bd2b005c1516437c613bcd0fcff7dd70`, also observed before, after and installed; size 22,702,878 bytes.

**Concrete gap:** the manifest reports instrumentation APK SHA256 `85e0d83ddc5017ef5cbc8fbe3503d128e2a530efa1755e3d12c8034f27db27a9`, but no captured source-tree/build-input attestation or installed test-package hash conclusively ties that binary to candidate sources. The checker snapshot, production-tree equality and successful build are corroboration, not that missing attestation. Current mutable build outputs cannot repair a historical binding. No source or receipt was manufactured. Source identity is therefore partially bound, and overall audit completeness remains incomplete.

## Independently decoded phase evidence

Every phase below has transport return code 0, no timeout, one `INSTRUMENTATION_CODE: -1`, matching run ID, a complete chunk manifest and exact SHA256/byte matches for every decoded file. Both preliminary teardown probes also pass these checks and preserve the boot ID.

| Phase | Assertions recorded | Transport seconds | Streamed files |
| --- | ---: | ---: | ---: |
| Default font | 108 | 42.018 | 44 |
| Large font | 108 | 40.857 | 44 |
| Cold UI restart | 3 | 2.929 | 3 |
| Personal documents | 83 | 3.147 | 3 |
| Cold documents | 7 retained collections (not 7 assertions) | 0.649 | 4 |
| Native/cards/recognition absence | 57 | 8.104 | 8 |

These are instrumentation assertions and elapsed transport times, not independent human usability observations or inference benchmarks. Default/large receipts exercise keyboard Back/edit restoration, blocked export cancellation and retry, source access and note persistence, destruction, and accessibility nodes. Blocked export cancellation took 91/42 ms. Cold UI retained bookmark/note state. Document receipt covers import, provenance/source offsets, Library return with no inference, malformed inputs, rollback and export cancellation; cold reopen retained seven fixture collections. Actual accessibility text and screenshots remain hash-bound; TalkBack and human review remain open.

Boot ID before, after, and both probes is `75d5e110-b22d-431e-af27-b0bb96f6c109`. Original font `1.0` equals device-reported restoration and host readback; activity scales were 1.0 and 2.0. This later continuous run does not erase the prior run's different boot IDs or transport failures.

Native receipt reports API37, page size 16384, CPU llama.cpp `bb4caa7540188872173c44d161602d9271386413`, context2048, threads2. Pinned Qwen2.5 0.5B fixture model SHA256 `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`, 491,400,032 bytes, load409.375 ms and reload387.562 ms; precancel/load/release/reset/reuse checks pass. No generation was performed. Loaded PSS75,619 KiB/native heap46,041,840 bytes are receipt samples, not peaks or phone proof. Six native-library receipts have congruent 16KB LOAD alignment, aligned RELRO ends and uncompressed 16KB ZIP offsets; zipalign succeeds and package reports pageSizeCompat=0.

All three bounded reviewed city cards have exact receipt hashes; no city index/nearby venue lookup is claimed. OCR and speech assets are absent, and explicit unavailable paths were exercised, not recognition success. Production model-selection and small/bulk catalogs are absent; the resident native fixture model is retained. Retention proves only the enumerated paths, not all user data.

## Storage and limits

App logical bytes increased from 565,688,487 to 577,373,425; allocated KiB from 557,776 to 569,992 as fixture receipts accumulated. `/data` used KiB increased from 1,836,064 to 1,848,216, available KiB decreased from 63,888,092 to 63,875,940. These are before/after subset measurements, not sampled maxima, full-corpus installation, or task303/API35 capacity evidence. APK, model, collection absence and optional asset absence are separately recorded.

## Check and remaining gates

`bash tools/evaluation/check_modern_receipt_audit.sh` verifies original frozen bytes, candidate source pins, every stream, receipts, identity, boot/font continuity, alignment data and packet copies. In-memory negative controls alter actual evidence for stale run, missing phase, corrupted chunk, corrupted manifest hash, boot mismatch, font mismatch and failed transport, without modifying originals. PASS means the **incomplete** classification is honestly supported, not product compatibility acceptance.

An initial audit-only check rejected the zipalign output because the tool spells its success text `Verification succesful`; the checker was corrected to require that exact actual line. This was not a device failure; no device work was repeated. Prior task400 failing reports remain untouched in their immutable checkpoints. Task302 remains blocked. Physical ARM64/GrapheneOS, full-capacity API37, sustained stability, TalkBack, source rights, generated quality, competitive comparisons and human release remain open. The precise missing evidence is immutable instrumentation-build provenance; no further suite execution is attempted in task410.
