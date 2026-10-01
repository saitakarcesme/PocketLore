# Task 224 strategy change: obligation coverage before prose

Status: the declared run completed; build and behavioral integrity pass, but unsafe generated candidates keep the quality gate failing. The original pre-inference declaration is preserved in [declared-protocol.md](obligation-ledger/declared-protocol.md).

## Why the previous approach stops here

The original finite fact extractor omitted answerable evidence and generated zero useful eligible answers. Whole-dependency equality then retained source sentences but rejected all 127 replay records. The mathematical compiler recovered one supported formula restatement, but still zero complete useful answers on 24 questions: it did not explain why a fifth root applies. These failures and checkpoint `9238f8e1c02832e4d1353e4c3166f1761f77e512` remain preserved. No more paraphrase productions, special entities, root-language variants or threshold searches will be added.

## Materially different experiment

Use an obligation-first evidence ledger, not a finite relation recognizer as the model's input bottleneck. Supply the complete bounded sentence catalog with stable typed IDs, exact source text and provenance. The model must first state the answer's required parts and choose the supporting sentences for each part. Each plan row contains an obligation number, sentence IDs and a short account of what those sentences establish. The prose stage sees only this plan and its selected source sentences. It must answer all planned parts, including causal or contrastive relations, and preserve qualifications. The plan's free-text account is explicitly untrusted and is never used as source evidence.

A structural controller checks bounded IDs, complete numbered coverage, context, token exhaustion, cancellation and exact provenance. It does **not** equate a well-formed plan, an NLI label, lexical overlap or a model's coverage declaration with semantic support. Complete generated prose goes into a review candidate, not automatic publication. Source review must assess both plan sufficiency and every final claim, including tails and conditions. No unsupported sentence is deleted and no generated answer is replaced with quotation or deterministic prose.

This separates three questions the failed design conflated: whether the model sees answerable evidence, whether it produces a useful supported explanation, and whether a general automatic validator can safely authorize it. The first two can be measured now. The third remains an explicit gate; builder review cannot authorize deployment. If this experiment finds useful prose but lacks independent semantic authorization, the required end-to-end check must continue to fail rather than redefine candidate quality as publication success.

## Fixed execution and discriminating checks

- Preserve the frozen 24 task-224 questions, exact source bytes, expectations, four absent controls and all earlier raw results. One new run is permitted solely for this materially different architecture; no retries or wording/seed search.
- Use the existing pinned Qwen3 4B Q4_K_M host candidate (`7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5`), unchanged greedy decoding, 4096-token host context and CPU six threads. At most 160 plan plus 352 prose tokens (512 total) per question. One serial process; no emulator, service or production model changes.
- Keep bounded sentence extraction and typed source rendering. Every obligation must have a unique row with one to eight existing IDs; missing, repeated or unknown IDs fail closed. W marks a proposed abstention, not proof that evidence is absent.
- Freeze constructed tests before implementation for omitted/duplicate obligations, unknown IDs, malformed rows, empty rationale, truncated output, cancellation, source namespaces, mutation of exact evidence, full-tail preservation and pending-review publication rejection. These are controller fixtures, not corpus facts or generated successes.
- Evaluate all 24 full outputs once against actual selected and available excerpts. Record plan sufficiency, source support, completeness, usefulness and route separately. Formula restatement must remain incomplete for q21; the previous false chronology and invented temperature claims remain negative evidence. All absent controls must remain unpublished.
- Build Android; replay exact saved stages through the shared Java controller; reject missing/changed run/model artifacts. Record raw stages, selected spans, full rendered candidate, timings, native identity and host memory. No host result is Android or phone evidence.

The acceptance script will expose candidate-quality results separately and preserve the outstanding automatic/independent authorization gate. This is an experiment in useful generation, not a claim that human or builder grading is a production offline verifier. Independent canonical review is still required; no orchestration action is taken.


## Fixed run and measured outcome

The declaration was committed in `ae707de`; the single architecture and harness in `0c28102` before inference. Run `run-20261001T150553Z` completed once on LLMRig. All 24 questions, source excerpts, model pins and expectations stayed fixed. No prompt, seed, threshold, source wording or generator retry was performed. The old 60-question matrix, same-model audit and independent classifier were not rerun.

| Outcome | Count |
| --- | ---: |
| Plan calls / prose calls | 24 / 15 |
| Structurally valid review candidates | 14 |
| Fully source-supported candidates under builder review | 7 |
| Complete supported useful candidates | 4 (q01, q09, q12, q19) |
| Unsupported candidates | 7 |
| Supported but incomplete or presentation-defective candidates | 3 (q07, q11, q21) |
| Absent controls correctly withheld | 4/4 |
| Truncated plans / malformed prose | 5 / 1 |
| Authorized publication | 0 |

This is **not** a change from zero to four approved product answers. The original strict validator and the new review-only route have different eligibility meanings. The new experiment demonstrates generated potential under explicit builder source inspection, while the product publication gate remains closed. There is no matched claim of held-out improvement, general factual precision or independent acceptance.

### Actual useful output and unsafe counterexamples

For q01 the real model generated:

> The prerequisite for applying binary search is that the array must be sorted first (P2.3). An empty final interval means that the target is not in the array (P1.3).

The typed citation links both exact edition-aware sentences; the source excerpts explicitly establish the prerequisite and empty-interval outcome. Source article attribution, immutable revision, rights, dates and hashes remain in the unchanged fixtures and run inputs. Redundant inline P tokens remain generated text, not extra navigable citations.

q09 preserves the distinction between a written single document or set and a single comprehensive codified document, including their overlap. q12 accurately describes differing constitutional powers with cited examples. q19 explains that surviving bacterial spores prevent a sterilization guarantee. These are builder-assessed complete useful candidates, not runtime semantic approvals. Borderline wording interpretations and presentation defects are recorded explicitly in the per-claim review rather than hidden by a scalar score.

Seven candidates retain unsupported facts. q05 adds water/nutrient transfer and a strong-foundation property; q10 adds an unsupported frequency/degree claim about discretion. q14 turns separate historical facts into a direct principality-to-autonomous transition in 1931. q17 repeats invented higher fermentation temperatures and nutritional assurances from its planning account, and loses the lactate conversion condition. q20 cites use/end-product neighbors rather than the actual lactate-production sentence and strengthens the input/output exclusion. q22 drops naked-eye and observing-condition qualifications in an extra visibility-limit tail. q23 turns an income/training description into a professional-field exclusion. No extra sentence is deleted or quietly corrected.

q21 still fails the central why obligation: its chosen example includes the five-magnitude, hundred-fold relationship, but both planning and prose merely restate that one magnitude uses the fifth root. Giving the model more relevant sentences does not guarantee it performs the explanatory connection. q07 emits literal schema placeholders; q11 loses a lawmaking object in its final clause. Their supported core content is not counted as a fully useful complete answer.

Full planning accounts, selected exact spans and their provenance are in [plans.json](obligation-ledger/plans.json). Every final candidate and failed stage is preserved under [run/results](obligation-ledger/run/results); [builder review](obligation-ledger/review.json) binds each assessment to the exact record hash and evaluates whole compound claims. Expected judgments, source inspection and independent criticism remain distinct. Review disagreements can change the builder score; they cannot enable publication.

## Checks, budgets and host resources

- `bash tools/android-build.sh`: **exit 0**. APK SHA-256 `f44d99b7ebffc7aa4f595b4d251907baac3926c243fcc9d0df2fbb7008a66b08`. Raw build log and byte count are sealed in the evidence directory.
- `bash tools/evaluation/check_source_plan_generation.sh`: **exit 1**, specifically at the candidate support gate after historical regression checks, 16 new ledger controls, exact replay, per-source offsets, typed links and changed/missing artifact checks pass. The diagnostic count named `eligible` means only review candidates in this experiment; the metrics explicitly record zero publication. This does not relax the old support gate.
- The shared Java controller preserves all prose, verifies that each citation belongs to its selected obligation, and refuses publication pending semantic authorization. The new 352-token admission is checked before invoking the historical shared syntax parser; it does not alter the production parser or Android token limits. The plan stage admits at most 160 tokens; total allowance remains 512.
- Actual generation totaled 2,504 plan plus 1,949 prose tokens; maximum per question was 398. Largest plan prompt was 2,479 tokens; largest prose prompt 1,056. Every stage plus its full allowance fitted the unchanged 4,096-token host context.
- Serial six-thread CPU run: **1,065.315 seconds** including model loading and all cases; cumulative plan time 798.998 seconds and prose time 264.967 seconds. First-token latency includes prompt prefill. Raw per-stage times and nearest-rank p50/p95 definitions are in [timing-summary.json](obligation-ledger/timing-summary.json). Broader source prompts cost time; no speed improvement is claimed.
- Sampled host maximum RSS **4,919,260 KiB**, maximum observed process swap **0 KiB**. Poll interval was one second; these are sampled Linux process measurements, not Android/phone peak or OOM-safety evidence. Native diagnostics retain the separate model/KV/compute counters. Every case released its context, and final native state was zero after model closure.
- Model SHA-256 remains `7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5`; native library SHA-256 `38cc3d9108c865fac5c7b8744987b58bee5a3ff9b37529f919e5ce24db42dfef`, llama.cpp `bb4caa7540188872173c44d161602d9271386413`. Runtime identity, exact prompt bytes, available memory and all receipts are sealed. No new downloaded asset or license was introduced.

## Consequence and next concrete boundary

The changed strategy reaches useful prose on several cases without finite paraphrase rules, but does not make generated explanations safe to publish. Its distinctive failure is contamination from an untrusted free-text planning account: q14 and q17 already contain the unsupported connection before prose. The next independent design should keep planner reasoning out of factual evidence and represent requested relations and required qualifiers as a separate coverage checklist linked to exact source spans. It must independently establish the cross-sentence connection and reject unsupported tails; merely saying an account is untrusted or scoring its lexical overlap is inadequate. A further run of these same questions with slightly revised wording is not justified by this result.

No external hardware issue explains this quality failure. Production remains the pinned 0.5B model; the 4B artifact is still a host candidate. The ledger is an experimental shared Java component, not wired into the Activity as an accepted answer path. No selected-model Android, physical/GrapheneOS, integrated release, signing, clean-machine or human acceptance gate is closed. No queue, orchestration state, service, main branch or global preference changed. This is a materially different but still negative development checkpoint.
