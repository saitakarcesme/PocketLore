# Stalled document-provider cancellation

Measured on LLMRig's existing API-35 x86_64 `emulator-5560`, 2026-10-01. Both requested checks pass. Stalled model and pack reads now cancel before the provider releases data, remove staging and retain saved assets. Same-process transport retries and same-Activity full real-model/pack retries pass. This is bounded emulator evidence, not physical/GrapheneOS or arbitrary-provider acceptance.

## Frozen cases and reproduced failure

Commit `6edba00` froze the [transport cases](../../tools/evaluation/stalled-provider/cases.json) before any product changes; SHA-256 `1c0818856e39dea26aa41f3806087b5ffb837f6c8aa205c7bf950a81435707f5`. Each import has pre-cancellation, an empty stalled pipe, a pipe stalled after four bytes, truncated EOF, and a retry. A stalled case waits for actual provider/staging progress, observes the unfinished operation for 250 ms, then requires return within 1,500 ms **without releasing the writer**. Release happens afterward; a failed write confirms the reader was closed.

The test-only Android DocumentsProvider uses real OS pipes. Short fixtures stop after four bytes; successful transport retries write in seven-byte pieces. The eight-byte `GGUFtest` fixture tests model staging only and is explicitly not a valid model or factual corpus. Pack tests use the existing licensed, validated 186-passage reference pack.

[Pre-change raw baseline](stalled-provider-cancellation/baseline/results.json), committed as `d92b9d0`, reproduces five deadline failures: model pre-cancel, model empty/prefix stall and pack empty/prefix stall. Each remained blocked at 1,500 ms, with staging still present, until the writer was released. Pack pre-cancel returned in 1.758 ms but unnecessarily opened the provider. Both existing short-read rejections and transport retries already worked; these are retained controls, not newly claimed fixes. The baseline app APK was `2457ee6c474d1d6b8f6447ed2a698b2b491ea1f03208ab7b78ab5eec9796fd7d`.

Setup failures are also preserved: [incorrect init-script path](stalled-provider-cancellation/failures/initial-build-failure.log), [late manifest configuration](stalled-provider-cancellation/failures/manifest-failure/instrumentation.txt), [missing provider protection](stalled-provider-cancellation/failures/provider-permission-failure/failure-logcat.txt), [grant startup](stalled-provider-cancellation/failures/grant-startup-failure/results.json), and [grant lifetime](stalled-provider-cancellation/failures/grant-lifetime-failure/results.json). The provider-permission crash left an older result file, retained verbatim in that failure directory; its instrumentation/logcat, not that stale JSON, identifies the failure. The harness now removes previous results before a run. Grants must be issued from the test APK after instrumentation starts, because pre-start grants did not survive.

## Product change

`DocumentInput` owns the AssetFileDescriptor and checks cancellation before opening and around every read. FIFO descriptors use nonblocking reads and 50 ms polling; the import worker exits its wait and closes the descriptor through try-with-resources. This avoids depending on Java interruption to interrupt a blocking pipe read. ModelImport also checks cancellation before each read. Both NativePanel model import and MainActivity pack import use this reader; existing atomic promotion, size/integrity checks, cleanup and saved-asset preservation remain in place.

Regular file descriptors retain declared offsets/lengths. Unsupported descriptor types are rejected rather than silently treated as ordinary files. No detached reader thread is abandoned on cancellation. The [Android Os API](https://developer.android.com/reference/android/system/Os) exposes the polling/read operations used here. Provider-open cancellation requires provider cooperation under the [DocumentsProvider contract](https://developer.android.com/reference/android/provider/DocumentsProvider); this repair does not claim to bound a provider that never returns from open or metadata query.

The fixture provider, grant Activity and fixture URI grants exist only in the test APK. The [measured product manifest](stalled-provider-cancellation/product-manifest.txt) contains neither that provider nor requested permissions. No unrelated provider, service or permission configuration was changed.

## Final measured behavior

The final [raw results](stalled-provider-cancellation/real-retry/results.json) and [summary](stalled-provider-cancellation/real-retry/summary.json) preserve all ten transport cases and four Activity assertions, under app PID 3954.

| Cancellation case | Model (ms) | Pack (ms) |
| --- | ---: | ---: |
| Already cancelled before open | 0.613 | 0.063 |
| Empty stalled pipe | 48.530 | 46.187 |
| Four-byte prefix then stall | 48.068 | 47.267 |
| Actual Activity cancel button, prefix stall | 5.935 | 50.997 |

Transport latency runs from setting the cancellation flag through worker return; pack tests also issue the interruption used by the actual controller. Pre-cancel latency includes worker dispatch. Activity latency includes the main-thread button click and observation of idle state. These single samples include cleanup/close and are not p95, universal upper bounds, or phone measurements. Each cancelled import removed its staging file before writer release. Pre-cancel cases made zero provider opens. All stalled writers observed reader closure after release.

Four-byte model input fails with `Incomplete model copy`; truncated pack input fails with `Missing pack entries`. Saved bytes remain unchanged. Transport retries succeed on the same executor thread, ID 41, in the same process. The Activity checks call the real import entry points and click the actual cancel buttons; model selection/confirmation is injected through the private import method, and pack selection through onActivityResult, so this is not a new system-picker UI test.

A supplemental [real retry fixture](../../tools/evaluation/stalled-provider/activity-retry.json), SHA-256 `d22480f1d7bc1db7679667f1336ba26b9bf3de5b577d80172579ad2314f1005c`, was frozen in `6f2cd21` before adding its execution. No product code changed after that freeze. It reuses the existing saved model, streamed into isolated test-provider storage with its hash checked before use; there is no new download or model tuning.

After button cancellation, the **same Activity** imports the complete 491,400,032-byte pinned Qwen2.5-0.5B Q4_K_M through a read-only regular provider descriptor. Actual staging, SHA-256, JNI validation/load and atomic promotion complete in **1,625.601 ms**; the UI reports the exact expected hash and runtime. The same Activity then successfully imports the 186-passage pack. The runtime is llama.cpp `bb4caa7540188872173c44d161602d9271386413`, CPU, 2,048-token context, one session and two threads. There is no generation workload or answer-quality claim in this task.

[Before](stalled-provider-cancellation/real-retry/saved-before.txt) and [after](stalled-provider-cancellation/real-retry/saved-after.txt) independently hash the actual app-owned saved model and pack; both are identical. The test model replica stays in test-app storage, outside Git. Successful model staging-only fixtures are removed, and failed/cancelled production stages are absent.

## Identity and reproduction

| Artifact | SHA-256 |
| --- | --- |
| Product APK, 11,769,461 bytes | `cb5c11602f88a63e31e87a44b11a06310f01a1090f7f4c3ea925b879db66e751` |
| Final test APK, 252,538 bytes | `1974c14aa5b7a164a4198cebe983988b5e5f8708fb2a301b42684385566e778b` |
| Saved/replicated model | `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db` |
| Pack | `567e9bbbaab896826809ec20f81ae1c4b3f421b011931edae0989d28cfce10ea` |
| Final raw results | `e9506a40f81b4fcc6f56d1433e1c041dd54dec83e052a3611b69fa2e9c24fe04` |
| DocumentInput source | `b2f472f8bbba519ae5fdf9a631613bff7d3849a4dcb65c26ac90d39bd879f93f` |

Run `bash tools/android-build.sh`, then `bash tools/evaluation/check_stalled_provider.sh` on the rig with the existing booted emulator and saved pinned model/pack. The checker requires those actual assets, builds/installs the two APKs, provisions only test storage, executes provider behavior and compares saved hashes. Each invocation creates a separate ignored `downloads/stalled-provider/run-*` directory. The legacy mode documents the original defect when run against the pre-change checkpoint; it is not a current baseline claim.

The [standalone build](stalled-provider-cancellation/standalone-build.log) exited 0, and the final [behavioral check/build](stalled-provider-cancellation/real-retry/build.log) and [instrumentation](stalled-provider-cancellation/real-retry/instrumentation.txt) passed. Product APK identity matches the measured bytes. Earlier passing [transport-only](stalled-provider-cancellation/transport/results.json) and [Activity cancellation](stalled-provider-cancellation/final/results.json) runs remain separate; the last run added the discriminating complete real-model retry rather than selecting a better latency sample.

## Limits and release status

Cancellation during provider acquisition/open or model metadata query is not bounded by this implementation. A regular file backed by stalled storage/FUSE can block inside a kernel read despite poll readiness; nonblocking FIFO behavior does not prove recovery for such descriptors. Shared descriptor flags are changed only for the opened FIFO read endpoint. Providers with unsupported descriptor types fail explicitly. A hostile provider, OS kill, fsync latency, native load cancellation and physical allocation/thermal behavior are not established by these tests; separate native-recovery and physical gates remain open.

The regular-file real-model retry is validated; arbitrary asset subsection providers and broader provider diversity remain unmeasured. Existing clean-install or answer-quality checks were not rerun or claimed here. No physical Android or GrapheneOS device was available. The prior release manifest is historical; later product work needs a fresh candidate freeze and exact-identity release validation. Attribution and licenses are unchanged. No private holdout, orchestration/state, service restart, branch switch, push or main advancement occurred.
