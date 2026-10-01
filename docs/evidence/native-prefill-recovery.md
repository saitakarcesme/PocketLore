# Native prefill cancellation and process recovery

Both requested checks pass on LLMRig's existing API-35 x86_64 `emulator-5560`. A real 1,801-token prompt is cancelled before any token callback, closing during real model loading releases the native session, and a separately killed app process restarts with saved assets intact. Preflight resource admission now precedes real weight/context buffers. These are bounded emulator results, not physical-device, OS OOM or answer-quality acceptance.

## Frozen protocol and implementation

Commit `dc978bb` froze [the public lifecycle fixture](../../tools/evaluation/prefill-recovery/cases.json) before implementation; SHA-256 `0d28f42eadd5dc0aace4d251f6f089249db381319278d6ba4c196844c861368e`. The prompt repeats `water ` 1,800 times, requests at most eight output tokens and produces 1,801 input tokens with the pinned model. It is a synthetic workload, not factual corpus. Cancellation/close must return within 5,000 ms. Private holdout was not read.

The prior runtime already had CPU abort callbacks and retained a session lease while in-flight calls finished. Its resource-budget check ran only after context allocation. The repair adds a preflight model/context using the pinned llama.cpp `no_alloc` path, applies the existing model/KV/compute ceilings to its estimates, frees that simulation, then loads actual weights. Real context accounting is checked again after allocation. Model load also rechecks cancellation after upstream load returns and frees a just-loaded model if close/cancel won that race.

Read-only native diagnostics expose phase, actual upstream load/abort callback counts, prompt-token count, context-allocation attempts/failures and last estimated buffers. They do not pause execution or inject success/failure. The test waits for prefill phase plus a CPU callback before cancelling, and for actual weight-load progress before closing. Diagnostic arrays are snapshots, not synchronization guarantees.

The shared admission policy accepts exact ceilings and rejects each ceiling plus one byte and UINT64_MAX in executable host C++ tests. These four rejected estimates are **policy refusals**, not failed real allocations. Limits remain model 2,147,483,648 bytes, KV 805,306,368 bytes and compute 1,073,741,824 bytes. Metadata, vocabulary and graph bookkeeping still allocate during simulation; this screen does not bound all allocations or establish a <=12 GB phone footprint.

## Preserved failed attempt

The first preflight implementation retained the default mmap mode while setting `no_alloc`. It aborted in the pinned upstream tensor loader before lifecycle assertions. The source has `GGML_ASSERT(!ml.no_alloc)` on that mmap path, matching the preserved native stack; disabling mmap for the simulated model fixed the run. Actual weight loading retains its original mode. No upstream checkout or pinned revision was changed.

The failing implementation remains checkpoint `c02fb7d`. Its [crash log](native-prefill-recovery/no-alloc-mmap-failure/crash-logcat.txt), [instrumentation failure](native-prefill-recovery/no-alloc-mmap-failure/lifecycle-instrumentation.txt), [partial record](native-prefill-recovery/no-alloc-mmap-failure/lifecycle.json), [APK identities](native-prefill-recovery/no-alloc-mmap-failure/artifacts.json) and build output are preserved. This was an assertion abort, not a measured OOM or a successful recovery test.

## Final actual measurements

The final [lifecycle record](native-prefill-recovery/final/lifecycle.json), [process-kill marker](native-prefill-recovery/final/kill-ready.json), [restart record](native-prefill-recovery/final/restart.json) and [summary](native-prefill-recovery/final/summary.json) retain exact prompts, raw outputs, timings and runtime observations.

| Operation | Observed result |
| --- | --- |
| Long prefill cancellation | 18.618 ms from cancel request through native return/context release; result -1, zero token callbacks before and after cancellation |
| Prefill observation | 1,801 tokens, phase 4, two real CPU abort-callback observations, one active context; observed 17.332 ms after generation submission |
| Reuse after prefill cancel | Same session reset, eight actual generated tokens in 525.727 ms; context released afterward |
| Close during loading | Phase 2 with 292 progress callbacks observed before completion; load returned `Cancelled` in 27.105 ms, lease/context counts both zero |
| Reuse after load close | New session loads and generates eight tokens in 518.853 ms |
| Malformed four-byte GGUF | Rejected with `Cannot preflight GGUF model`; no live context remained |
| Process death/restart | PID 4571 killed; new PID 4638 starts with zero lease/context counts, Activity reload succeeds, staged files removed, unrelated fixture retained |
| Generation after restart | Eight actual tokens in 666.695 ms; final lease/context counts zero |
| Observed real context allocation failures | **0**; lifecycle had three real context attempts and restart had one direct generation-context attempt |

Cancel latency includes native unwinding and freeing the generation context. Close latency includes the in-flight load's return and session destruction, not merely the close JNI call. Generation times exclude model loading, setup, retrieval and UI. The JSON `load_ms`/`after_load` fields describe the most recent successful direct load within that phase (337.092 ms for lifecycle, 412.400 ms for restart), not an aggregate or cold-load benchmark. All measurements are single emulator samples, not p50/p95, thermal or phone latency.

Actual model/KV/compute buffers during prefill were **485,452,288 / 25,165,824 / 78,709,248 bytes**, respectively, equal to the preflight estimates in this run. The checker enforces positive actual buffers no larger than the estimates and ceilings. These are native buffer-accounting values, not process RSS, peak memory or phone RAM. Zero failed real context allocations does not prove allocation failure recovery; memory exhaustion was intentionally not induced.

All three recovery generations produced this unedited continuation of `Water is`:

>  a precious natural resource. Which of the

That incomplete fragment is retained as real output. The eight-token cap is a lifecycle probe; no correctness, citation support or usefulness is claimed.

## Actual process death and saved data

The kill phase starts genuine native prefill, records callback progress and zero emitted tokens, then waits for the host. The checker sends SIGKILL only to that measured app PID. [Android exit information](native-prefill-recovery/final/exit-info.txt) independently reports PID 4571 with reason `SIGNALED`, status 9; [PID observations](native-prefill-recovery/final/pid-after-kill.txt) show its absence before restart. This is actual process death, not a callback pretending the process died, and not an OS low-memory-killer test.

Two known app staging paths (`model.partial`, `pack-140000.partial`) were deliberately seeded immediately before killing; they simulate interrupted imports rather than proving a kill at every copy/promotion boundary. Their [post-kill presence](native-prefill-recovery/final/stages-after-kill.txt) is recorded. On restart the real Activity's existing cleanup removes those stages and reloads its saved model. `prefill-notes.partial` remains unchanged. Existing cleanup required no product change. A direct JNI session then generates successfully after the Activity releases its session.

[Before](native-prefill-recovery/final/saved-before.txt) and [after](native-prefill-recovery/final/saved-after.txt) hashes of the actual saved GGUF and pack are identical. The test uses app-owned fixtures and refuses to overwrite preexisting named model/pack stages. No model assets, binaries or bulk datasets enter Git; no new download or license change occurred.

## Exact identity and checks

| Artifact | SHA-256 |
| --- | --- |
| Product APK, 11,773,557 bytes | `d31b692e1098aa994332174b958ad1c88172694d692bda33c09914cb6ad646d1` |
| Test APK, 237,022 bytes | `00fe32dc7905f1041d726536ca8002b955a97546dea8bf867ef1883493e3aa53` |
| Qwen2.5-0.5B Q4_K_M, 491,400,032 bytes | `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db` |
| Saved English reference pack | `567e9bbbaab896826809ec20f81ae1c4b3f421b011931edae0989d28cfce10ea` |
| Final lifecycle record | `ae602148120ce999347f224fca09ac4d00c986f8c814e1b58634718217c2fce9` |
| Final kill record | `8989e304871ec64743569b3a14b4eb81f1ce3a9b535310977df40fb35c250ecc` |
| Final restart record | `b3b969de8032a738ec08f8090d706c5f656c1fa3dfb17e39b0cce5c351f25ceb` |

Runtime identity remains llama.cpp `bb4caa7540188872173c44d161602d9271386413`, CPU, context 2,048, FP16 KV, one sequence/session and two threads. APK and [source hashes](native-prefill-recovery/final/source-hashes.json) distinguish the wrapper repair. Both ARM64 and x86_64 libraries build; execution here is x86_64 only.

Both named commands exited 0:

- `bash tools/android-build.sh`: [standalone build](native-prefill-recovery/final/standalone-build.log).
- `bash tools/evaluation/check_prefill_recovery.sh`: [test build](native-prefill-recovery/final/build.log), [lifecycle instrumentation](native-prefill-recovery/final/lifecycle-instrumentation.txt), [killed instrumentation](native-prefill-recovery/final/kill-instrumentation.txt), [restart instrumentation](native-prefill-recovery/final/restart-instrumentation.txt). The killed run is expected to end without normal instrumentation success; success instead requires the verified signal, changed PID and actual restart behavior.

Reproduction requires the existing booted `emulator-5560`, installed saved assets with the pinned hashes, and compatible installed toolchain. Every run archives output under ignored `downloads/prefill-recovery/run-*`. The checker compiles and executes budget-boundary behavior, invokes real JNI, verifies actual phase/callback evidence, checks context/lease release and raw generation, kills only the app, restarts it and compares saved hashes. It does not accept a self-reported PASS without those observations.

The earlier [passing run](native-prefill-recovery/first-pass/summary.json) remains preserved (15.041 ms prefill cancel, 27.879 ms close). The final run added discriminating actual-versus-estimated buffer assertions and Android exit-reason verification; no fixture tuning or faster-sample selection occurred. Final product APK bytes match the standalone build.

## Remaining limits

Cancellation depends on upstream callback granularity; metadata parsing, simulation/bookkeeping, filesystem faults and some allocation operations can take time before callbacks. The one pinned small GGUF and one emulator do not establish safe handling of all architectures, malformed GGUFs or device memory pressure. The mmap assertion failure remains visible. No forced failed allocation, OS OOM survival, low-memory-killer behavior or sustained/thermal test is claimed. Saved-stage seeding is explicitly distinct from actual interrupted-import data.

Physical ARM64/GrapheneOS, larger-model resource behavior, independent quality and release acceptance remain open. The prior release freeze is historical; the changed APK requires later candidate freezing and exact-identity release validation. No private holdout/context, orchestration/state, emulator service restart, branch switch, push or main advancement occurred.
