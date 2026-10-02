# Modern integrated Android compatibility — task400 repair1

**The required Android build and fresh dedicated API37 integrated check pass.** The accepted390 application remains byte-identical; repairs are in test transport/registration, absent-catalog restoration and validation. All earlier failures, including missing installed code, remain preserved. Emulator evidence is not phone, generated-answer, full-capacity or release acceptance.

## Candidate and data-preserving recovery

APK SHA256: `9c71a32dbc2deac3d650c6849a335379bd2b005c1516437c613bcd0fcff7dd70`,22,702,878 bytes. Actual installed hash equals the built hash. DEX/native/bundled-asset identities remain in [candidate.json](modern-integrated/host-checks/candidate.json); fresh test-APK identity and all run artifacts are pinned in [manifest.json](modern-integrated/repair1/passing/manifest.json).

The repair started from the current task checkpoint, recovering failed50e2fd5 changes without switching/resetting/pushing.5564 was booted at API37/page16384 but its retained package record had `pkg=null` and pointed to a missing APK. The builder performed a normal `adb install --no-incremental -r`, with no uninstall, clear-data, emulator restart or service change. App ID10230 was preserved; the existing491,400,032-byte task305 model still matched SHA256 `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`, and prior task files remained accessible. Exact commands, exit codes and outputs are under [recovery/preflight](modern-integrated/repair1/recovery/preflight/). This restores package accessibility; it does not establish the cause of the earlier missing code or device losses.

A fresh preflight then caught an incorrectly quoted `stat` format argument. That failure is preserved; quoting is corrected. The checker verifies all three instrumentation registrations and runs UI/documents before the resident native test. All six expected report paths and both cold-restart results are required, with exact invocation ID, transport exit0 and raw `INSTRUMENTATION_CODE: -1`. No recovered report substitutes for failed transport.

## Actual required execution

```
bash tools/android-build.sh
bash tools/evaluation/check_modern_integrated.sh
```

Both completed with exit0. Fresh run: `downloads/modern-integrated/20261002T022111Z-c63af576`; no prior device report was reused. The serial suite took approximately114 seconds from timestamped creation to final manifest (filesystem timing, not a latency benchmark). Read-only verification of the final stricter receipt checks also passes:

```
bash tools/evaluation/check_modern_integrated.sh downloads/modern-integrated/20261002T022111Z-c63af576
```

Environment: existing emulator-5564, Android17/API37, x86_64, libc page16,384; fingerprint `google/sdk_gphone16k_x86_64/emu64xa16k:17/CP41.260828.004.A7/16296984:userdebug/dev-keys`. Actual package manager reports `pageSizeCompat=0`; final UI dump has no compatibility warning. Current ARM64 and x86_64 LOAD/RELRO and APK ZIP16KB checks pass; only x86_64 executed.5560/5562 and their corpora were untouched.

| Fresh phase | Observed behavior |
| --- | --- |
| Default UI |108 checks: actual keyboard/Back, Settings return, edit/recreation preservation, model-unloaded research, source reader, bookmarks/notes, share/picker, blocked provider cancellation/retry and Activity destruction |
| Large UI |108 checks at actual font_scale2.0, with screenshots/accessibility nodes; original1.0 preference restored |
| Cold reader |3 checks: saved bookmark, note and source identity survive force-stop/relaunch |
| Personal documents |83 checks: actual Library import→return→Citrine search, model explicitly unloaded/no invocation, provenance/UTF16 offsets, real quoted-CSV/JSON/text-PDF/TXT/MD handling, integrity/error/cancellation, portable export/reimport and exact live-catalog rollback |
| Cold documents |7 retained test collections reopen and search; initially absent live catalog restored to absence |
| Native/cards/recognition |57 checks: real pinned resident-model load/cancel/reset/close/reload with no generation; three reviewed six-field cards in actual reader and real provider exports; absent-engine/no-microphone/cancellation behavior |

Notebook blocked-write cancellation measured113ms(default) and68ms(large). Personal provider read cancellation measured73.537ms; blocked document export10.225ms. These are bounded public fixture observations, not arbitrary-provider guarantees. Source/Notebook access remained usable during blocked export; retry bytes match exactly.

Raw reports/text/accessibility nodes are committed in [repair1/passing](modern-integrated/repair1/passing/). Screenshots remain in the ignored fresh run directory and are SHA-pinned in the manifest; default/large keyboard and document-result screenshots were visually inspected. The large-font layout uses substantially more vertical scrolling; node/control checks do not establish human or TalkBack usability. The document screenshot visibly labels extractive fallback with no loaded model, not generated research. Source-dialog fields/offsets are asserted separately by the real instrumentation.

## Identity, memory and subset storage

Before/after hashes and explicit ABSENT states are identical: production `model.gguf`, model-selection, installed small/bulk catalogs and optional OCR/speech assets are absent; the resident task305 model remains intact at `page-size-test/model.gguf`. No model/corpus/optional asset was downloaded or transferred. Only documented small personal fixtures were provisioned into test-owned directories. Model load does not promote the fixture to production selection.

Native observations: precancelled load throws `IllegalStateException: Cancelled`; reset/load470.941ms, cancel/reset/close/reload392.357ms. Loaded PSS75,673KiB, native heap46,032,416 bytes; zero generation contexts and released final native session/context state. There is no generate call in the modern native instrumentation. Document-phase sampled PSS peak94,655KiB; sampled test-root disk peak242,738 bytes. These are emulator point/periodic observations, not combined generation/KV or whole-process absolute peaks.

| Snapshot | Before | After |
| --- | ---: | ---: |
| Logical app tree |528,997,254 |540,224,096 |
| Allocated app tree, KiB×1024 |531,521,536 |543,629,312 |
| Logical app tree plus APK |551,700,132 |562,926,974 |
| Allocated app tree plus APK blocks |554,217,472 |566,325,248 |

Byte totals include retained test reports/screenshots inside app data; they exclude test-APK/provider storage and shared system overhead. They are measured subset snapshots, not a whole-device peak or a replacement for303/390 full-inventory evidence. `/data` reports65,871,612KiB total, but nominal capacity is not installed-corpus proof. No full31-shard transfer/update or physical memory claim is made. Gradle2workers/2GiB heap is configured, not measured total build memory.

The reviewed GeoNames outputs preserve only IDs292223/292672/292968 and six approved fields, exact offsets, dates, credit, offline license and unknown-agency/as-is limitations. They are saved extractive metadata, not generated reasoning, current observations, routing or venue evidence. Underlying city-index lookup/raw-row matching was unavailable on this subset; prior360 source-review scope is not expanded. Optional OCR/speech assets were absent, so recognition success and microphone-grant capture are not claimed. Android reports location/audio permissions ungranted; missing speech starts no microphone and typing remains available.

## Failures, integrity and remaining gates

The [initial failed report](modern-integrated/initial-failed-report.md) and [original raw failures](modern-integrated/failures/) preserve missing completion, misregistered runner, device loss and missing package observations. The new [failed preflight](modern-integrated/repair1/failed-preflight/) remains separate from success. The cause of prior device/code loss remains unknown.

Three host regressions reject actual formatted-only completion, failed/timeout transport and stale run IDs. On the fresh run, actual report deletion/mutation, stale invocation and changed installed identity (even with recomputed receipt hash) were rejected. Current ELF/APK mutation tests reject misalignment, missing/compressed libraries and historical unaligned binaries. Original immutable evidence was not edited. [SHA256SUMS](modern-integrated/repair1/SHA256SUMS) pins new committed text receipts.

This closes the bounded emulator subset interaction checks only. Physical ARM64 Android/GrapheneOS, TalkBack/human review, full-capacity API37, present-asset recognition, long-duration stability, generated-answer quality/unseen generalization, bulk-source rights and external release acceptance remain open. No network research/inference, new model generation, protected inference changes, global preferences, publication or main advancement occurred. Independent criticism of frozen checkpoint `0b24b52e73cdaef3a85638d740f08afcba21ec0c` found no bounded blocker; its exact English result is in [repair1-independent-review.json](modern-integrated/repair1-independent-review.json). This is agent criticism; builder checks are not canonical or human acceptance.

## Repair2 in progress — later required run failed

The subsequent required invocation `20261002T022718Z-cb4e8303` failed during large-font collection (`files.txt` exit255), followed by offline font-restoration failure. Its raw transport/report stream and partial collection are preserved under `modern-integrated/repair2/failed-required-run/`; the earlier passing run above does not establish this invocation's success. On recovery5564 was booted with the app present and font2.0. The recorded original1.0 value was explicitly restored and read back before new tests.

The changed collection design restores font immediately after each UI instrumentation, before collecting screenshots. Each phase uses one bounded archive instead of one transport call per file; extraction rejects unsafe paths/types and limits total bytes to64MiB. The final verifier requires equal boot IDs before/after and exact font-restoration readback. Five host receipt/archive regressions pass. Fresh device validation is pending; no restart, data clearing, service change or old report substitution is used.
