# General grounded generation — bounded host experiment, product gate fails

Task500 does not yet satisfy its product objective. A general full-paragraph context and draft path replaces finite relation templates in the new experiment, without changing the deployed model or claiming an unverified draft is supported. The required quality checker deliberately remains failing while general semantic verification, selected-model Android execution and current complete distribution measurements are missing.

## Frozen design and historical failures

Task220 already measured Qwen3 4B Q4_K_M (26/40 useful drafts, only4/40 useful controller candidates), Qwen2.5 7B and a sparse Qwen1.5 MoE. Its low-bit MoE produced0/40 useful drafts. Those old trials are preserved, not rerun or represented as new questions. The task224 report at9238f8e preserves extraction, dependency-parser and formula-only failures ending in0/24 useful explanations. Task222's independent classifier falsely approved role and chronology transfers. Neither finite source frames nor classifier labels are reused as general entailment proof.

Twelve existing reviewed source documents across six subject pairs were frozen before twelve new public development requests. Exact source bytes, original revision URLs, attribution and pack SHA are in tools/evaluation/general-generation/sources.json. The source pack remains61a5d472c8dd5445893f0d10565332d2dfea4e0e35557f6bd8c397dda5e8a135. No new source rights, bulk clearance or unseen evaluation is claimed. Explanations, comparisons, negated false premises and two unavailable personal/live requests are in protocol.json; they are public development only.

The material change is complete source paragraphs with ordinary multi-sentence prose, local typed S labels distinct from article footnotes, and explicit GAPS. No fixed claim count,220-character ending, handcrafted facts, topic routing, self-audit, NLI approval or paraphrase allowlist is used. Citation syntax only locates a paragraph. Drafts remain withheld pending independent entailment AND completeness review, which cannot be replaced by the generator's GAPS:none statement.

GeneralGroundedAnswer also implements bounded reciprocal-rank fusion over full questions, subquestions and overlapping content-word windows, at most eight complete paragraphs and two per source URL/date. Native token counting removes whole lowest-priority paragraphs until context plus512 generation tokens fits4096; it never cuts a qualifier mid-paragraph. The model screen supplies the frozen pair directly (oracle evidence), so its output quality does not measure end-to-end retrieval. A separate real Java retrieval test retains mulch and rotation but also retrieves ventilation, pickling, absolute value and compiler distractors. This is a preserved relevance failure, not a support win.

## Models, runtime and limits

The existing4B SHA7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5 and7B SHA65b8fcd92af6b4fefa935c625d1ac27ea29dcb6ee14589c55a8f115ceaaa1423 are reused. Immutable revisions/full Apache2 licenses remain in tools/evaluation/model-capability and scale-model-quality, with existing THIRD_PARTY_NOTICES. No competitor code is copied: the pinned competitor audit records Apache/MIT implementation notices separately from source/model rights and supplies no blanket corpus clearance.

Pinned llama.cpp bb4caa7540188872173c44d161602d9271386413 runs through the existing host JNI library, whose exact hash is in each manifest. Greedy decoding, six CPU threads,4096 context and512 output tokens are fixed; one process at a time. Each process has a hard12,000,000,000-byte virtual-address limit,256MiB Java heap, CPU time limit and sampled11GB RSS stop, plus12GB host available-memory preflight. This is host feasibility, not12GB phone acceptance. Model mmaps/repacked buffers, JVM and context are included in sampled process RSS; peaks can be missed by one-second sampling.

The current authorized API37 emulator has4,007,040KiB total and2,244,428KiB available memory in the task preflight. The4B artifact is2,497,280,256bytes before KV/compute/JVM/app memory, and prior measured native weight repacking alone was4,242,363,904bytes. No unsafe selected-model load is attempted on this4GB environment. Existing Android admission remains2GiB file/2048context/256output and the production catalog/selection is unchanged. No0.5B run is substituted for selected-model qualification. Real selected-model JNI/UI cancellation and restart remain unproven.

## Storage and remaining gates

storage-plan.json reconciles the two weight choices against the historical full303 allocation and update/provider allowance, not a new full installation. Replacing its baseline gives43.634GB for4B and45.820GB for7B before subsequent candidate changes. Historical update allowances become46.802GB and48.988GB respectively; staging another model copy can approach49.479GB for7B before unknown later overhead. Target45GB and hard50GB remain unchanged, and no coverage is silently dropped. Current full installed inventory/provider/update peaks require measurement; modern5564 is only a subset.

The new shared controller is an experimental host path and is not wired into production answer publication. Safe withholding therefore yields zero newly qualified generated product answers, not100% support precision or success. The Android build passes (APK65e91629f4af8238b5c9885023843412fe6adaf12c30972b857c8561eac6effa); this new APK is not installed for selected-model qualification. The installed API37 APK remains task490 f14099efbb96f945b739fc88da7f1ecfba34a61f5d1a270faf052d3440d8035d. Device probes are read-only: boot is unchanged, and both selection-file reads return the same missing-file error, not a successful selection receipt. Full raw transport exits are retained. Run outputs, independent source inspection and final check status are bound below. Source briefs remain explicitly extractive. Physical ARM64/GrapheneOS, model admission in a sufficiently provisioned Android environment, general semantic verification, relevance/completeness, rights, independent unseen comparison and human acceptance remain open.


## Completed execution and measured performance

Both serial native processes completed all twelve requests with exit0, one draft per question. All24 drafts, exact prompts, incremental text, model/runtime logs, native counters, timing and one-second process samples are copied into general-generation/run-20261002T134119Z; ignored weights remain at their recorded paths. GGUF loader logs confirm qwen3/qwen2 architecture and Q4_K Medium, mmap plus CPU repacking. There were no seed/prompt retries, new downloads, concurrent inference, service changes or device generation.

| Host candidate | Load seconds | First token median/p95 seconds | Total median/p95 seconds | Sampled RSS peak bytes | Sampled swap peak |
| --- | ---: | ---: | ---: | ---: | ---: |
| Qwen3 4B | 1.117 | 9.526 / 14.069 | 20.653 / 44.717 | 4,940,734,464 | 0 |
| Qwen2.5 7B | 2.607 | 15.749 / 20.150 | 30.274 / 46.259 | 7,983,595,520 | 0 |

These percentiles use nearest rank for12different requests, not repeated cold trials. Model load is separate; first-token and total include fresh-context prefill and token capture; reading/hashing weights warms host caches. Both are host CPU results.4B prompt maximum936 tokens,7B932; generation maxima360/227, within4096/512. Native weight/KV/compute peaks were4,242,363,904/603,979,776/80,413,184bytes and7,798,468,608/234,881,024/81,527,296bytes. Native counters are not whole-process memory. The current4GB emulator cannot establish either profile's Android feasibility.

The required Android build passes. check_general_generation.sh verifies model/runtime/input/output hashes, all24 actual records, token budgets and compiled retrieval/cancellation behaviors; missing output, changed output, changed model identity and missing model mutations fail. It then exits1 honestly for missing general runtime entailment qualification, selected-model Android JNI/UI execution and current full-distribution measurements. This is a negative product result, not a docs-only pass or a claim that general generation is delivered.

## Remaining concrete work

Preserve these exact drafts for source-support regression rather than regenerating the same questions. A separately pinned stronger independent verifier must be qualified against full compound claims, subject/condition transfers and wrong-neighbor citations before any automated publication; neither the generator nor the already failed NLI/finite-frame mechanism is an approval authority. That is an unresolved engineering step, not proven solved by this experiment. End-to-end retrieval must also reduce the observed generic-window distractors without losing the required paragraphs. Selected-model JNI/load/cancel/restart requires an approved Android environment with measured memory headroom for the selected profile; no baseline playback can substitute. Reconcile current full distribution plus model/shard update reservations before selecting a mobile deployment. No task queue or orchestration state was changed.


## Independent development source review and selection

The supplementary independent source reviewer inspected all24 full drafts against their actual provided paragraphs, including all factual clauses, qualifiers, citation targets and requested coverage. Its exact hashes and case judgments are in general-generation/support-review.json. This is separate from builder assessment and is not the canonical final grade or unseen evaluation.

| Candidate | Fully supported, correctly cited, complete educational drafts /10 | Correct unavailable responses /2 | Newly qualified product publications |
| --- | ---: | ---: | ---: |
| Qwen3 4B | 4 | 2 | 0 |
| Qwen2.5 7B | 5 | 2 | 0 |

4B g05 says assembly is always one statement per instruction, contradicting its source and later prose; g06 loses the bootstrap compiler's often-temporary qualifier; g08 adds an unsupported complex-plane explanation. Both models add unsupported shared soil-health benefits in g03.7B g05 cites the assembly paragraph for cross-compilation, g07 overstates unrestricted monarch power, and g09 omits the pressure mechanism.4B g01 loses a sufficient-moisture condition and strengthens inhibition to prevention. All failures are retained, not repaired by deleting tails or assigning a favorable quote. Correct abstention is not credited as generated educational usefulness. The generator's GAPS:none is not treated as a verifier finding.

**Selection result: no candidate qualifies for general product publication.** The7B's one additional successful draft on ten public oracle questions is insufficient to establish a reliable model preference, and its memory/storage costs are larger. Keep production selection unchanged. The4B remains an experimental asset, not a newly deployed baseline. New implementation and real model execution are checkpointed, but task500's full product objective remains unmet and the required general-generation check exits1. Canonical criticism must evaluate the immutable packet; this report does not award acceptance.
