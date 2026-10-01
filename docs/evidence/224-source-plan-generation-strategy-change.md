# Task 224 strategy change: obligation coverage before prose

Status: protocol declared before implementation and new inference; unvalidated.

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
