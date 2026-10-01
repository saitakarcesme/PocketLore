# Supported-answer capability — task 190

**Measured negative model selection; independent review and product acceptance remain open.** All 72 corrected-matrix generations completed on LLMRig. Neither larger candidate improved the frozen fully-supported, complete, useful **published** answer count over current Qwen3 1.7B Q8. Retain the current model pending a bounded complete-claim architecture repair; no larger-model Android integration is selected from these results.

## Frozen experiment and actual results

Commit `d1cc857` froze 24 new public development questions, verbatim excerpts, provenance and expectations before any generation. The [original protocol](../../tools/evaluation/model-capability/protocol.json) remains byte-identical. Cases span geology, genetics, geomagnetism, historical civics, outdoor preparation and travel: 19 answerable cases and five absent-evidence cases, including comparisons, explanations, multi-source questions, qualifiers and four false premises contradicted by real excerpts. These are not synthetic factual passages. False-premise cases do not establish handling of conflicts between independent source documents. No private holdout was read.

The coordinator corrected the current baseline to Qwen3 1.7B Q8. The initial Qwen2.5 0.5B/1.5B attempt is retained as **historical, partial control work**, not as completion of the requested selection. The human then explicitly directed faster host execution. Commits `87fd591`, `d655a4b` and `8a13bd5` froze the [revised execution configuration](../../tools/evaluation/model-capability/execution-v2.json), model pins, host driver and policy before new generation. Questions, excerpts, scoring expectations and production answer grammar were unchanged.

Builder source assessments, **not independent entailment certification**:

| Model | Generated / fallback / abstained routes (24) | Fully useful supported published answers (19 answerable) | Fully useful supported raw answers (19) | Unsupported raw outputs (24) | Unsupported published answers |
|---|---|---:|---:|---:|---:|
| Current Qwen3 1.7B Q8 | 2 / 2 / 20 | 2 | 7 | 6 | 0 |
| Qwen3 4B Q4_K_M | 3 / 1 / 20 | 2 | 7 | 2 | 0 |
| Phi-3.5 Mini Q4_K_M | 2 / 2 / 20 | 0 | 6 | 3 | 0 |

Each model reached JNI through the production controller on four cases. On the other 20, the controller blocked before generation; a separately labeled diagnostic call measured raw capability using the same retained excerpts, template and grammar. Diagnostic drafts are not product publications. All five absent-evidence cases stayed withheld by the controller. Fifteen of 19 supported cases were blocked before JNI; fallback and incomplete generated text account for further lost usefulness. This new oracle-evidence set does **not** repair or replace the earlier frozen retrieval set's twelve blocked supported cases.

“Useful” requires supported requested relationships, essential qualifiers and intelligible complete prose; it is separate from route and factual support. A source-cited fragment can be true but incomplete. Exact quotes, lexical overlap, valid labels and a GENERATED flag do not establish entailment. Ratings and reasons for every output are in [builder assessments](model-capability/builder-assessments.json); borderline inference/omission judgments are visible for independent review. Counts are descriptive development results, not general capability estimates.

## Concrete failures and selection

- **Evidence selection:** `cap-10` offers storm and reversal excerpts, but the unchanged production selector keeps only the storm excerpt. Qwen3 1.7B invents reversal details; the larger candidates disclose missing reversal evidence. Review inputs distinguish offered sources from sources actually retained in the prompt. A model cannot reliably repair dropped evidence by guessing.
- **Scope and citations:** Qwen3 4B `cap-21` changes hikes **from** trailheads before camping into hikes **to reach** trailheads. Both larger models' `cap-22` river claims cite the map-status excerpt rather than the excerpt containing the river facts. Structurally valid citations therefore conceal unsupported claim-to-source links.
- **Absent evidence and qualifiers:** current Qwen3 1.7B invents a cat chromosome count and affirms a regular 780,000-year magnetic-reversal schedule. Phi's `cap-24` refuses live trail status but then overstates precautions as ensuring safety. These remain diagnostic failures, not published answers.
- **Claim architecture:** the grammar limits each claim body to 220 characters and forces two claims for comparisons. Current-baseline civics output ends with an unsupported “district 17”; Qwen3 4B's civics comparison ends mid-clause with a non-English character. Phi `cap-13` emits only cited list numbers. Phi's **published** earthquake and DNA explanations include supported facts but terminate mid-clause or mid-word. The raw non-English failure is deliberately preserved, not presented as accepted English product content.
- **Conservative publication filter:** Qwen3 4B's supported headlamp paraphrase and Phi's supported magma/lava comparison are withheld for lexical weakness. More capacity alone does not solve these controller losses.

The predeclared rule requires a strict increase in fully useful supported publication with no unsupported-publication or absent-case regression. Qwen3 4B ties the current model, and Phi scores lower; no replacement qualifies. Larger candidates reduce some raw unsupported answers, but do not solve completeness and publication losses under this architecture.

The concrete next step is [task 200: complete-claim output](model-capability/queued-follow-up.json), created in the authorized private task queue with task 190 as dependency. It replaces forced character-level endings and mandatory two-claim shape with bounded complete claims, keeps the current model/token budgets/safety controls, freezes eight additional public cases, and measures actual before/after usefulness plus a discriminating emulator subset. It is a product architecture repair, not further prompt/seed search or marginal inventory work. Runner dispatch and canonical criticism remain separate; no runner state was modified. Evidence selection, lexical coverage and broader research quality remain additional open gaps.

## Pinned models, licenses and identity

Loader metadata reports **1.72B / 4.02B / 3.82B** parameters, with `qwen3 / qwen3 / phi3` architectures. The two new alternatives have genuinely greater capacity than the current baseline and are distinct model families. Quantizations were supplied by publishers/community maintainers, not reproduced here.

| Model and license | Immutable GGUF repository revision | Actual verified bytes | Actual SHA-256 |
|---|---|---:|---|
| [Qwen3 1.7B Q8, Apache-2.0](https://huggingface.co/Qwen/Qwen3-1.7B-GGUF/tree/90862c4b9d2787eaed51d12237eafdfe7c5f6077) | `90862c4b9d2787eaed51d12237eafdfe7c5f6077` | 1834426016 | `061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a` |
| [Qwen3 4B Q4_K_M, Apache-2.0](https://huggingface.co/Qwen/Qwen3-4B-GGUF/tree/bc640142c66e1fdd12af0bd68f40445458f3869b) | `bc640142c66e1fdd12af0bd68f40445458f3869b` | 2497280256 | `7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5` |
| [Phi-3.5 Mini Q4_K_M, MIT](https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF/tree/6d70da17e749a471ccb62ade694486011a75cda3) | `6d70da17e749a471ccb62ade694486011a75cda3` | 2393232672 | `e4165e3a71af97f1b4820da61079826d8752a2088e313af0c7d346796c38eff5` |

The new upstream license revisions are Qwen3 4B `1cfa9a7208912126459214e8b04321603b3df60c` and Microsoft Phi-3.5 Mini `2fe192450127e6a83f7441aef6e3ca586c338b77`. Full texts, immutable license URLs and publisher/quantizer attribution are retained in the [candidate pins and licenses](../../tools/evaluation/model-capability) and `THIRD_PARTY_NOTICES`. All model files remain ignored; none entered Git or the APK. All three individual files are below 4 GiB.

The host library uses pinned llama.cpp `bb4caa7540188872173c44d161602d9271386413`; measured library SHA-256 is `2af1eb5011a3cf3fa58af7c074cc8b14126bf0d67efd2d65bdb804de1cfbe67f`. The actual Java `AnswerEngine`/`EvidencePrompt`, chat formatter, claim grammar and production sampling policy run through JNI. Host-only compilation enables native CPU ISA, six inference threads and a 4 GiB file/model-buffer screen. Android retains two threads, its existing ISA settings and 2 GiB file/model screen, even if the host macro were accidentally specified. Existing 768 MiB KV and 1 GiB compute screens remain. The new larger files would exceed current Android admission; no phone suitability is inferred.

All models use context 2048 and output budget 256. Qwen3 uses production non-thinking formatting, temperature 0.7, top-k 20, top-p 0.8, presence penalty 1.5/256 and seed 42; Phi uses production greedy decoding. Thus this is a matched production-policy/budget comparison, **not sampling-matched architecture isolation**. One generation per case/model, no seed search and no prompt revision. CPU ISA/floating-point differences can affect reproduction across hosts.

## Host measurements and limits

Measured available host RAM at admission was **17,214,332,928 bytes**; the declared two-process threshold is 12 GiB. At most two independent six-inference-thread processes ran; JVM helper threads are additional. No concurrent emulator work or GPU job ran. GPU access failed inside the scoped sandbox; this does not contradict the coordinator's host report of idle RTX3090s and is not a hardware blocker. No GPU stack, service or global preference was changed.

The corrected matrix ran from 05:23:00.954 to 05:32:12.138 UTC, about **551 seconds**, excluding fetch/build. Each model loaded once; each answer got a fresh context. Host wall times below include up to two processes competing for resources; they are **not a model speed ranking or a comparison with old scalar/emulator runs**.

| Model | Load ms | First-token p50 / p95 ms | Total p50 / p95 ms | Sampled peak process RSS KiB | Sampled process swap KiB |
|---|---:|---:|---:|---:|---:|
| Qwen3 1.7B Q8 | 523.238 | 5228.145 / 7146.031 | 7316.720 / 14174.521 | 2262452 | 0 |
| Qwen3 4B Q4_K_M | 992.764 | 8493.376 / 13277.672 | 11736.614 / 23756.615 | 4650252 | 0 |
| Phi-3.5 Mini Q4_K_M | 1315.292 | 8111.412 / 12758.669 | 13584.518 / 22030.820 | 4476744 | 0 |

Percentiles use nearest rank `ceil(p*n)-1` over each model's 24 calls, including diagnostic calls. First token is the first unverified callback, not time to useful answer. Controller-invoked totals include controller preparation/validation; diagnostic totals measure the native call path, with controller totals separately recorded. RSS/VmSwap are one-second process samples including JVM and native allocations, not exact peaks/PSS, OS-OOM proof, host-wide zero swap, phone RAM or thermal measurements. No allocation failure occurred in this matrix. Host snapshots and all samples are retained.

## Evidence, reproduction and checks

- [Manifest and receipts](model-capability/run/manifest.json): exact models, commands, timestamps, runtime/source hashes and actual zero process exit codes.
- [Identity-blind review inputs](model-capability/blind-review.json): full questions, expectations, offered/retained evidence, exact prompts, raw drafts and publication routes; [identity key](model-capability/identity-key.json) is separate. Reviewer blinding and independent source judgments are not claimed to have occurred.
- [Builder assessments](model-capability/builder-assessments.json) and [summary](model-capability/summary.json): all 72 explicit judgments with record hashes, separate from machine identity/budget checks.
- [Historical partial attempt](model-capability/historical-cpu-partial/status.json): old 0.5B completed 24; old 1.5B completed only one. The interrupted case had no completed record and that original harness did not persist partial tokens. New runs persist partial text/active-case state. The initial missing-CMake failure and installed-toolchain correction are retained in build logs.

```sh
python3 tools/evaluation/model-capability/fetch_candidates.py
bash tools/runtime/build-host.sh
python3 tools/evaluation/run_model_capability_v2.py
python3 tools/evaluation/verify_model_capability.py
```

The baseline and two original licensed packs must already be available at their pinned ignored paths. A new run writes a new ignored directory; it does not overwrite frozen evidence or automatically replace builder ratings. The verifier validates the recorded matrix against actual local model/library/source bytes. It must fail if those artifacts are missing or changed; it is not a source-entailment oracle.

Android build passed after the host-only change: debug APK SHA-256 `4ff562b46fbfa947e698ee6c0e5b2f3d2b042e6467bfa78366f5833e48faba8a`. The executed policy regression rejects a 3 GiB model buffer by default and under Android, accepting it only in the explicit non-Android host build. Final matrix verification and mutation receipts are recorded alongside this report.

Release work remains incomplete: queued product repair, selector/coverage and source-support gaps, independent review, refreshed exact-artifact release evidence, physical Android/GrapheneOS, human usefulness and owner distribution decisions remain open. The separate acquisition worker's private staging was not read; no new manifest was supplied to alter this experiment. No private holdout, credentials, orchestration/state, emulator supervision, branch switch, push, main advancement, bounty submission or superiority claim is involved.
