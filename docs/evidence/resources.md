# Resource audit — task 070

Status: both named checks passed on LLMRig on 2026-10-01. `bash tools/android-build.sh` builds ARM64 and x86_64; `bash tools/evaluation/check_resources.sh` runs 25 behavior assertions and real x86_64 JNI measurements on the existing `emulator-5560`. Physical Android/GrapheneOS, <=12 GB real-device acceptance and sustained performance remain open. No private holdout, orchestration, service, branch switch, global preference or push was involved.

## Changes and controls

[Policy and reproduction](../RESOURCES.md) describe the implementation. It enforces one live native lease even during close/cancellation, one fresh 2,048-token context with FP16 K/V, 256 output tokens, and explicit post-allocation model/KV/compute admission limits. Model and pack imports require a 256 MiB free-space reserve and retain old installed files until successful atomic promotion. Pack staging is now streamed and serialized. Recognized abandoned stages are cleaned without touching unrelated files. Low-memory callbacks cancel and unload the model; explicit reload works and preserves the saved model. Pack-import cancellation is available in the UI.

[Development cases](resources/development-cases.md) were frozen in `ff8d651`. [Final raw report](resources/final/results.json), [check summary](resources/final/summary.json), [standalone build](resources/build-release-counter.log) and [instrumentation build](resources/final/build.log) preserve measurements. The measured run is `downloads/resources/run-20261001T013649Z`. Earlier passing audits are preserved under `resources/first/` and `resources/buffer-audit/`; later iterations added native buffer, RSS/swap and installed-disk accounting. A later test-APK reproduction check failed and is preserved in `resources/apk-reproduction-failure.json`. The app APK matched; the test APK changed after switching runners. The audit now archives exact binaries at measurement time. No failed measurement was discarded or silently rerun to select a better score.

The 25 assertions cover pinned real model identity; storage refusal; mid-copy model/pack cancellation; old-file preservation; injected Java OOM cleanup; invalid pack rejection; narrow orphan cleanup; full real model staging/hash/removal; concurrent resident rejection; token overflow; actual generation; context release; close during generation with lease retention; slot recovery; Activity trim/low-memory callbacks, idle transition and explicit reload; unchanged saved model bytes. These include injected failures, not an actual exhausted-memory or full-disk experiment. Native cancellation is requested in the first token callback, not during long prompt prefill. Activity callbacks were tested with an idle loaded model; that does not establish all combinations of Activity pressure during native load, prefill or provider blocking.

The existing pack regression also passed: 18 corrupted packs plus real SAF import/restart/rejection/source inspection, with [summary](resources/pack-regression/summary.json), [instrumentation](resources/pack-regression/instrumentation.txt) and [UI log](resources/pack-regression/ui.log). This protects the changed pack installation path. Its duplicate-ZIP warning is an intentional corruption fixture, preserved in the log.

## Runtime identity and actual workload

Runtime: llama.cpp b10566, immutable revision `bb4caa7540188872173c44d161602d9271386413`; CPU only, two threads, one sequence, context 2,048, batch 2,048, microbatch 128, FP16 K/V. The Qwen3 claims sampler remains documented in the runtime identity; this resource workload calls ordinary `generateChat`, which uses greedy decoding, not the constrained claim sampler.

Test model: Qwen3-1.7B-Q8_0, **1,834,426,016 bytes**, SHA-256 `061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a`. Its pin and Apache attribution are unchanged. The real 32-token output and full prompt semantics are in the test source/report: the output is truncated and includes an unsupported heat-energy assertion. It is **not** a supported answer or answer-quality success; generation success here means actual JNI tokens were produced.

| Operation | Actual emulator measurement |
| --- | --- |
| Full 1.83 GB staged copy and hash | 4,997.452 ms |
| Stage logical bytes | 1,834,426,016 |
| Free-space decrease while stage existed | 1,834,434,560 bytes; includes filesystem activity/rounding |
| Model load | 890.469 ms |
| 32-token raw generation | 4,934.753 ms |
| First-token close request to native return | 88.410 ms |
| Pack verification plus index construction | 110.897 ms |

The Activity recovery check separately loaded the previously saved **491,400,032-byte** Qwen2.5 model, SHA-256 `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`. It received trim-critical and low-memory callbacks, released the native lease, and explicitly reloaded successfully. Its disk hash remained unchanged. The larger model is an isolated test asset, not a silently changed default.

## Memory: host, emulator and buffers are different measurements

The [host snapshot](resources/final/host-meminfo.txt) reports **32,638,484 KiB MemTotal** and **13,701,740 KiB MemAvailable**. These are LLMRig host values, never phone measurements. The [emulator snapshot](resources/final/emulator-meminfo-before.txt) and ActivityManager report **2,593,685,504 bytes total RAM**, with **2,043,285,504 bytes available** immediately before the workload; Java maximum heap was **201,326,592 bytes**. These readings occur at different instants and have different definitions.

There are 117 process samples, with a target 100 ms delay plus measurement overhead. Actual intervals are in the raw report. Memory phases and native allocation counts are recorded per sample. Peaks are sampled unless explicitly identified as `/proc` high-water values. Debug memory, `/proc` and native counters are collected sequentially, not atomically; maxima from different series cannot be added to obtain a peak.

| Metric | Observed value | Meaning |
| --- | --- | --- |
| Sampled process PSS maximum | 2,091,318 KiB | Android Debug proportional accounting, not a physical-device bound |
| Sampled process RSS maximum | 2,007,812 KiB | `/proc/self/status` resident pages; includes shared pages |
| Process RSS high-water field | 2,062,372 KiB | Kernel VmHWM, distinct from sampled PSS |
| Sampled VmSwap maximum | 172,908 KiB | Swapped process memory; this run did experience pressure |
| PSS immediately after Qwen3 unload | 68,096 KiB | Native lease/context counters both zero |
| Final PSS after Activity reload/unload | 129,398 KiB | Activity/Java/runtime overhead remains |
| Sampled Java heap used during index phase | up to 16,978,288 bytes | Whole Java heap, not isolated retained-index size |
| Active model buffers | 1,828,474,880 bytes | Pinned llama.cpp buffer accounting, not all native/process allocation |
| Active context/KV buffers | 234,881,024 bytes (224 MiB) | Fixed 2,048-token Qwen3 context |
| Active compute buffers | 79,888,896 bytes | Backend work buffers |

Native buffer counts return to zero after a request context is released, while the model may remain loaded. A model-loaded session without a context reports zero context-associated buffer diagnostics; it does not imply the model uses zero memory. No KV state is retained across requests. Native buffer bounds are checked **after allocation**, before decode, and therefore do not guarantee protection from allocation-time OOM, malformed models or an OS process kill. Java OOM recovery was injected at the import stream, not forced through actual device exhaustion. Android may omit callbacks or kill the process directly.

The index has **186 passages, 1,770 terms, 6,001 postings and 59,862 passage-text characters**. It is rebuilt in memory and has **0 persistent serialized-index bytes**. Logical posting payload alone is 6,001 × (4-byte passage ID + 8-byte score) = 72,012 bytes; this excludes object headers, collections, strings, vocabulary, metadata and allocator overhead, so it is not an index RAM estimate. Exact retained index memory and maximum-size pack behavior remain unmeasured; the observed whole-heap sample is provided instead of inventing an object-size total.

## Disk accounting

[Installed APK tree](resources/final/installed-apk-tree.txt), [owned data tree](resources/final/owned-data-tree.txt), [before](resources/final/disk-before.txt)/[after](resources/final/disk-after.txt) and [filesystem free space](resources/final/free-disk-before.txt) distinguish logical lengths from allocated `du -k` blocks. Test artifacts are not representative of a clean production install.

| Component | Logical/allocated measurement |
| --- | --- |
| APK, including both native ABIs and bundled packs | 17,794,384 bytes logical |
| Installed app code tree | 17,404 KiB allocated; no separate native-library file or oat artifact observed in this tree |
| ARM64 native library inside APK | 5,594,632 bytes; do not add again to APK total |
| x86_64 native library inside APK | 6,074,216 bytes; do not add again to APK total |
| Saved app model | 491,400,032 bytes logical; 479,892 KiB allocated |
| Larger test model | 1,834,426,016 bytes logical; 1,791,440 KiB allocated |
| Installed research pack | 159,327 bytes logical; 160 KiB allocated |
| Bundled starter/travel TSV | 5,380 / 909 bytes uncompressed inside APK; no extra installed file |
| Persistent index / inference cache | 0 / 0 bytes by implementation; no cache files written |
| Android cache / code_cache directories | 8 / 8 KiB allocated in this snapshot |
| App-owned data including historical test assets/reports | 2,365,068 KiB allocated |
| Maximum real model stage in this audit | 1,834,426,016 bytes logical, then removed |
| Production pack-stage cap | 16 MiB, plus the prior installed pack until atomic replacement |

The app-owned total includes the prior 93,511,232-byte native-smoke model, the saved 0.5B model, isolated Qwen3 model, pack corruption fixtures, raw reports and tiny sentinels. It excludes the installed APK tree and user document-provider copies. Those external originals remain after import and must be included in a user's total installation accounting; no unrelated user storage was inspected. The filesystem showed 2,789,452 KiB available before and 2,789,892 KiB after the audit; unrelated emulator filesystem activity means the difference is not a precise allocation ledger. Native memory is not disk cache; code/compiler artifacts may differ after Android optimization and across devices.

## Proposed device budgets — not acceptance

Use decimal GB for the bounty limits; MiB/GiB below are binary. A conservative planning allocation under a **12,000,000,000-byte device ceiling** is:

| Allocation | Bytes | Enforcement/status |
| --- | --- | --- |
| Model buffers | 2,147,483,648 | Post-allocation native cap; file capped separately |
| Context/KV buffers | 805,306,368 | Post-allocation cap, with token/sequence bounds |
| Compute buffers | 1,073,741,824 | Post-allocation cap |
| Other native/runtime/import overhead | 1,000,000,000 | Planning allowance, not a measured worst case |
| Java/UI/index/pack transitions | 800,000,000 | Planning allowance; actual Java heap limit varies by device |
| OS, graphics and other apps | 4,000,000,000 | Device/environment assumption, not controlled by PocketLore |
| Additional headroom | 2,000,000,000 | Planning reserve |
| Total | **11,826,531,840** | Below 12 decimal GB arithmetically; physical verification still required |

This is not a guarantee that every <=12 GB phone, every allowed GGUF or every maximum-size pack works. The emulator's smaller heap, swapping, OS behavior and arbitrary allocation overhead prevent that conclusion. Known-model profiling, pressure tests, background apps, thermal/sustained runs and real GrapheneOS hardware are still required. Lower-RAM devices may need smaller models or refusal before load; no adaptive model selection is implemented.

A conservative **11 decimal GB disk plan**, below the 50 GB ceiling, allocates 9 GB for four possible 2 GiB model copies (old/new provider originals, installed old model and new stage = 8,589,934,592 bytes) plus pack/APK copies; 1 GB for compiler/cache growth and 1 GB headroom including the mandatory 256 MiB import reserve. Steady app-managed storage is normally one model and one research pack. This assumes bounded provider originals and does not account for an unlimited user's download library; the app cannot enforce a device-wide 50 GB limit. Actual measured test-fixture storage is reported separately above.

## Immutable artifacts and remaining work

APK SHA-256: `27f9d7824be8b843db7b7238c39c56893005c09f808267cf72e765c87fe0789b`.
Resource test APK SHA-256: `e8c3e7c83fcf1c4615d17a6a05b2fa943efae2e81a6e2e20e54a3604a34be868`.
Raw report SHA-256: `fcdf974c2fce127d4c769c51b3edd96b597b94fc516428185d249a4ba8e7ecaa`.
[Summary](resources/final/summary.json) includes both native library hashes. An attempt to reproduce both measured APKs after the supplemental pack regression failed for the test APK. The final audit archived both exact APKs immediately and their hashes were independently verified against the summary. Final native counters remain held until model destruction completes; both named checks pass with that change. Test-APK byte-reproduction across runner switches remains unresolved and is not claimed. [SHA256SUMS](resources/SHA256SUMS) freezes evidence files.

Remaining gaps include real OS OOM/process-death recovery, allocation-time safety for diverse models, blocking-provider cancellation, long-prefill cancellation latency, maximum-pack retained memory, sustained/thermal behavior, clean-install footprint after platform compilation, external-original accounting and physical Android/GrapheneOS acceptance. The first resource-only raw model answer is inaccurate/truncated and remains preserved; this task establishes no new research-quality claim.
