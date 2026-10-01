# Independent evidence linking — task 221 repair

Status: fixed experiment complete with a negative support-safety result; required quality check fails and no product acceptance is claimed.

The failed checkpoint `15a742f7680dbd1ecdb1adf8414cb687d4306cb3` was recovered onto the current repair branch without changing its sealed task 220/221 artifacts. The coordinator's task 222 specification is the repair strategy. The old 60 questions are not regenerated; all original drafts, same-model audits and eleven historical generated-claim regressions are replay inputs.

Sixteen new paired public development questions and constructed claim probes were frozen in `2f04b00` before implementation and inference. These cover gardening, civics, history and astronomy, including subject, input/output, condition, time, negation, false-premise, formula/number and compound-tail failures. Constructed claims are labeled regression fixtures, never corpus facts. No private holdout is read.

The independent verifier is `cross-encoder/nli-deberta-v3-small`, revision `fa2804872c3b4bd748f38c0185cc85775361e735`, original FP32 ONNX artifact SHA256 `59fd8dd78926e15907ab419303179e4196bdedd710e888773e2f0143fe430897` (568,032,787 bytes). Its pinned model card declares Apache-2.0 and training on SNLI/MultiNLI; the full license and model card are retained. ONNX Runtime runs locally on the CPU with six intra-operation threads and one inter-operation thread. This is an independently trained discriminative classifier, not an independent human reviewer and not proof of entailment.

The fixed thresholds are entailment >=0.95 and contradiction <=0.02 for both the whole generated claim and every sentence. More than 512 input tokens fails closed without truncation. Selected citations are tried first, then each of at most six available passage candidates in source order; every candidate consists only of exact catalog spans. No fact is rewritten or unsupported tail removed. Every candidate input, raw logit, probability, token count, duration and failure are retained. Visible question/subject headings precede unchanged generated prose so hidden metadata does not silently resolve an antecedent.

New generation uses the same Qwen3 4B host candidate, SHA256 `7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5`, unchanged template and greedy CPU six-thread configuration, 4096 context, 320 draft tokens and 192 same-model audit tokens (comparison only). The controller uses independent scores, not that self-audit, for experimental eligibility. No extractive fallback is a generated success.

The first environment attempt failed because ONNX Runtime 1.23.2 had no Python 3.14 wheel on the installed package index. Version 1.24.1 was declared before classifier inference, preserving the original protocol and failed installation log. A test-call argument-order compile error was also preserved and fixed before the successful 25-check behavioral run. These do not change questions, model pins or quality thresholds.

Production remains Qwen2.5 0.5B. Neither the4B model nor this classifier is deployed into the Android answer flow; Android admission remains2GiB/2048context/256generation. The new shared Java controller and renderer are Android-compatible code compiled in the APK, but host replay is not selected-model Android execution. Selected4B admission/load/cancel/reload/resource qualification, verifier mobile runtime and resources, physical Android/GrapheneOS, independent source review and human acceptance remain open.

## Completed fixed experiment: negative quality result

The run is complete and the support-safety requirement **fails**. No threshold, seed, generator wording, model, admission ceiling or scoring architecture was changed after the observations. All 60 old drafts and 11 historical wrappers were reused. Exactly 16 new questions received real local 4B generation; 16 constructed probe records are separately labeled and receive no generated-success credit. The independent verifier evaluated 994 unique premise/hypothesis pairs once, with no failed or truncated pairs. Pair deduplication is across this development matrix, not a deployed cache claim.

| Population | Eligible | Withheld | Fully supported, complete, useful eligible | Unsupported eligible |
| --- | ---: | ---: | ---: | ---: |
| Original 48 (40 supported/false-premise, 8 absent) | 10 | 38 | 8/40 | 2 |
| Previous 12 (11 supported/false-premise, 1 absent) | 5 | 7 | 3/11 | 2 |
| New 16 generated questions | 5 | 11 | 5/16 | 0 |
| Historical 11 generated-claim wrappers | 3 | 8 | 1 repaired wrapper, not fresh generation | 2 |
| New 16 constructed probes | 6 | 10 | 4 supported final bindings, not generation | 2 |

The original 40-case usefulness count is **8**, exceeding task 220's four but below task 221's self-audit count of twelve. Original-old unsupported eligibility falls from seven to two; previous-new unsupported eligibility falls from five to two. This is not a successful safety repair: zero was required. All eight old and one previous-new absent controls remain withheld. No extractive fallback or production publication occurred. Builder support/completeness/usefulness judgments are separate from the classifier and await independent source review.

On the sixteen constructed probes, the classifier/controller admits one of eight negative probes and rejects three of eight positive probes. In addition, a positive probe (`p01`) becomes unsupported because the selected link changes to an inadequate neighboring passage. Thus a binary true/false probe accuracy summary would conceal an actual binding failure.

Concrete false approvals:

- `s10`: compost green/brown inputs cite the vermicompost definition; another clause transfers vermicompost nutrients/fertilizer properties to vermicast. Full-claim entailment scores are 0.980239 and 0.992671.
- `s22`: the codified definition incorrectly allows an arbitrary written set; score 0.987070.
- `n07`: “became capital after joining” contradicts the source's continued capital role; score 0.997265. The new minimally altered `p08` explicitly says “first became” and still scores 0.994191.
- `n02`: the first shared-use claim still lacks the vermicompost use source, and rebinding moves its second water-soluble-nutrient claim away from the correct source to a definition with no such fact. A prose label “P6.1” cannot override the actual typed link.
- `r01`: the historical worm-input transfer remains eligible. `r09` retains a square-root claim despite fifth-root TeX; score 0.982722. A matching approximate decimal does not establish mathematical meaning.
- `p01`: the true end-product probe is rebound from its proper vermicast definition to the vermicompost-mixture definition, which does not establish the asserted output relation; score 0.985380.

Measured useful repairs also remain visible: `l11` and historical `r06` are rebound to the exact magnitude and industrial-products passages without changing generated facts; `n05` recovers a supported negated false-premise correction; `l07` recovers supported Barcelona continuity rejected by the old audit. `n09` gains the previously missing industrial-use and mild-heat source clauses. Its broad lactate food-preservation wording is assessed as a use summary, not a claim of direct unconverted action; the source's lactic-acid conversion qualification remains inspectable and deserves independent scrutiny. Even a stricter judgment there cannot change the definite failed gate.

The renderer exposes question and subject headings. A behavioral replay of the actual `n08` draft now shows Athens before its “It” clause, with correct typed link ranges. The real independent-score route for `n08` is still withheld: this preview is not a newly published or generated success. Template-placeholder subjects/qualifiers and withheld corrections remain product limitations. Neither an exact quote, a source hash nor a high entailment score certifies support.

## Receipts, resources and checks

[All new raw generation](independent-linking/new-run), [raw classifier inputs/scores](independent-linking/scoring), [claim-level builder assessments](independent-linking/review.json), [new raw-draft assessments](independent-linking/new-draft-review.json), [review inputs without builder/classifier judgments](independent-linking/independent-review-inputs.json) and [derived metrics](independent-linking/metrics.json) are preserved. Source dates, rights, document/passage hashes and exact UTF-16 offsets remain bound to the unchanged reviewed edition and index. The original task 220/221 seals pass byte-for-byte checks. The new fixture SHA256 is `183b2c90b71df69ef8f3feb969bbc1a939c14186354461683d6d04fbdc0affbc`.

| Measurement | Actual rig CPU host result |
| --- | --- |
| New generation wall time, 16 questions | 895.233 s |
| New draft first-token p50 / p95 | 31.026 / 59.034 s |
| New draft total p50 / p95 | 40.894 / 72.980 s |
| Draft plus self-audit comparison p50 / p95 | 53.025 / 95.804 s |
| Classifier load / total 994-pair run | 0.711 / 45.880 s |
| Classifier pair p50 / p95 / maximum | 0.04273 / 0.07456 / 0.16356 s |
| Generator load | 1.147 s; filesystem warmed by artifact hashing |
| Generator sampled RSS / kernel HWM / sampled swap peak | 4,999,811,072 / 4,999,811,072 / 33,280,000 bytes |
| Classifier sampled RSS / kernel HWM / swap peak | 884,727,808 / 1,030,778,880 / 0 bytes |
| Native model / KV / compute counters | 4,242,363,904 / 603,979,776 / 80,413,184 bytes |
| Largest actual prompt / total generated tokens | 2,516 / 255; limits remain 4,096 / 512 |
| Generator file / verifier file | 2,497,280,256 / 568,032,787 bytes |
| New debug APK | 11,937,577 bytes; SHA256 `4671e8ce1d90331904c7bc52c6ad54c674f678507457363922cdf8a41db3cfdd` |

Percentiles use nearest rank `ceil(p*n)-1`, over distinct cases or pairs, not repeated process-cold/phone measurements. Native contexts are released after each stage while the model stays resident. Generator and classifier ran serially; these peaks do not prove co-resident memory safety. The native identity also lists dormant `generateClaims` sampler settings; this run used greedy `generateChat`. No PSS, phone thermal behavior, OS OOM safety, or selected-model Android timing was measured. The classifier adds model, tokenizer and runtime storage and requires separate mobile qualification; its local artifact hashes, selected runtime packages’ installed-file hashes and available notices are retained. The tokenizers wheel lacked license files/metadata; the full Apache-2.0 text was obtained from its immutable upstream tagged-source revision `afaae088837b277c19f90604a1111a272838857b` and recorded separately. The classifier model card declares Apache-2.0 but its repository lacks a separate license file; the canonical license text is preserved, not invented publisher-specific terms.

`bash tools/android-build.sh` passes (10 seconds, incremental build: 7 tasks executed and 30 up-to-date). `bash tools/evaluation/check_obligation_binding.sh` passes artifact validation, all 29 shared Java behavioral checks, exact 103-record controller replay, changed/missing model/run rejection and preserved source/provenance/native/production identities, then **exits 1** on unsupported eligible prose and the unsupported constructed probe. The failed check is evidence, not hidden or reclassified as success. Cancellation checks cover the shared transaction boundaries and reuse the sealed real native callback/cancel/retry evidence; they do not establish in-flight ONNX cancellation or Android verifier execution.

Two additional setup failures are retained: replay preparation initially used a relative path where an absolute path was required; a review helper named `inspect.py` then shadowed Python's standard module during ONNX import. Both stopped before classifier inference. Partial preparation and full failure logs remain; completed generation was never repeated. These are distinct implementation faults, not an external blocker.

## Reproduction and next product step

Use `fetch.py` for immutable verifier assets, an isolated ignored virtual environment with the recorded Python package versions, and the preserved new run. `prepare.py <completed-new-run> <fresh-output>` compiles the shared controller and builds exact replay inputs; `score.py <output>` performs one fixed CPU pass; `LinkHarness` binds/renders its score transport. `seal.py` copies only completed text artifacts and refuses different overwrites. `verify.py` replays behavior and checks live model/runtime/APK identities without regenerating old answers. Do not use `run_new.py` again to search for nicer outputs; its sixteen completed records are the immutable new-run input. The already queued task 222 must inspect/reuse this exact strategy and outcome, not duplicate inference.

Queued **223-source-fact-frame-support**, dependent on task 222, is the next materially different bounded experiment: source-first subject/relation/input-output/condition/time constraints and deterministic formula interpretation, with unknown or unparsed factual tails withheld. It must use generic relations rather than question/entity allowlists, preserve this negative matrix, freeze new discriminating cases, and retain zero-unsupported/absent gates. [Exact queued specification](independent-linking/proposed-follow-up.json) and [atomic creation receipt](independent-linking/queue-receipt.json) are recorded; no runner state or dispatch changed. This is not another threshold search or same-model approval loop.

Useful supported production answers, selected-model/verifier Android qualification, candidate release identity revalidation, clean-machine reproduction, production-key ownership, physical Android/GrapheneOS and human acceptance all remain open. No model deployment, publication, push or main advancement occurred.
