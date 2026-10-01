# Scale model quality: fixed host comparison

Builder evidence for task 220; independent criticism and product acceptance remain pending. The host screen selects **Qwen3 4B Q4_K_M for the next integration step**. It is not deployed or Android-qualified: `tools/answers/model.env` still pins the actual Qwen2.5 0.5B production model. The answer architecture is not ready for promotion: only four of forty supported cases yield a fully useful 4B answer that also passes its controller.

## Frozen evidence and execution

Commit f9522c5 froze 48 new public questions before implementation: eight topic pairs, each containing literal, explanation, comparison, multi-part, false-premise and absent cases. There are 40 supported/false-premise cases, eight absent controls, 65 question obligations, 16 real source documents and 48 distinct paragraphs. This is a narrow development sample, not encyclopedic or holdout coverage.

A source-only preflight amendment in 45d4ea4 selected the explicit worst-case BST and negative-magnitude paragraphs before any candidate generation. Questions, expectations and model pins did not change; the initial freeze and before/after source hashes remain in Git and `tools/evaluation/scale-model-quality/preflight-amendment.json`. Every model used amended protocol SHA256 `061bb57fb3c0fa6715762846ad8ef1c72f004417e41ad5426b2534d8c90a512b`.

Each question receives the same six pinned paragraphs from two articles, with titles, dates and stable source identities. The verifier checks their exact text, document hashes, dates and rights against the reviewed disk-backed edition: pack SHA256 `b8d18801b099402205938979ab2bb44ee9a316f06f030aab789cf93ba3605012`, SQLite SHA256 `9009b19de43f851a815d1797779a94ab47077cc2fc5b3dfe70fc4bdf9a097386`. Expectations are never sent to the model. This **oracle-evidence screen bypasses production retrieval and its pre-generation absence gate**; it cannot establish end-to-end retrieval usefulness.

The experimental `ObligationAnswer` controller deterministically separates semicolon obligations, offers a diverse reading order, and bounds context to six source paragraphs and one to four obligations. It uses the existing citation, complete-clause, temporal and lexical/number screens, which are not entailment proofs. It is not wired into the production UI. Production retrieval and source-scope protections remain unchanged.

All 192 quality calls ran locally through real JNI/llama.cpp `bb4caa7540188872173c44d161602d9271386413`, CPU native ISA, six inference threads, 4096 context tokens and a 512-token generation ceiling. Excerpt limits stayed at 1200 characters for every case. Each model uses its pinned GGUF chat template; Qwen3 retains the non-thinking assistant prefix. Every call uses greedy `generateChat`, not the dormant stochastic `generateClaims` settings also printed in the runtime identity. There are no seed searches, prompt retries, canned answers or extractive fallbacks in this matrix.

## Model artifacts and rights

| Role/model | File bytes | SHA256 |
| --- | ---: | --- |
| Production Qwen2.5 0.5B Q4_K_M | 491,400,032 | `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db` |
| Qwen3 4B Q4_K_M | 2,497,280,256 | `7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5` |
| Qwen2.5 7B Q4_K_M | 4,683,074,240 | `65b8fcd92af6b4fefa935c625d1ac27ea29dcb6ee14589c55a8f115ceaaa1423` |
| Qwen1.5 MoE A2.7B Q2_K | 5,890,164,032 | `cce008140714bb8b76185c0e2db802c60ce62182fa2eddb86ac53303b7525986` |

Immutable repositories/revisions, base-model revisions, full licenses and model cards are in `tools/evaluation/model-capability/{baseline,qwen3-4b}.json` and `tools/evaluation/scale-model-quality/{qwen25-7b,qwen15-moe}.json`, with attribution in THIRD_PARTY_NOTICES. The three dense models use Apache 2.0; MoE uses the archived custom Tongyi Qianwen agreement, not Apache 2.0. Its 14.3B total/2.7B active model uses Q2_K to fit the predeclared file cap; these results do not isolate capacity, training, architecture or quantization effects. All four files are below the 6,000,000,000-byte candidate ceiling. Weights remain ignored and were not published. The already downloaded 4B artifact was reused unchanged.

## Actual quality and controller routes

Every draft has a separate builder clause/source assessment in [reviews](scale-model-quality/reviews). [Obligation/source review inputs](scale-model-quality/obligation-source-review.json) bind each requested obligation to its raw slots and exact cited excerpts. Independent source review is still required.

“Useful draft” requires supported facts, correct cited excerpts, all obligations and complete usable prose. A paragraph citation can establish subsequent sentences only if its cited excerpt actually supports them; the unchanged machine sentence-citation gate remains separately reported. Withheld drafts never count as usable screen answers. All results here are experimental: **zero production publications**, and no fallback receives generated-success credit.

| Model | Useful supported drafts /40 | All screen candidates | Fully useful screen candidates /40 | Unsupported screen candidates | Fully source-faithful absent responses /8 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Production Qwen2.5 0.5B Q4_K_M | 1 | 0 | 0 | 0 | 4 |
| Qwen3 4B Q4_K_M | 26 | 5 | 4 | 0 | 8 |
| Qwen2.5 7B Q4_K_M | 24 | 7 | 5 | 1 | 8 |
| Qwen1.5 MoE A2.7B Q2_K | 0 | 0 | 0 | 0 | 2 |

Controller routes are baseline 0 candidate/48 withheld, 4B 5/43, 7B 7/41 and MoE 0/48. All eight absent controls are withheld for every model, sometimes because another formatting/support screen fails rather than because the model abstains correctly. The 4B and 7B candidate sets each contain one incomplete explanation. MoE explicitly withholds four absent questions, but two additionally misdescribe the supplied source set; only two meet the strict full-response source-faithfulness criterion. These builder judgments are exposed for independent reassessment.

4B wins the declared draft-support/completeness ranking (26 versus 24 for 7B) with a smaller file and native footprint, and no observed unsupported screen candidate. This is a **candidate selection**, not a promotion decision. Fixing citation formatting alone would risk admitting unsupported 4B drafts presently caught by formatting failures.

| Preserved failure | Source-review finding |
| --- | --- |
| 4B s02 | Names insertion-order degeneracy but does not explain the resulting tree shape/search work; supported yet incomplete. The initial optimistic builder rating was corrected in Git. |
| 4B s08/s09 | Treats vermicast as decomposed input rather than earthworm output and transfers compost properties to vermicompost. |
| 4B s22; 7B s22 | Lose or reverse the single-comprehensive-document condition for codification. |
| 7B s16 | Passes the lexical controller while transferring protection from smaller pruning wounds into a general reason for pruning unwanted material. |
| 4B s34; 7B s34 | Change “continued to be” into “became after,” or move the founding-story tradition qualifier to later political roles. |
| 7B s40/s43/s46 | Correct facts cite neighboring paragraphs that do not establish them; magnitude-sign coverage is also incomplete. |
| MoE s25/s27 | Transfers Andorra facts/capitals to Aruba and invents shared capitals. |
| MoE s36/s46 | Fabricates live opening hours/prices; elsewhere calls a fifth root a square root while retaining 2.512. |
| Formula/article-footnote output | Brackets can be mistaken for application citation IDs; this is a distinct parser failure, not evidence that a claim is unsupported or safe. |

The older [3/27 complete-claim outcome](complete-claim-output.md) and [task-212 outcomes](broad-answer-integration.md) remain intact. Task 212 published three supported answers, only two fully useful out of eight supported cases, and preserved two earlier unsupported drafts. Its old retrieval result remains 24/32 with two gains and two losses. Different cases, models and budgets prevent treating the new oracle scores as an end-to-end before/after improvement.

## Resource failures, timing and memory

The initial stage preserved 48 zero-token post-allocation budget rejections for each of 7B and MoE. Their processes exited normally because the harness recorded exceptions; they are not successful quality runs. CPU mapped plus repacked weight buffers exceeded the original 6 GB file-equals-buffer assumption. These were budget rejections, not demonstrated OS OOM recovery. Failed-stage peak RSS was 7,674,200 KiB and 8,317,828 KiB, with zero sampled process swap.

Commit 097fe24 declared the resource-only revision before either large model generated a token: retain the 6 GB file cap, allow 9 GB native host weight buffers, and retain 768 MiB KV/1 GiB compute caps. Kernels, model pins, prompts, context and decoder stayed fixed. The successful baseline/4B calls were not repeated. The revised scheduler admits one large model at a time with 10 GB (7B) or 10.5 GB (MoE) reservation plus 2 GiB available host margin, a 10.5 GB sampled RSS ceiling and four-hour per-model timeout. It briefly overlaps the already active 4B process, never exceeding two six-thread inference jobs.

The executor could not access a working GPU driver interface; [the preflight](scale-model-quality/gpu-preflight.txt) is not evidence that the host lacks GPUs. No GPU stack or service was changed.

| Model | Load seconds | First token p50 / p95 seconds | Total p50 / p95 seconds | Output tokens p50 / p95 |
| --- | ---: | ---: | ---: | ---: |
| Production Qwen2.5 0.5B Q4_K_M | 0.452 | 7.304 / 11.235 | 9.881 / 18.870 | 68 / 512 |
| Qwen3 4B Q4_K_M | 1.638 | 29.034 / 41.016 | 36.898 / 67.746 | 62 / 182 |
| Qwen2.5 7B Q4_K_M | 6.931 | 34.245 / 58.462 | 46.750 / 80.130 | 59 / 183 |
| Qwen1.5 MoE A2.7B Q2_K | 14.697 | 15.779 / 23.677 | 31.155 / 47.040 | 234 / 512 |

Percentiles use nearest rank, sorted values at `ceil(p*n)-1`, with n=48 different questions per model. First-token time starts at `generateChat`, including context creation/prefill; total ends after generation and incremental output capture. Load and token counting are separate. Each question starts with a fresh context under one loaded model handle; preflight hashing can warm file cache. Concurrency and measured swap differ across stages. These are neither process-cold repetitions nor isolated speed rankings, thermal tests or phone measurements.

| Model | Native weight / KV / compute peak bytes | Process RSS peak bytes | Process swap peak bytes |
| --- | --- | ---: | ---: |
| Production Qwen2.5 0.5B Q4_K_M | 514,869,760 / 50,331,648 / 78,709,248 | 760,254,464 | 0 |
| Qwen3 4B Q4_K_M | 4,242,363,904 / 603,979,776 / 80,413,184 | 4,976,906,240 | 436,133,888 |
| Qwen2.5 7B Q4_K_M | 7,798,468,608 / 234,881,024 / 81,527,296 | 8,180,408,320 | 43,065,344 |
| Qwen1.5 MoE A2.7B Q2_K | 8,219,912,192 / 805,306,368 / 86,244,864 | 8,972,570,624 | 39,878,656 |

Native values are callback-observed buffer accounting, not whole-process PSS or OS allocation peaks. Context counters return to zero after each call while the model handle remains resident; this does not mean zero model RAM. RSS/swap are sampled once per second and can miss transients; their maxima need not coincide. Full per-case/context/timing and per-second process samples are in [metrics](scale-model-quality/metrics.json) and the immutable run directories.

## Android and disk limits

Android still has the 2 GiB model ceiling, 2048-token context, 256-token output and existing thread policy. A compiled test defines every host macro together with `__ANDROID__` and verifies that none changes these limits. There was no selected-candidate Android inference or admission increase. The existing emulator-5560 preflight reports MemTotal 2,532,896 KiB and MemAvailable 1,742,904 KiB; the 4B file alone exceeds the current application ceiling. A coordinator-approved sufficiently provisioned emulator/device is needed for actual selected-model load, cancellation, reload, combined index/native memory and JNI quality qualification. Missing KVM is not asserted as a current blocker.

Measured files: new APK 11,937,577 bytes, reviewed broad pack archive 46,339,444 bytes, SQLite index 121,401,344 bytes, selected model 2,497,280,256 bytes. All four host model downloads total 13,561,918,560 bytes; they are development assets, not an Android installation. APK SHA256 is `d2c834f07a663a4920e179c4f8c10310cb91d25c2053705084571c3ae61c83c0`.

A conservative **planning estimate**, not a measured candidate import, reserves three selected-model copies (provider/staging/final), the old 491,400,032-byte model, two index copies, the archive and APK: 8,284,320,509 bytes. Adding 1 GiB for the small editions, caches and administration gives 9,358,062,333 bytes. This fits the 45 GB target/50 GB hard budget on paper; actual selected-model import transitions and all active future editions still require accounting before promotion. It establishes no <=12 GB phone-RAM result.

## Checks, reproduction and next action

Both required checks pass: `bash tools/android-build.sh` (final build eight seconds) and `python3 tools/evaluation/verify_scale_model_quality.py`. The verifier replays all 192 actual drafts through compiled Java controller code, checks exact SQLite source/provenance rows and model/library/source/APK hashes, exercises three native resource profiles with nine over-budget rejections, and rejects actual missing/changed run files plus missing/changed model files. It preserves all 96 initial zero-token failures. It certifies artifact integrity and behavior, not factual entailment or acceptance. The earlier partial-verifier failure remains archived.

For a new measurement, use a separate rig source/build copy at the recorded initial-stage commit 9db899b and buffer-v2 commit 097fe24, with the tool versions and exact reviewed edition above. Preserve the original native libraries and sealed run directories. The following are the provisioning and historical stage commands; provisioning is online-only and inference is local:

```bash
python3 tools/evaluation/scale-model-quality/fetch.py
bash tools/runtime/build-scale-host.sh
python3 tools/evaluation/scale-model-quality/run.py
bash tools/runtime/build-scale-host-buffer-v2.sh
python3 tools/evaluation/scale-model-quality/run_buffer_v2.py
bash tools/android-build.sh
```

Run `python3 tools/evaluation/verify_scale_model_quality.py` in the preserved checkpoint to verify its sealed artifacts; a new build/run needs its own receipts and review rather than being substituted into that checkpoint. The two runner commands create new timestamped raw directories; they do not replace sealed evidence. The first reproduces the historical stricter-budget attempts, including expected large-model failures. Sequential execution is a bounded reproduction route; recorded overlap/timing comes from the archived scheduler receipts. `seal.py` refuses divergent overwrites, and source/assessment changes require a new reviewed checkpoint. Tool versions, acquisition receipts, build logs and SHA256SUMS are archived beside the raw results. Independent clean-machine reproduction is still open.

The sealed Android worker handoff was read and hash-checked only; [its audit](scale-model-quality/android-handoff-audit.json) records no merge, a same-baseline answer-check failure, unchanged 2 GiB ceiling and missing emulator execution. Wiki/places handoffs were not sealed when checked and were not read or used as installed coverage.

Queued [221-obligation-source-binding](scale-model-quality/queued-follow-up.json), dependent on task 220, is a material controller/representation repair: typed per-obligation claim/source spans, subject/qualifier preservation, formula/footnote-safe citation rendering and real 4B output evaluation. It must exceed four fully useful screen answers out of forty without unsupported candidates, keep all eight absent controls withheld, freeze twelve new cases and preserve every current failure. [The queue receipt](scale-model-quality/queue-receipt.json) covers only the task specification; no runner state or dispatch was changed.

Future support regressions must also wrap preserved unsafe drafts in structurally valid new records, so rejection of old syntax cannot masquerade as repaired source-support validation.

Selected-model Android admission and real JNI qualification, current candidate/release identity validation (existing task 213), physical Android/GrapheneOS, sustained device limits, owner signing, independent source/rights criticism and human usefulness remain open. No publication, main advancement or product acceptance is claimed.
