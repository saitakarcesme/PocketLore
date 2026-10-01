# Pack scale and real-answer latency: task 170

Both named checks pass on LLMRig with the existing API 35 x86_64 emulator-5560. This is a completed bounded measurement protocol, **not** speed, answer-quality, physical Android/GrapheneOS, thermal or product acceptance. No production admission/recovery changes were needed: all expected imports succeeded, the oversized manifest rejected cleanly, old state survived, and no allocation exception was observed.

## Frozen workload and provenance

Commit **058aba7** froze the [protocol](../../tools/evaluation/scale-latency/protocol.json) and deterministic fixture builder before execution. Protocol SHA-256: 1b656778fcdbb093b7be044789aef4e8a0950d092e5c1ada982065ae68aeccb5. The exact original 186-passage English reference pack is pinned to 567e9bbbaab896826809ec20f81ae1c4b3f421b011931edae0989d28cfce10ea. It retains licensed USGS/NPS/National Archives text, URLs, source dates and rights; see [knowledge-pack provenance](knowledge-pack.md). No new factual text or source content was generated or downloaded. Stress copies keep verbatim original text and rights but use explicit stress-only document IDs. **They are duplication-only fixtures, not a corpus or added factual coverage.** Model, packs and APKs remain ignored.

The [protocol notes](pack-scale-latency/protocol-notes.md) define scope, timing boundaries, memory semantics and limits. Scale cases contain 1, 5, 20, 50, 74 and 75 repetitions. The active admission boundary for this mix is the **2 MiB manifest cap**: 74 copies contain 13,764 passages and a 2,085,378-byte manifest; 75 contain 13,950 passages and a 2,113,580-byte manifest. All remain below 16 MiB archive/expanded bytes, 1,000 documents and 20,000 passages. This is the largest whole-copy fixture admitted, not a universal maximum corpus size or a byte-by-byte proof of every cap.

## Index memory and import transitions

Each scale case starts in a fresh app process, loads the real model and the old 186-passage index, then imports to an isolated directory while retaining the old live index. Source, previous saved pack and staging copies can coexist. After validation and atomic replacement, new and old indexes remain referenced for a requested-GC snapshot; old reference release is measured separately. These are baseline-to-large transitions, not two simultaneous maximum-size indexes.

| Passages | Admission | Import ms | Java used-heap delta bytes | Before / after PSS KiB | Sampled peak PSS / RSS / swap KiB |
| ---: | --- | ---: | ---: | --- | --- |
| 186 | accepted | 88.933 | 696320 | 564146 / 565675 | 575611 / 638672 / 25564 |
| 930 | accepted | 397.945 | 3096576 | 564921 / 576150 | 583874 / 659192 / 25692 |
| 3720 | accepted | 1530.898 | 11866112 | 567416 / 597531 | 639295 / 714832 / 25692 |
| 9300 | accepted | 3726.406 | 29159424 | 571556 / 621278 | 700821 / 775648 / 25564 |
| 13764 | accepted | 5511.986 | 42688512 | 575390 / 640456 | 759315 / 833912 / 25564 |
| 13950 | rejected | 36.896 | -147456 | 575367 / 575514 | 575514 / 650832 / 25564 |


Java used-heap deltas include runtime/allocator behavior and requested-GC variability, not exclusive index-object size. PSS/RSS/swap include native model, runtime and other process memory. The rejected import's negative heap delta is GC variation. Logical index payload is separately recorded: vocabulary remains 1,770 terms while postings grow from 6,001 to 444,074; passage text grows from 59,862 to 4,429,788 characters. This workload does not measure diverse-vocabulary growth.

The maximum accepted import took **5,511.986 ms** (exact raw value is in scale-4.json); post-GC incremental Java heap was **42,688,512 bytes**, with sampled peak process PSS **759,315 KiB**. Times span production KnowledgePack.install, including copy/fsync, ZIP/hash/provenance validation, index construction and atomic replacement. They do not isolate individual CPU/I/O stages. Stage and saved-file logical byte samples are in every raw record; short-lived stage peaks may be missed and these are not allocated-block or provider-wide disk totals.

The next fixture rejected with “Pack exceeds size limit”; previous saved bytes, live old-index research and stage cleanup were checked. All accepted replacements matched fixture SHA-256 and passage count, and retrieval remained usable. [Raw scale observations](pack-scale-latency/scale-observations.json) and measured/scale-0.json through scale-5.json preserve counts, retrieval timings, candidate counts, native buffer observations and all samples. No OS OOM or host memory exhaustion was induced; clean rejection does not prove arbitrary low-memory recovery.

## Real answer latency

One real warm-up answer is preserved and excluded. **Ten subsequent warm requests** share one process and loaded model; **five process-cold requests** use five distinct restarted app processes and fresh model sessions. Both modes use the original real 186-passage pack, not the duplicated stress packs. Native contexts are recreated per request: warm means resident model, not retained prompt/KV cache. OS/filesystem caches are not flushed, so process-cold does not mean storage-cold.

Two frozen questions alternate: “What helps protect skin and eyes from ultraviolet rays?” and “What navigation backups should I bring?”. Warm has five of each measured question; cold has three sun and two navigation questions. These differing mixtures and small samples do not support a causal cold-vs-warm speed claim.

Nearest-rank p50/p95 use sorted values at ceil(p*N)-1 with no interpolation. With five cold samples, p95 is the observed maximum. All values below are milliseconds. The single warm-session setup took 196.444 ms for pack load and 365.114 ms for model load; both are excluded from measured warm request latency.

| Group | Measurement | N | p50 | p95 | Observed range |
| --- | --- | ---: | ---: | ---: | --- |
| warm | retrieval_ms | 10 | 0.171 | 0.254 | 0.139–0.254 |
| warm | request_first_token_ms | 10 | 21963.396 | 22520.789 | 21860.386–22520.789 |
| warm | request_total_ms | 10 | 23773.934 | 24770.900 | 23708.047–24770.900 |
| process_cold | retrieval_ms | 5 | 0.452 | 0.526 | 0.391–0.526 |
| process_cold | request_first_token_ms | 5 | 22077.420 | 22632.726 | 21927.396–22632.726 |
| process_cold | request_total_ms | 5 | 24766.411 | 24898.423 | 23739.368–24898.423 |
| process_cold | model_load_ms | 5 | 343.146 | 353.961 | 341.200–353.961 |
| process_cold | pack_load_ms | 5 | 195.116 | 229.317 | 193.098–229.317 |
| process_cold | ready_to_result_ms | 5 | 25325.892 | 25449.395 | 24291.544–25449.395 |

Retrieval and request totals begin before research; request total ends when AnswerEngine returns and excludes pack/model load. First-token request latency adds retrieval to the first native callback measured from AnswerEngine entry. This is an **unverified draft token**, not first useful supported content. Cold ready-to-result includes pack/model load and setup from instrumentation onStart, but excludes Android launch overhead. Full instrumentation wall times include report/teardown overhead and are retained separately. PSS sampling overhead is included; no CPU isolation or thermal stabilization is claimed.

All ten measured warm and five cold routes are GENERATED; raw prompts, drafts, final linked text, reasons, sources and token counts remain in [warm-0.json](pack-scale-latency/measured/warm-0.json) and cold-0.json through cold-4.json. No response was substituted or templated by the harness. The preserved sun answer says sun protection is necessary but omits specific protective items; the navigation answer says to bring a physical map. These narrow outputs do not establish broad usefulness, independent entailment or superiority. No fallback/abstention is relabeled as generation.

## Memory definitions and environment

| Answer group | Sampled peak PSS KiB | Sampled peak RSS KiB | Sampled peak VmSwap KiB |
| --- | ---: | ---: | ---: |
| warm | 658739 | 698512 | 25564 |
| cold | 641438 | 727716 | 25688 |

Sampling targets 250 ms using Android Debug PSS, /proc/self/status RSS/VmSwap/VmHWM, Java used/max heap, native lease/context/buffer counters and logical file lengths. Timestamps expose actual intervals. Sampled maxima may miss transient peaks; process-lifetime VmHWM is distinct from phase-specific sampled RSS. No swap-PSS value is fabricated. Post-instrumentation dumpsys records may describe an idle/finished process and are not substitutes for in-process phase samples.

[Emulator memory before](pack-scale-latency/measured/emulator-meminfo-before.txt), [after](pack-scale-latency/measured/emulator-meminfo-after.txt), [fingerprint](pack-scale-latency/measured/fingerprint.txt) and separately labeled [host memory](pack-scale-latency/measured/host-meminfo.txt) preserve environment evidence. Host RAM is never phone RAM. This small-model emulator result cannot close the <=12 GB physical-device gate, large-model resource budget, sustained/thermal or background-app pressure gates.

## Identity, failures and reproduction

- Model: Qwen2.5-0.5B Q4_K_M, 491,400,032 bytes, SHA-256 74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db.
- Runtime: pinned llama.cpp bb4caa7540188872173c44d161602d9271386413, CPU, 2,048-token context, one session/sequence and two threads. Full reported identity is retained in every record; its Qwen3 settings text does not rename this Qwen2.5 model.
- App APK: 11,773,557 bytes, SHA-256 ee1d884d40a3b510c680ee8c9b97e470a22f75f953a7330e59503b45c8ab74cd.
- Test APK: 236,434 bytes, SHA-256 b63092d54a52b81f191d1cfa56c2f3773f43a076a047311daff605f48c7a3a60.
- Instrumentation source SHA-256: cd1caa41021893b20e12fdbe6250e094c7323fd1dd5f256e39ee84e07f9015a7.
- [Summary with individual raw-record hashes](pack-scale-latency/measured/summary.json).

The initial harness failed compilation on an unavailable swap-PSS API. Checkpoint **a80af25**, [build log](pack-scale-latency/compile-failure/build.log) and [traceback](pack-scale-latency/compile-failure/check.log) preserve it. The fix uses supported /proc VmSwap observations. No failed answer, allocation or import result was removed; the oversized-manifest rejection is expected and retained. All native contexts/leases are released at each case's end; saved model and research-pack hashes are identical before and after.

Run with the provisioned toolchain, pinned source pack, saved pinned model and already-booted emulator-5560:

    bash tools/android-build.sh
    bash tools/evaluation/check_scale_latency.sh

Both exit 0; see [standalone build](pack-scale-latency/android-build.log), [fixture build](pack-scale-latency/measured/build.log) and per-case instrumentation logs. The checker creates a fresh ignored run directory, verifies exact fixture bytes, runs six scale cases and sixteen real answers serially (one excluded warm-up), checks actual timing/output/cleanup/provenance results and recomputes percentiles. PASS means this behavioral protocol passed, not a performance SLA. No services are started/restarted; only the measured app is force-stopped between processes.

Task 180 remains independent distribution work. Diverse real corpora, large-to-large transitions, large models, independent answer quality, storage-cold behavior, sustained/thermal measurement, physical/GrapheneOS acceptance and a later exact release freeze remain open. No private holdout/context, orchestration/state, branch switch, push or main advancement occurred.
