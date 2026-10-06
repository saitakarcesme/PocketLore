# Exact strong-model scalar host execution — task 534

**Current result: HOST_ENGINEERING_INCOMPLETE.** Required Android build: **0**. Required strong-native-host checker: **1**. The single permitted screen attempted original probe 1 once, stopped at the unchanged aggregate memory limit, and did not run probe 2. No generated output or useful-answer success is claimed. No implementation was changed after this screen.

## Implementation and lineage

Accepted prerequisite d34abaa2a76a8d90141cb7bf569c493cb95d1bf5 established bounded owned-fd mapping/cache controls only; its original receipts remain unchanged. Checkpoints e50e244 and 20dad9b add universal scalar diagnostic scheduling and bounded failure collection. The ordinary model admissions, prefetch/repack defaults and Android product behavior remain unchanged.

The opt-in exact-asset route now uses n_batch=1/n_ubatch=1 and exactly one token per llama_decode throughout prefill and generation, retaining context1024, two threads, greedy sampling and max128 output tokens. A reusable scalar_step holds the owned reader through synchronization, releases it, then calls targeted advice. Load completion also receives advice. No mid-graph eviction, expert pruning, quantization change, smaller model or global cap increase was introduced. Cancellation/exception handling retains native RAII release and PID-owned TERM/KILL/reap controls.

The two original public prompt files remain byte-identical (0541f16c... and d1b56364...). Their original source freeze SHA is 8333619a074f93950999d1319035f578aaaa9dfbd3ef5f38f5a1b8873791a537. The separate route.json explicitly freezes changed settings and a first-failure-stop policy; no original freeze was rewritten. Current full frozen input packet SHA: 2009c7ce4df70f4e06a66c4a095d2e701e8f8c2cce712baaef9b8c9a70403d2b.

The old 531 failure is preserved byte-for-byte: receipt acc6df50c95cd5af63236adaa001d46eb86aaf7a3e876bfb452e6279f506327c and independent manifest ba1cec4daeddbc08ebc448ce4fac1ac46aff56315636851b8db7cf862569829d. That batch32/ubatch16 first prefill stopped after 6.673 seconds with zero output; its aggregate measurement was not model-only RSS or a kernel OOM. The old tools and raw failure remain under strong-scalar-inputs/historical and are embedded in current review evidence.

## Linked builds and controls before execution

The host CLI, native fixture executable, ARM64 and x86_64 libraries linked from isolated pinned bb4caa7540188872173c44d161602d9271386413 derivation bc318d6b7c43ed3cf129117df56a6c81e6154944284d7ed28b00986d4cf531f4. Honest pinned-plus-modified metadata remains content-addressed. All four native hashes were stable across checkpoint/reconfiguration. ELF machines, 16 KiB LOAD/ZIP alignment and packaged library hashes passed before the screen.

| Artifact | SHA-256 |
|---|---|
| Host CLI | 3ab63ab83374c681f1b8e9d33c9997c4b2f4c9fd281011a1dbf219844ad465f3 |
| Native controls | 3d34e8cbd9efeb68bb1062baa056683dbb318fad6ee10cbc4bcd129e3ae33419 |
| ARM64 library | b5c0740c14036104b9fa94ec8cc6205d36cdbc97a7c5035b3e71f5da13d6452c |
| x86_64 library | ca983487c421bc0d060c79946120ac17cbcd03a3705040277f173d509f98010c |
| APK | 573d9c2d0a3fd603cd91b5517588779c73e511e4c876f92be00ee330fc3a055b |

Seven pre-screen control groups passed: malformed/unreadable raw collection, owned hung worker KILL/reap, read error, failed child, native cancellation, native expiry, and real mmap scalar/lifecycle controls. The scalar fixture independently checks 33 sequential byte reads/synchronizations, rejects multi-token input before callbacks, rejects advice with a live reader, synchronizes exceptions, and stops cancelled work. Existing alias, lifetime, identity, expiry and teardown controls remain. These are engineered algorithm controls, not model generation.

Independent pre-screen review identified an unguarded collection path. Before freezing or loading the model, bounded byte-first collection was added and tested with malformed UTF-8 and a real directory-read error. Current source/derivation/build configuration/binary identities were frozen before spawn and checked after release. Logs are bounded; no unbounded process pipes are used.

## Actual single-case result

One native held-readonly-fd streaming SHA pass verified the entire unchanged 12,290,628,576-byte Qwen3.6-35B-A3B model against 96b9c0af5c77a4ecaabe3983175112b5ece763261c1ece12b2494b692a70dad7. There was no separate Python full hash, repeated sweep, second model load or retry. The loaded mapping uses actual fd/mount/namespace identity rather than retroactive foreign-VMA attribution.

Case 1 lasted **43.646 seconds**, including identity hashing and loading. It recorded **430 live samples**, namespace PID **5**, kernel startticks **49053938**, and tokenized the unchanged prompt into **379 tokens**. Logs contain SCALAR_BEGIN 0 1 / SCALAR_END 0 0, then SCALAR_BEGIN 1 1. Thus one scalar prefill completed with synchronization/advice; the second did not complete. Generation never began, stdout was empty, and case 2 is explicitly unrun.

The 100 ms monitor observed aggregate cgroup current **8,460,570,624 bytes**, above the unchanged **8,053,063,680-byte** stop, and issued TERM. The polling overshoot is reported, not treated as a raised cap. The child exited **12** and was reaped **63 ms** after TERM; KILL was unnecessary. Context/backend release and released_after_scope markers are retained. No successful final model-release observation is claimed after cancellation.

Maximum sampled process RSS was **1,995,083,776 bytes**, HWM **2,007,703,552 bytes**, swap **0**, and threads **2**. The separately observed unit lifetime peak was **8,460,570,624 bytes**, not process RSS. Case-start aggregate current was **1,786,793,984 bytes**. Near the stop, sequential kernel memory.stat readings reported file **7,896,768,512**, anonymous **472,039,424**, and kernel **38,600,704** bytes. These describe the supervising cgroup, not an exact per-model attribution or an atomic total. Kernel OOM/max event counters remained zero.

The synchronous post-load observation reported RSS **92,975,104**, PSS **89,505,792**, anonymous **85,970,944** bytes, with zero mincore-present pages in the owned weight mapping. Before prefill it reported RSS **203,264,000**, PSS **199,794,688**, anonymous **195,825,664** bytes, also zero mapping-cache pages. Quiescent load advice therefore did not establish a safe subsequent decode working set. No claim is made that file-cache bytes equal model RSS or that this model necessarily requires the entire observed aggregate alone.

The process limits remained CPU150soft/160hard, 180-second wall, swap0 and 7.5 GiB stop under the 9 GiB/CPU200/four-affinity/Tasks512 supervisor. Fresh host availability passed the 11 GiB preflights. User-bus querying was unavailable in this namespace; its exact failure is retained, rather than fabricating observed Restart/RuntimeMax settings. Process limits and the one-attempt guard are directly enforced. No service or device was changed.

## Gate, criticism and remaining work

The checker freezes every attempted raw case and the explicit unrun denominator before validation. It requires both genuine generated outputs and source/binary/namespace/phase/resource identity. The incomplete screen fails; corrupted-generation-receipt negatives receive no discriminatory credit from this failing baseline. Previous 533 fixture success is not transferred to this changed executable.

Frozen receipts show one scalar token completed before the aggregate stop, followed by TERM and reaping with zero output; the skipped second probe and failed gate leave generation, memory fit, and Android behavior unqualified.

A future attempt needs a separately reviewed material change addressing measured cache charging between quiescent boundaries; merely replaying scalar prefill or raising limits is not justified. This task stops the screen here. Original 500/524 useful explanation/comparison/synthesis and independent entailment, source admission, actual Android JNI/UI/cancel/reuse/restart, physical12GB/no-GMS, complete45GBtarget/50GB installed-provider-temp-update-rollback, and all unseen rival gates remain open. There are no outputs to grade for source support. The terminal emulator, original model/source assets and independent source jobs remain untouched.
