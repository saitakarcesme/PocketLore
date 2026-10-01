# Task 224 repair 2: one supported mathematical candidate, zero useful explanations

The [compositional formula replay](equation-plan/README.md) preserves the frozen 24 questions and all original generation. Android build passes; historical checks, 16 new behavioral controls, artifact mutation checks and exact Java replay pass. The required quality check still **exits 1**: the sole supported candidate restates the formula but does not explain why, so there are **zero complete useful answers**. All four absent controls remain withheld. This narrow proof improvement is not a repaired useful-answer architecture or product acceptance. Builder source assessments remain separate from independent review.

The previous failed reports follow unchanged.

---

# Task 224 repair 1: source retention improved; usefulness still fails

The [repair experiment](source-plan-parser-repair.md) recovers the failed checkpoint and adds a bounded complete-sentence source adapter plus an independently trained dependency-parser prototype. Build and113 behavioral/parser controls pass. The required quality check still **fails**: zero structural candidates across127 preserved records and0/24 useful new-case answers. No4B or NLI inference was repeated; no support gate or case-specific phrase rule was added. Independent source review and mobile qualification remain open.

The broader source adapter now retains14–24 admitted sentences per new case, including answerable material previously omitted by finite frames. Whole syntactic structure matching still fails to recognize supported prose, so it is not promoted as an answer architecture. Historical raw failures, parser setup failure, licenses, pins and resources are preserved. The original negative report follows unchanged.

---

# Source-grounded plan before prose: negative task 224 result

The fixed experiment produced **zero complete useful eligible answers out of24 new public questions**. All four absent controls withheld; no unsupported answer was published because no answer was published. Positive-output precision is undefined, not100%. `bash tools/android-build.sh` passes. `bash tools/evaluation/check_source_plan_generation.sh` passes artifact checks,85 behavioral tests and exact saved-output replay, then **exits1 at the quality gate** because usefulness is zero. No product acceptance, deployment or model suitability is claimed.

## Freeze and one declared architecture

The24-question set was frozen in `9580629` before implementation or generation. [Fixtures](../../tools/evaluation/source-plan/fixtures.json) cover computing, horticulture, civics, geography/history, food biology and astronomy, with multi-part explanations/comparisons, qualifiers and four absent controls. Real licensed source excerpts, dates, rights, edition/document/passage hashes and expectations are copied exactly from reviewed earlier packs. Questions are new; excerpts and topics are reused public development material, not held-out generalization or additional corpus coverage.

[Protocol](../../tools/evaluation/source-plan/protocol.json) declares one source-grounded plan-before-prose design. The unchanged `FactFrames` extractor produces bounded subject/relation/argument/condition/formula grounds from exact source spans. The first4B call chooses fact IDs for each question obligation. The second4B call generates complete cited prose using only those selected grounds. Independent deterministic validation requires every full generated clause to be proved by grounds selected for its obligation. A model-selected plan is relevance, not entailment or complete obligation coverage; no same-model audit or NLI score grants publication.

The source extractor and claim parser are deliberately unchanged: this isolates planning without adding case-specific paraphrase rules. Unknown families or tails withhold the whole answer. Generated prose is never rewritten to a quote, canned answer or template. Limits are32 source grounds,8 selected per obligation,4 obligations,8 claims/references, and the existing6passage/1200-character sentence windows. Original source sentence labels remain separate from plan fact IDs; typed exact edition-aware references survive validation and rendering.

The code/prompt implementation was committed in `b48894f` before inference. The fixed host configuration is greedy `generateChat`, CPU6native threads,4096context per call,128 plan tokens plus320 prose tokens, at most448 of the permitted512total tokens per question. If no source grounds exist, no model call occurs; malformed or withheld planning prevents the prose call. Each permitted stage ran once. No prompt, seed, threshold, model, grammar or expected-label change followed output inspection. Old143 frame records and994 classifier pairs remain immutable replay evidence; no old generation or classifier inference was repeated.

## Actual run, outputs and failure boundaries

The run completed normally with20 plan calls and9 prose calls, totaling382 plan and1328 prose tokens. Maximum per-question generation was235 tokens. Four computing cases had no recognized source frames, so neither stage ran. All24 final records withheld.

| Final failure class | Cases | Meaning |
| --- | ---: | --- |
| No source frames |4|Three answerable computing questions and one absent personal-data question never reached the model. |
| Planner W |6|Three live-data controls and three answerable questions whose necessary facts were omitted by extraction. |
| Unknown plan fact |5|Nonexistent F IDs or sentence labels such as P4.1 mixed into the fact namespace; no prose call. |
| Unknown complete prose syntax |6|The unchanged parser rejects the generated full wording; some drafts contain supported potential. |
| Geography subject conflict |1|The compound geography draft also contains unsupported chronology and wrong source links. |
| Prose W |1|The selected plan lacks the requested1931/1970s timeline. |
| Malformed typed prose |1|Six-field/concatenated records also invent a temperature comparison. |

There are three materially different boundaries, all preserved rather than conflated with a weak model:

- **Extraction removes answerable evidence.** q01–q03 have explicit binary-search/tree material but no recognized frames. q07 smaller-cut/young-plant reasoning, q10 constitutional authority, q12 varying monarch powers and q15 Barcelona chronology exist in original passages but not in selected semantic grounds. W is often accurate about the reduced plan and still fails the original user question. Source-first planning with incomplete extraction cannot repair these avoidable answer blocks.
- **Planning fails namespace and relevance.** q06/q14 invent unavailable fact IDs; q19/q20/q22 mix P sentence labels with F fact IDs. q05 chooses unrelated pruning for a stock/scion question. These errors fail closed. Merely fixing the ID syntax would not supply missing facts or prove obligation coverage.
- **Prose remains unbound or unrecognized.** q13 repeats the old unsupported transfer from continued capital status to beginning after Aragon union and supplies wrong-neighbor Athens references. q17 invents that pasteurization temperatures are lower than fermentation temperatures, which its excerpts do not establish. q23 changes discovering transient astronomical events into monitoring them and misses the requested income explanation. Conversely q09's definition overlap, q18's industrial-products/heat contrast and q21's fifth-root statement contain source-supported potential but fail the finite prose grammar. None is counted as generated success.

The Barcelona and explicit-fact withholding goals were therefore **not repaired**. Source planning did not prevent the chronology error in q13 and did not provide sufficient evidence to answer q14/q15. The old failure matrix remains unchanged; new cases diagnose a boundary rather than form a matched before/after quality benchmark. The0/24 result must not be compared as a controlled improvement or regression against differently worded prior sets.

[Raw frames, stage prompts, plan/prose bytes and final records](source-plan/run/results), [receipt and runtime identity](source-plan/run/manifest.json), [builder raw-stage assessments](source-plan/review.json) and [independent review inputs](source-plan/independent-review-inputs.json) are preserved. Every new case has a stage-level source assessment; there are no eligible published claims to endorse. W is not itself proof of correct absence detection: q04 withheld before any semantic planning because extraction produced no facts. Earlier counterexamples remain replay-only regressions.

## Resource and artifact measurements

All work ran on LLMRig. Serial CPU host inference took335.099 seconds including one640.564ms load and harness overhead. Model hashing warmed the filesystem; this is not cold-phone load time. Plan calls: first-token p50/p95 6508.732/12974.399ms and total p50/p95 7784.475/14214.129ms, n20. Prose calls: first-token p50/p95 6127.534/9244.848ms and total p50/p95 16425.670/25795.988ms, n9. First-token includes prompt processing and first decoding; total covers the native generation call, excluding model load. Percentiles use nearest rank `sorted[ceil(n*p)-1]`, only stages that actually generated tokens. They do not establish an equivalent-work speedup over earlier longer-context cases.

Maximum actual prompt was1005 plan tokens and687 prose tokens. Sampled host RSS/kernel HWM peaked at4,922,904KiB, sampled swap0KiB. Native tracked weight/KV/compute peaks were4,242,363,904 /603,979,776 /80,413,184bytes. Every generation released contexts and final close released the model. These counters and host samples are not Android device RAM, co-resident index/verifier proof, thermal behavior or OS OOM safety. No PSS measurement was added.

- Qwen3 4B Q4_K_M host candidate SHA256: `7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5`;2,497,280,256byte file.
- Actual native library SHA256: `38cc3d9108c865fac5c7b8744987b58bee5a3ff9b37529f919e5ce24db42dfef`; pinned llama.cpp `bb4caa7540188872173c44d161602d9271386413`.
- Actual debug APK:11,953,961bytes; SHA256 `a6df1b49c9a41b37eeb3bec6fddb4f6e44a4392878eb3013595b65f73e092bdb`.
- Production remains Qwen2.5 0.5B; model.env, Android model/context admission and native runtime are unchanged. This shared prototype compiles but is not wired into production. No selected4B Android execution occurred.

No new model/data/license downloads or dependencies were introduced; existing attribution is retained. No services, orchestration state, private holdout/context, main, publication or global model preferences changed.

## Checks and exact remaining product step

The required [check output](source-plan/check.log) reports the prior frozen frame regression pass separately from the **new experiment's failure**. It verifies actual pinned model/library/source/build identities, original143-record replay, new stage budgets, exact final replay, cancellation, namespace/unknown-ID rejection and changed/missing model/run/plan artifacts. There are39 previous frame tests,29 previous linking tests and17 new planning tests. A perfect or well-formed plan cannot approve an unplanned relation or unsupported tail. [Build log](source-plan/android-build.log) passes; source review remains builder assessment pending canonical independent criticism.

The exact unresolved boundary is **lossy source extraction plus an incompatible free-prose validation interface**. A further attempt must address both before another generation matrix: measure retention of requested source relations/qualifiers and use a typed obligation/claim representation that the validator can actually understand, while keeping generated natural-language usefulness separately assessed. Grammar-constrained ID selection alone addresses only malformed plans and cannot justify a new usefulness claim. More prompt rewrites, extra semantic regex variants or repeated inference on these24 cases are not justified by this result. No duplicate follow-up task was queued or dispatched.

Selected4B Android admission/load/cancel/reload and combined native/index resources remain separate approved-environment gates. Independent source review, useful supported research, integrated candidate identity revalidation, clean-machine reproduction, signing ownership, physical Android/GrapheneOS and human acceptance remain open. The negative result has no hardware blocker; the implementation's source/representation boundary is the problem.
