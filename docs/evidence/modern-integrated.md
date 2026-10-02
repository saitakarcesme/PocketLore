# Modern integrated Android compatibility — repair2

**The required build and a fresh six-phase API37/16KB check pass.** This result is run `20261002T023305Z-ce6da5b0`, not the earlier repair1 success. The subsequent failed canonical invocation and its unrestored font state are preserved. Source/runtime/model/answer behavior and APK remain unchanged; this repair changes evidence collection and restoration validation only.

## Failure and material collection change

The failed required run `20261002T022718Z-cb4e8303` completed large-font instrumentation with raw completion-1, but the next collection command returned255 and font restoration reported `adb: device offline`. Its available raw receipts—including full instrumentation output—are now committed under [failed-required-run](modern-integrated/repair2/failed-required-run/). Partial success never establishes that invocation's success. The [prior report](modern-integrated/repair2/prior-repair1-report.md) remains historical.

On repair entry5564 was booted, the package was accessible, and font scale was2.0. The failed run's recorded prior1.0 value was explicitly restored and read back before testing; no emulator restart, reinstall, wipe or service change was performed in this repair. No cause is inferred for the earlier disconnections.

The checker now restores and reads back the original font **immediately after each UI instrumentation, before collecting its screenshots**. It collects each phase in one tar stream instead of separate per-file transfers. Extraction admits only flat JSON/text/Markdown/PNG files and at most64MiB; unsafe names/types and truncated archives are rejected. Failed transport/restoration/collection still fails the entire invocation. Final verification requires identical before/after kernel boot IDs, original font readback, six complete invocation-bound reports, successful transports, and exact installed identity/asset retention. No device restart or stale report may bridge a successful run.

## Actual fresh validation

```
bash tools/android-build.sh
bash tools/evaluation/check_modern_integrated.sh
```

Both returned0. Raw current output: `downloads/modern-integrated/20261002T023305Z-ce6da5b0`; committed text receipts: [repair2/passing](modern-integrated/repair2/passing/). Read-only verification also returned0:

```
bash tools/evaluation/check_modern_integrated.sh downloads/modern-integrated/20261002T023305Z-ce6da5b0
```

APK SHA256 `9c71a32dbc2deac3d650c6849a335379bd2b005c1516437c613bcd0fcff7dd70`,22,702,878 bytes, matches accepted390 and the actual installed APK. The exact test APK, all receipts, screenshots and tar streams are SHA-pinned in the fresh [manifest](modern-integrated/repair2/passing/manifest.json); binaries/screenshots remain in the ignored raw run, not Git. Current native ELF LOAD/RELRO and ZIP16KB checks pass for both ABIs. Actual execution is x86_64 emulator-5564, Android17/API37, libc pages16,384; package manager `pageSizeCompat=0` and final UI has no compatibility warning. No API35 result is relabeled as API37.

Before/after boot ID is `72f76fcd-579c-43d2-85b6-5223ede63110`. Default-phase, large-phase and final font readbacks are all1.0. All fresh phases pass with their own same-run transport/receipt binding:

| Phase | Observed behavior |
| --- | --- |
| Default and200% font UI |108 checks each: keyboard/Back/edit/recreation, source/Notebook/notes/bookmarks, blocked export/retry/destruction, source inspection and accessibility node/control screenshots |
| Cold reader |3 checks: bookmark/note/source persistence after force-stop/relaunch |
| Personal documents |83 checks: Library import→return→search with model explicitly unloaded/no inference, exact provenance/offsets, CSV/JSON/TXT/MD/text-PDF, corruption and cancellation, portable export/reimport and live-catalog rollback |
| Cold documents |Seven test collections reopen/search; original absent live catalog remains absent |
| Native/cards/optional input |57 checks: real resident model load/cancel/reset/close/reload without generation, three exact reviewed six-field source cards/provider exports, explicit absent OCR/speech and cancellation |

Default/large blocked notebook export cancellation:75/34ms. Document blocked export:8.599ms; stalled provider read cancellation:100.924ms. The six collection archives are4,781,568;4,756,992;336,384;245,760;246,784;1,147,904 bytes. These are bounded public fixture measurements, not arbitrary provider guarantees or human usability acceptance. Actual default/large screenshots and accessibility nodes are retained; TalkBack was not exercised.

Five host regressions pass, including actual historical transport/stale-report failures plus bounded archive success/path/type/truncation controls. Fresh device-run artifact mutations reject missing/changed reports, stale IDs and a changed installed identity even after recomputing the receipt hash. The original failed device report is not used by any successful phase. [SHA256SUMS](modern-integrated/repair2/SHA256SUMS) pins new committed evidence.

## Current subset resources and limitations

Before/after asset hashes and ABSENT states are identical. The only resident model fixture remains491,400,032 bytes at `page-size-test/model.gguf`, SHA256 `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`. Production model-selection, installed small/bulk catalogs and optional OCR/speech assets remain absent. The model was neither downloaded nor promoted. Personal public fixtures alone were staged in test-owned directories; previously retained data was preserved.5560/5562, protected inference and services were untouched.

Native load410.827ms and reload372.111ms; loaded PSS75,546KiB and native heap46,063,248 bytes. Precancelled load throws; reset/load succeeds, generation contexts remain zero, and close releases native state. These are load-time emulator observations, not generation/KV/phone memory peaks. No model generation or research inference occurred. Optional recognition success and microphone-grant capture are not claimed: assets are absent and permissions remain ungranted.

App-tree logical bytes before/after:548,694,868 /560,019,030. Allocated app tree:552,648,704 /564,772,864 bytes. Adding the APK yields final logical582,721,908 bytes and allocated587,468,800 bytes. These snapshots include accumulated task reports/screenshots but exclude test-APK/provider and shared Android overhead; no continuous whole-device peak, full31-shard capacity or update budget is inferred. Earlier303/390 full-corpus measurements are not transplanted. Gradle2workers/2GiB heap is configured, not measured total build peak.

Reviewed cards preserve only IDs292223/292672/292968 and six approved fields, UTF16 spans, dates, credit, offline license and unknown-agency/as-is limitations. They remain visibly saved extractive metadata, not generated reasoning/current venue facts. City-index/raw-row matching is unavailable on this subset. Document retrieval is visibly extractive fallback, not generated-answer success.

The fresh bounded compatibility gate passes; unexplained earlier device loss and long-run stability remain unresolved. Physical ARM64 Android/GrapheneOS, full-capacity API37, present-asset recognition, TalkBack/human acceptance, unseen answer quality, bulk-source rights and external release acceptance remain open. No private holdout, new inference/downloads, model/admission changes, publication, main advancement or global configuration changes occurred. Independent criticism of checkpoint `d31c0a40d30e7cd2ab91b153dce8ae2be0012f09` found no bounded blocker; its exact result is in [repair2-independent-review.json](modern-integrated/repair2-independent-review.json). Builder verification and agent criticism are not canonical or human acceptance.
