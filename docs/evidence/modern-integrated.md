# Modern integrated Android compatibility — task400

**Required build passes; the dedicated API37 integrated check fails.** Native load/recovery and narrow source-card/absent-recognition behavior have real partial evidence, but default/large-font editorial navigation and personal-document interactions remain unverified on5564. No failed invocation is promoted by a recovered PASS report. The candidate application is byte-identical to accepted390; only test/evaluation code changed.

## Exact candidate and environment

- APK: `9c71a32dbc2deac3d650c6849a335379bd2b005c1516437c613bcd0fcff7dd70`,22,702,878 bytes. DEX/native/bundled-source hashes and test APK identity: [candidate.json](modern-integrated/host-checks/candidate.json).
- Existing emulator-5564: Android17/API37, x86_64, process/libc page size16,384; fingerprint `google/sdk_gphone16k_x86_64/emu64xa16k:17/CP41.260828.004.A7/16296984:userdebug/dev-keys`.
- Actual initial `/data`:65,871,612KiB total. The subset has the resident task305 model at `files/page-size-test/model.gguf`,491,400,032 bytes, SHA256 `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`. Production model-selection, installed pack/bulk catalogs, OCR and speech assets were absent. No corpus/model/optional-asset transfer was performed.
- The permitted `runtime/modern-android/state.json` was read; its old unaligned delivery APK and task305-pending description are historical, not current candidate evidence.305 and390 receipts were inspected, not relabeled as400 execution.

## Implemented bounded checker

`bash tools/evaluation/check_modern_integrated.sh` binds only5564 and shares the existing task305 serial lock. It verifies actual boot/API/page size, exact accepted APK, ELF LOAD/RELRO/ZIP16KB, package compatibility state and installed hash; captures baseline/final assets/storage; builds three explicitly registered instrumentation runners; uses raw instrumentation completion, zero transport exit and fresh report IDs. It never changes canonical serial defaults.

Accepted ProductUiInstrumentation and DocumentsInstrumentation are reused with dynamic API labels and invocation IDs. Documents can now restore an initially absent catalog after removing only test-created imports. The default/large-font UI, blocked SAF cancellation/retry, cold restart and personal Library-return/search assertions remain intact. New ModernIntegratedInstrumentation performs no generation call: it tests precancelled load, reset/load, cancel/reset/close/reload, exact reviewed six-field projection/source-reader/provider export, and missing optional engines. It does not claim nearby-index lookup on this subset. Final APK/asset/corruption controls fail closed; complete-run changed/missing/rehashed-identity mutations remain pending because the run never reached them.

Three independent host tests consume the actual initial failed bytes: a PASS JSON without transport completion is rejected; nonzero/timeout/crashed transport cannot be replaced by a raw success marker; a report cannot be rebound to another invocation. Actual built ELF/APK mutation tests reject changed LOAD/RELRO, missing native libraries, ZIP misalignment/compression and the historical unaligned APK. These host passes do not satisfy device integration.

## Preserved runs and actual failures

All raw text reports, transport exit/timing metadata and build logs are under [failures](modern-integrated/failures/). Each directory contains a hash inventory including screenshots retained in the corresponding ignored `downloads/modern-integrated/<run>/` directory. No APK/model/binary payload is committed.

| Run | Observed result |
| --- | --- |
| `20261002T020922Z-0fb6e277` | Native/card/absent-recognition report PASS; formatted `am instrument` output omitted the completion code. Whole invocation failed; corrected to raw `-r` output. |
| `20261002T021019Z-6f678acc` | Raw native instrumentation returned0 and completion-1;5564 went offline during report collection. Whole run failed, and attempted font restoration also reported offline. No font mutation had yet occurred. |
| `20261002T021246Z-6a5578b4` | Native/card/provider-export report and transport pass. UI invocation failed because Gradle replaced the first manifest instrumentation entry. Explicitly listing the default runner first fixes this; a registration preflight was added. |
| `20261002T021331Z-462767aa` | All three runners registered; native report again returned completion-1, but5564 disappeared during screenshot collection. Whole run failed. |
| `20261002T021503Z-6d28c1c4` | After5564 reappeared, preflight failed: `run-as: unknown package: org.pocketlore.app`. Package manager shows `pkg=null`; `pm path` returns no installed path. UI-first order was prepared to isolate independent checks, but could not start. |

No emulator was restarted, wiped or uninstalled by the builder; no service/GPU/global configuration changed. No cause is inferred for transport loss or package-manager state. The user was asked whether another coordinator action owns5564; device mutations stopped rather than reinstalling over unexplained state. Final raw inventory/package/path observations are in [host-checks](modern-integrated/host-checks/). Resolving serial ownership and providing a stable installed5564 environment is the concrete external dependency; no change to5560/5562 or protected inference is requested.

## Partial measured behavior, not whole-gate success

The third run's actual report records a precancelled native load throwing `IllegalStateException: Cancelled`, followed by load376.094ms and close/reload372.340ms; loaded PSS76,589KiB and native heap46,063,008 bytes. Load has zero generation contexts, and final close releases session/context state. These are load-time emulator samples, not generation/KV/phone working-set peaks. No model generation or research inference ran.

That run opened all three approved GeoNames card projections in the actual source reader, kept exact six-field UTF16 spans, attribution/license/unknown-agency limitations, and exported the exact portable bytes through a real provider. Screenshots visibly label saved extractive metadata, not reasoning/current observations. Original raw-row/city-index matching was not exercised because the installed city index is absent. Absent OCR explicitly fails; absent speech leaves typing available without starting the microphone; cancellation clears input. Present-asset recognition was unavailable and is not claimed.

Before the fourth attempt, actual app-tree logical bytes were528,939,778 and allocated bytes531,435,520 (518,980KiB). Adding the22,702,878-byte candidate APK gives551,642,656 logical bytes for this snapshot, excluding test APK/provider/package allocation and shared Android overhead. No complete post-run total, continuous peak or full inventory budget is established: final package identity is unresolved. Earlier303/390 full-corpus capacities and API35 observations are not transplanted to5564.

## Checks and release gaps

- `bash tools/android-build.sh`: PASS, recorded initial required build; final dedicated test compilation also PASS.
- `bash tools/evaluation/check_modern_integrated.sh`: FAIL as above; not waived.
- Receipt regressions:3 PASS. Real current native artifact mutation checks: PASS.
- Default/large-font keyboard/Back/edit restoration, Notebook blocked-export interaction, cold restart and actual personal import/search/export on API37 remain pending. Existing API35 successes are not substitutes.
- Current installed APK identity, post-run asset retention/storage, compatibility-dialog absence and final lifecycle receipts remain unresolved after package-manager failure.
- Optional recognition with installed assets, full-capacity API37, native ARM64/physical Android/GrapheneOS, TalkBack/human acceptance, unseen answer quality, source-rights clearance and competitive/release acceptance remain open.

Two Gradle workers/2GiB heap are configured, not measured total compilation peak. No new models, downloads, inference, corpus expansion, private holdout, main advancement or publication occurred. Independent criticism of the frozen partial checkpoint is recorded separately; this report does not claim completion or acceptance.
