# Task330: offline personal document library

Both required commands pass on LLMRig: `bash tools/android-build.sh` and `bash tools/evaluation/check_documents.sh`. The latest check ran on existing **emulator-5560, AOSP Android 15/API35 x86_64**, with 74 actual Android assertions and a separate force-stop/process-restart read. No services, model pin, answer policy, private holdout, UI lane, main branch or publication were changed. This is implementation and emulator evidence, not product acceptance or generated-answer quality.

## Delivered behavior

A real **Personal documents and collection export** entry opens a dedicated Activity. TXT/MD retain exact UTF-8-decoded source; CSV handles quoted commas, escaped quotes and multiline records; strict JSON retains scalar spans and JSON pointers; Android's local PdfRenderer API extracts actual text from PDFs. Empty/image-only and password-protected PDFs return explicit rejection messages. No OCR or new application dependency is included. PDF extraction requires API35+; earlier Android can still import supported text formats.

Imports use the existing durable content-addressed `PackLibrary`, combined index and active-collection controls. Exact source text, original bytes, date, importer-supplied ownership/location, extractor identity and UTF-16 citation ranges survive export/reimport. Every imported personal archive re-extracts its original and checks all span boundaries/locations, not just hashes. The existing source dialog displays these details without falsely claiming whitespace normalization. Namespace hashes remain edition-aware. Personal provenance does not grant redistribution rights or establish factual truth.

Portable `.plpack` export copies the verified retained archive exactly, including private original bytes and metadata, after explicit selection. Export state survives Activity recreation. Pollable input/output pipes support cancellation; transaction staging is removed on failure. All library instances now share one interruptible transaction lock, preventing another Activity's cleanup from deleting an in-flight archive. Existing shared storage/index admission remains enforced, including eight total collections and 16 MiB of small-pack archives; bulk export is explicitly rejected in this workflow.

[User and integration contract](../PERSONAL_DOCUMENTS.md) describes formats, limits, offsets, local-only picker requests, export privacy and platform limitations. The active UI refinement lane keeps Saved/history/bookmarks/reader/notebook export ownership. This task adds one route and a personal-source wording branch; it does not rebuild that lane. Generic collection selectors still show edition IDs/hashes; friendly filename labels remain a presentation refinement.

## Exact current evidence

| Artifact | Identity/result |
|---|---|
| Product APK |15,702,034 bytes; SHA256 `129179e21f4b760a49aeb6ed2b819b42e9d59178802e80e83a5834ad06869204` |
| Installed APK | Independently hashed on the emulator; same identity in [installed receipt](documents/installed-apk.txt) |
| Test APK |382,534 bytes; SHA256 `5d417843fff2b2a3f200cc0e4ffa8b6a47d94d87ee5f308702e577cd42653425` |
| Original fixture manifest | SHA256 `ee0a7f2c43ae4665b2c176992f75b172a662cfd4c966b11b4372861d010065ad`; eight constructed public format fixtures, not corpus |
| Latest Android results | SHA256 `c1a051580a1c70ca3e8874c8b78535bdda8764eea8fdb3ee4202bd3c90af70f5`; [74 assertions and raw samples](documents/required-checks/results.json) |
| Saved production model |491,400,032 bytes; SHA256 `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`, unchanged |
| Existing catalog | SHA256 `6c1d922c4a060d9f57138d6a65c3f238e1196301cf6e1e63b7580c60f8e93b64`, restored byte-exact after temporary UI fixture removal |

The [receipt](documents/required-checks/receipt.json), [build log](documents/build-final.log), [check output](documents/check-final.log), [source hashes](documents/source-identity.json), [dialog text](documents/required-checks/source-dialog.txt) and [actual screenshot](documents/required-checks/source-dialog.png) bind the result to this candidate. The initial complete validation remains separately in `documents/final/`; it used the same final product/test APKs. Each earlier raw run is retained with [hashes and locations](documents/run-artifact-manifest.json).

Tests cover all five positive formats, exact multiline CSV records, JSON pointers, real PDF page/text extraction, UTF-16 emoji spans, metadata/ownership, combined retrieval, disabled-source exclusion after catalog reopening, deletion, exact export/reimport identity, changed original/extracted bytes, truncated ZIP, malformed CSV/JSON/UTF-8, input/collection limits, pre-read/mid-copy/transaction/export cancellation, and staging cleanup. A forged PDF with recomputed text/passage hashes is rejected against its original. A concurrent import/load fixture verifies commit preservation and interruptible lock waiting. A real stalled provider read is cancelled using the Activity button; retry succeeds in the same Activity. A non-reading output pipe is cancelled through the export stream. Pending export and owner metadata survive real Activity recreation. Source inspection uses the actual MainActivity source button. The original model/catalog hashes match before/after. Missing and changed fixture artifacts fail before upload.

The test injects local provider results at the Activity's result handler; it does not automate the system file-picker's file selection. Enable/disable/delete and portable roundtrip exercise real library transactions; the pre-existing collection-control wiring is reused. No generated answer is scored or credited. Manifest inspection rejects INTERNET; DEX inspection finds no Google Play Services references. The framework test provider is only in the test APK.

## Measurements and budget scope

The final run's five personal documents produced **6,112 bytes** of retained archives and five distinct searchable originals. Combined extraction plus validation, atomic install and index rebuild took TXT 37.33 ms, MD 46.92 ms, CSV 53.94 ms, JSON 36.47 ms and text PDF 70.29 ms. These are single fixture observations, not throughput percentiles or large-document guarantees. Metadata records device-clock import time; emulator time is not an authoritative source date.

Blocked input cancellation took **74.85ms**, blocked output cancellation **9.04ms**. A separate process reopened the retained seven-document test catalog in **152.38ms**, with 7,725 archive bytes and 39,161 KiB PSS. These seven include constructed admission-test documents; they add no factual corpus coverage.

Sampling at roughly 50 ms during extraction and actual MainActivity/model/library opening observed peak PSS **642,882KiB**, Java live allocation **61,758,896 bytes**, and native allocation **232,967,072 bytes**. Native/model mmap, UI and instrumentation are included; this is not an isolated PDF-parser measurement or physical phone RAM. The task test directory's sampled high-water was 407,623 bytes, largely screenshot/evidence output rather than installed document payload. Sampling can miss short allocation/staging peaks.

[Storage snapshot](documents/device-storage.txt) reports 2,928,744 KiB in the existing app files area, 136 KiB cache and 8 KiB code cache; this includes historical fixture assets. It is not a new full-scale candidate inventory. [Exact retained archive/model sizes](documents/installed-sizes.txt) and [device capacity](documents/device-capacity.txt) are recorded independently. Input buffers, PDF temporary files, portable ZIP validation and installation staging are bounded by the documented per-operation limits, but maximum-admitted import/update peaks were not measured here. Task303's old frozen full inventory measurements do **not** validate this new APK. Recompute final joint installed/update/cache totals against 45 GB target/50 GB hard limit during candidate integration; no full-scale budget gate is closed by these small fixtures.

## Preserved failures and review

The first build failed on an incorrect library refresh call. The first device attempt lacked the test provider's files directory. The next exposed a real legacy dispatch defect: `BroadPack.isBroad` rejected a personal archive before its reader ran. A UI test then asserted before the enabled search control and crashed; its exact temporary public fixture archive was preserved before targeted recovery. No app reset occurred. Later harness failures concerned an absent framework result-code marker despite passing assertions, an undeclared secondary test runner, and a transient empty accessibility root. Logs remain; the final checker requires actual assertions, marker, preserved hashes and fresh restart results.

Independent review found malformed signed JSON escapes, lost export state after recreation and blocked output writes. A second review found cross-instance transaction cleanup and PDF text-correspondence gaps. These were fixed and received new regressions, rather than being waived by the earlier passing run. [Final supplementary criticism](documents/independent-review-final.txt):

> Reviewed fixes address prior defects; 74 emulator checks and restart pass, but physical-device acceptance, cross-version PDF portability, adversarial PDF resource bounds, and generated-answer usefulness remain unestablished.

This is supplementary source/test review, not the runner's canonical acceptance or human approval. Remaining limits include provider-open/FUSE/native-PDF call cancellation, malicious compressed-PDF resource isolation, PDF layout/complex-script fidelity, cross-version extraction portability, pre-API35 device exercise, physical Android/GrapheneOS, independent clean-machine reconstruction and final release identity/resource integration. No competitive percentage or superiority is claimed.

## Reproduction and attribution

See [fixture/check instructions](../../tools/evaluation/documents/README.md). All eight frozen fixture hashes reproduced exactly in a separate temporary directory with the pinned test tools; original bytes were retained. Fixtures and virtualenv live in ignored paths. Tool licenses are preserved under `documents/test-tool-licenses/` and summarized in `THIRD_PARTY_NOTICES`; none is a shipped PDF dependency.

The requested competitor output was available at the worker's actual `repo/output` path. Its handed artifacts' hashes were verified, and its static-only limitations and disclosed acquisition violation remain recorded. [Verification](documents/competitor-verification.json) and [bounded requirement excerpt](documents/competitor-scope.txt) document reuse without copying implementation or branding. Android's primary [PdfRenderer page text API](https://developer.android.com/reference/android/graphics/pdf/PdfRenderer.Page#getTextContents()) supplies local extraction, not OCR or layout-perfect transcription.
