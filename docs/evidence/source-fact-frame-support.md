# Task 223: source-frame prototype reused and coverage made explicit

Task221 repair2 already implemented and measured this exact source-first strategy. Task222 reuse and guarded repair preserve the independently trained classifier failure separately. This task reuses all **143 records**:103 prior draft/probe records,20 real new4B drafts and20 new constructed probes. No generation, classifier inference, threshold search, parser-rule change or new asset acquisition occurred. The frozen20-case specification, fixed994 classifier pairs, raw frames, parse errors, span mappings and historical failures remain unchanged. This is public retrospective development, not held-out generalization or product acceptance.

Both task223 commands pass: `bash tools/android-build.sh` and `bash tools/evaluation/check_source_fact_frames.sh`. The first validation attempt correctly rejected the old frame APK identity after task222 added shared code; [that failure](source-frames-reuse/initial-check.log) is preserved. The check now pins task222's separate current APK receipt without replacing the original sealed receipt. Actual APK SHA256 is `2d04838f2bf676b474e355d93e5228b775acc4d444a17f8eee1542b6bd51b1db`. [Fresh build](source-frames-reuse/android-build.log) and [final check](source-frames-reuse/final-check.log) record the results. The source-frame parser itself is hash-identical to its prior measured implementation.

The check recompiles and replays the actual143-record controller, runs39 frame and29 original linking/renderer behavioral tests, verifies live pinned model/native/source artifacts and exact typed spans, and rejects changed/missing model/run artifacts. It derives and checks a new [coverage breakdown](source-frames-reuse/coverage.json) directly from frozen fixtures, final routes and separately identified builder assessments. It does not regenerate prose or treat classifier labels as entailment.

| Generated question population | Useful eligible / all questions | Complete / eligible | Supported / eligible | Withheld |
| --- | ---: | ---: | ---: | ---: |
| Original48, including8 absent |5/48|5/5|5/5|43 |
| Previous new12, including1 absent |1/12|1/1|1/1|11 |
| Independent-linking new16 |1/16|1/1|1/1|15 |
| Source-frame new20, including2 absent |1/20|1/1|1/1|19 |

The required supported-old denominator remains **5/40**, and all **eleven absent controls** withhold. Conditional builder-assessed support precision is100% among the eight eligible generated answers, but useful question coverage is only8/96 overall (including absent questions), and5/40 on supported old cases. This small conditional count is not evidence of100% general factual precision. Historical wrappers and constructed probes are excluded from generated-success counts. Completeness of a withheld answer is not inferred from its W label.

False rejections remain severe: the prior16 probes contain8 expected positives, of which7 are rejected; the new20 probes contain8 expected positives, all8 rejected. All20 expected negative probes across both sets withhold. New t10's positive prose has a conflicting Barcelona wrapper heading; it remains counted as a rejection of the frozen positive expectation rather than silently changing the label. Supported corrections, different subjects and paraphrases remain challenging; unknown clauses fail closed. Final source bindings for l11/r06 and repaired p01 are preserved, while n02 still withholds rather than retaining its damaged links. Ten total eligible records include these eight generated answers, one historical wrapper and one constructed probe; builder review finds no unsupported final output, pending independent source review.

No additional task was queued: existing224-source-plan-generation is the precise independent next step for avoidable W and supported prose rejected by finite grammar. Repeating223 or its old inference would add no new evidence. Production model/admission, services, orchestration state and main remain unchanged. Selected4B Android admission/load/cancel/reload and combined resources, actual mobile verifier integration, candidate release identity, physical Android/GrapheneOS and human acceptance remain open.

The original implementation report below preserves the actual generation protocol, freeze, post-output safety correction, resource measurements and limitations unchanged.

---

# Source-first fact frames: bounded task 221 repair 2

This is a public development experiment and builder assessment, not independent acceptance. Both required commands passed: `bash tools/android-build.sh` and `bash tools/evaluation/check_obligation_binding.sh`. The latter reruns shared Java behavior and all 143 saved records, validates actual model/run/source/APK identities, rejects missing or changed model/run artifacts, and applies separately recorded builder source judgments. It does not independently prove those judgments.

Final builder review records **5/40** fully supported, complete, useful old screen-eligible answers, **zero unsupported eligible answers** across all populations, and all **8 old + 1 previous-new + 2 new absent controls withheld**. Only **1/20** newly generated answers is useful and eligible. This clears the narrowly specified development threshold while leaving the useful-answer product gap substantially open. Nothing was deployed, pushed, promoted to main or submitted for acceptance.

## Recovery, freeze and preserved failures

Recovered the preserved failed checkpoint `2623197415ccdd0cee8bb139500f1e7a48e2c75a` onto the existing checkpoint branch. Original task 220, task 221 and repair 1 evidence remains byte-for-byte sealed. No old generation, same-model audit or independent classifier inference was repeated. The previous self-audit experiment admitted unsupported chronology and input/output transfer; the independent classifier still admitted these despite scores above its fixed threshold.

Commit `52ee3bf` froze twenty new public questions and twenty explicitly constructed semantic probes before parser implementation and new generation. Fixture SHA256: `cba43463f2862c9bf7f89f2a631351b818dbe2a2dd1d3692f3b312614752b75e`; execution protocol SHA256: `599930ed1ed045b8a03e2724361d06d4f10d74f7721fef4a5c98724a47cc1cdb`. Topics include computing, horticulture, civics, geography/history, biology and astronomy. Source bytes and expectations did not change. Constructed probes are neither factual corpus nor generated successes.

The declaration is in [protocol.json](../../tools/evaluation/fact-frames/protocol.json). Implementation fixes before viewing new prose addressed compilation, standalone definition segmentation, unanchored source pronouns and unsafe generic process-name stemming. Exact failure records remain in [early failures](fact-frames/early-failures.txt) and [normalization failure](fact-frames/normalization-failed.log). Missing `/usr/bin/time` stopped the first replay launcher; [that failure](fact-frames/time-tool-failed.log) is retained. Replay measurement now uses per-child `os.wait4` resource usage.

A post-output source review found an additional real rendering defect: constructed t10 contained correct Athens prose but its source-derived wrapper topic was Barcelona. The [first complete replay](fact-frames/replay-before-subject-fix/results/linked.json) is preserved. A generic geography-subject agreement rule now withholds such a mismatch, with a renamed-city regression. This is explicitly a post-freeze safety correction, not an untouched prospective evaluation. No fixture, generated prose, prompt, seed, source or scoring expectation changed; only deterministic replay and the Android build were repeated. The positive constructed probe remains withheld rather than being silently repaired or counted as a success.

## Material architecture and its limits

`FactFrames.java` parses complete generated factual clauses into typed relations and arguments, extracts matching grounds from exact source sentences, and derives citation bindings from those grounds. Both subject and material role/condition/time must match. It distinguishes decomposition output from input, continued capital status from a beginning event, written single-or-set documents from comprehensive codification, and usual strict temperature bounds from universal or exact conditions. Formula checking reads the TeX root degree and radicand and computes displayed rounding; matching a decimal alone cannot approve a wrong root. Article footnotes and formula brackets never become citation IDs.

Source anaphora requires explicit article/definition antecedents and attaches those spans. Unknown clauses or unproved tails withhold the whole answer. Complete generated prose is retained; the parser does not replace it with quotes or an extractive answer. Rebinding corrects wrong-neighbor references only when the entire recognized relation has an actual ground. The shared renderer exposes question and subject context and produces typed edition/document/passage/UTF-16 sentence references and click ranges.

This is a **finite, corpus-informed controlled-English adapter**, not a general entailment solution. Matching parsed arguments is useful only for the implemented semantics. Many correct syntactic variants remain unknown. No case IDs, entity allowlists, review labels or positive NLI/self-audit decisions grant eligibility. Some narrow aliases and relation patterns were developed from old public failures; the measurements are development regressions, not held-out generalization. Automatic question coverage beyond the existing obligation structure remains limited, and every eligible answer still needs independent source review.

Bounds remain six passages, the existing 1200-character sentence window, eight claims and eight references per claim. Shared cancellation checks run before and within parsing/proof stages. The required check passes 39 frame and 29 existing binding/renderer behavioral tests, including renamed subjects, role/time/condition reversal, unknown tails, decimal/root consistency, namespace collision, corruption, cancellation/retry and typed citation ranges. Experimental code compiles for Android but is **not wired into production answer generation**.

## Actual inference, identities and resources

Only the twenty new questions received real local generation, once each, on LLMRig CPU using six native threads, 4096 context and a maximum 320 draft tokens within the unchanged 512-total-token ceiling. There is no autoregressive self-audit; 192 remaining tokens are unused. The actual call is greedy `generateChat`; the native identity string also describes a separate Qwen3 claims sampler that this harness does not invoke. No GPU, network inference, emulator process, model preference or service was changed.

- Host candidate: Qwen3 4B Q4_K_M, 2,497,280,256 bytes, SHA256 `7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5`.
- Native library SHA256 `38cc3d9108c865fac5c7b8744987b58bee5a3ff9b37529f919e5ce24db42dfef`; llama.cpp `bb4caa7540188872173c44d161602d9271386413`.
- Reviewed edition SHA256 `b8d18801b099402205938979ab2bb44ee9a316f06f030aab789cf93ba3605012`; SQLite SHA256 `9009b19de43f851a815d1797779a94ab47077cc2fc5b3dfe70fc4bdf9a097386`. Verification compares text, title, source URL, date, rights, passage and document hashes against the actual read-only index.
- Production remains Qwen2.5 0.5B SHA256 `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`. `model.env`, native runtime and Android admission are unchanged.
- Actual final APK identity and size are in [build.json](fact-frames/build.json); earlier APK and build logs remain separate. This APK is a compile artifact, not selected-model Android execution or a release-qualified installation.

Twenty requests took 904.227 seconds of host wall time including one 1176.417 ms model load and harness overhead; 1484 draft tokens were generated, maximum prompt 2517 tokens. Nearest-rank p50/p95 uses `sorted[ceil(n*p)-1]`, n=20: first-token 32,673.820/53,870.810 ms; total generation call 40,061.604/65,365.064 ms. First-token includes prompt evaluation and first decoding, not model load. These heterogeneous new questions are not a matched speed comparison with earlier matrices.

Sampled host RSS/HWM peaked at 4,893,708 KiB; sampled swap was 0 KiB. Native tracked peaks were weights 4,242,363,904 bytes, KV 603,979,776 bytes and compute 80,413,184 bytes. Each request released its contexts and final close released the model. Parser replay of 143 records took 0.664 seconds with child maximum RSS 238,724 KiB under `-Xmx256m`; compilation is excluded. No PSS measurement was taken in this experiment. None of these numbers is phone RAM, thermal behavior, OS-OOM safety or selected-model Android admission evidence.

## Source review and useful-answer failures

[review.json](fact-frames/review.json) is explicitly builder assessment, bound to exact replay hashes. Every eligible claim was compared with its final attached source spans; all twenty new raw drafts also have individual assessments. Old withheld raw claims retain their prior reviews; a withheld route is not a new support judgment. [Independent review inputs](fact-frames/independent-review-inputs.json) identify raw records, exact sources, obligations and final outputs without supplying builder labels as ground truth.

| Population | Eligible | Fully useful generated answers | Interpretation |
| --- | ---: | ---: | --- |
| Old 48: 40 supported, 8 absent | 5 | 5/40 | s16, s19, s31, s40, s46; all eight absent withheld |
| Previous new 12 | 1 | 1 | n10 correct fifth-root explanation; one absent withheld |
| Repair 1 new 16 | 1 | 1 | l11 correct root binding |
| Historical 11 | 1 | Not fresh generation | r06 products and temperature rebound to correct sentences |
| Prior constructed 16 | 1 | Not generation | p01 vermicast now references actual end-product definition |
| New real 20 | 1 | 1/20 | f10 Athens capital/largest-city relation; two absent withheld |
| New constructed 20 | 0 | Not generation | Includes conflicting t10 subject metadata |

The 10 eligible records contain no unsupported publication under builder review. The comparison against the required measured baseline is 4/40 to5/40; against the failed independent-classifier experiment it is8/40 to5/40, trading coverage for safety. Original self-audit12/40 and its unsupported publications remain historical failures. Do not present any of these as production app quality.

Important remaining failures: f06 still confuses written and codified definitions; f11 invents uninterrupted capital status through the1970s; f12 transfers economic prominence to capital chronology. They are withheld. f02 and f14 issue W despite explicit source answers. Correct potential in f04, f07, f13, f15, f17 and f18 is also withheld because the grammar does not recognize it. f03 overproduces and loses a selection qualifier; f19 drops the some-amateurs quantifier. No correct-looking draft or fallback was credited as eligible success. The finite parser therefore repairs this bounded safety failure but does not solve useful open-domain explanation.

## Next concrete work and open gates

The queued source-first task223 strategy was executed here; its eventual handling should reuse this immutable experiment rather than regenerate it. The separate follow-up specification in [proposed-follow-up.json](fact-frames/proposed-follow-up.json) targets source-grounded obligation planning before prose generation, prompted by avoidable W, malformed fields and correct paraphrases blocked by the adapter. It requires new frozen questions and no more hand-added variants against this matrix. No runner state or dispatch was changed.

Selected-model Android admission/load/cancel/reload, combined index/native memory, integrated model/controller quality and new release identities remain separate gates. They require an approved sufficiently provisioned emulator/device for selected-model execution. Independent source review is pending. Clean-machine reproduction, signing ownership, physical Android/GrapheneOS and human acceptance remain open.
