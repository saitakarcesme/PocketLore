# Reference coverage expansion — in progress, not accepted

Task 480 preserves accepted task 470 at `a0cba18` as an immutable historical seven-document candidate. This edition is separate; no unseen or historical holdout inputs are used. No task-480 device access has occurred: the required exclusive emulator-5564 lease is pending.

## Frozen source selection

`tools/packs/reference-expansion/selection.json` selects 140 distinct existing Wikipedia article identities across 20 subject families before writing new public development questions. Its SHA-256 is `21dab3107d7267b7a4ec79eeba32d7677cff087ecc5a354746a65779086bc29a`. Exact prior HTML/revision bytes are reused without redownloading. Selection is neither a rights disposition nor installed coverage. At least 100 admitted distinct documents and 20 meaningful families remain required.

The approach retains complete bounded paragraphs, original HTML, revision and contributor links, publisher license/terms, acquisition records and an explicit transformation ledger. It excludes unresolved third-party quotations and warned content. Independent per-source review must precede admission. New source briefs remain labeled exact excerpts, never generated-answer successes. No model selection changes are planned.

## Implementation and verification plan

Add shared offline license records and source-text span binding to the existing pack format, preserving old pack compatibility and admission limits. A full license repeated per document would exceed the current 2 MiB manifest bound at this size; shared license references avoid that duplication. Verify complete paragraph mappings, UTF-16 boundaries, unique document identities and rollback on corrupt or missing source/rights metadata. Integrate through the existing catalog, not topic-specific runtime rules.

Freeze public development questions after source selection and before retrieval changes. Exercise general retrieval, mixed-topic/multipart requests, false premises and absent/private/current information. Source-level builder assessments and independent inspection are distinct from unseen generalization.

The new candidate must bind build inputs, APKs, installed state, corpus, settings, model selection and device receipts under a new freeze ID. Original task-460/470 evidence must remain unchanged. Storage sampling must distinguish the new subset from historical full inventories and include staging/rollback/provider copies where observable.

## Open gates

Source dispositions, admitted counts, implementation, development tests, required checks, independent criticism and new candidate/device evidence are not yet complete. Exclusive modern5564 ownership is required before device work. Physical Android/GrapheneOS, full-capacity modern Android, TalkBack, generated quality, broad rights clearance, independent unseen/matched comparison and human acceptance remain open. No competitive claim follows from this task.

## First implementation checkpoint

The schema-2 importer now carries complete selected source text, shared offline licenses, rights-review and source-packet identities, and contiguous exact paragraph bindings. It rejects missing identities, duplicate source identities, source-text hash mismatch, missing/changed licenses, unadmitted rights, fractional offsets, shifted paragraphs, trailing unbound text and split Unicode surrogate ranges. Existing schema-1 packs remain readable; this is integrity validation, not cryptographic proof of publisher authenticity.

The initial Android build passed on LLMRig (`downloads/reference-expansion/build-initial.log`), producing APK SHA-256 `993f5932b80c8d77820252353c14517b04b5ab7d52d1037c73b06dc1177b6d9a`. This is compilation only, not device validation. Gradle is configured for two workers and a 2 GiB heap; no total-process memory claim is made.

The original extraction packet is frozen at SHA-256 `abbb800f0c837f401cb9c9d0f3ccf836e191c9f06d797917ef7678833ee392bc` in `downloads/reference-expansion/source-packet.json`. It contains 140 candidates and 1,095 candidate paragraphs, not admitted coverage. Independent source review is explicitly narrower: inspect first-paragraph admission plus source-wide rights/context; later paragraphs remain excluded. Discovered missing attribution notices, formula/list lead-ins and misplaced topic content must remain recorded, not promoted by hash matching.

The new public development protocol contains 53 questions across the selected families, paraphrases, four multipart requests, six unavailable-evidence controls and three misleading premises. `tools/evaluation/reference-expansion/development.json` SHA-256: `7ffc25a4adfcd04a19ec09dd37e23efa0c2c42ede53115986771aeb06d76d20d`. Questions were frozen after source selection and before retrieval changes or execution. Excluding an expected source records a miss, not permission to rewrite the expectation. These builder-visible cases establish no unseen generalization.
