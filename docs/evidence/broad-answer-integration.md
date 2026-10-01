# Task 212: broad evidence in production-model answers

This task integrates the task-211 reviewed rendered edition into the actual deployed Qwen2.5 0.5B controller. It does not change the model, 2,048-token context, 256-token output budget or Android admission limits. The frozen [12 new cases](../../tools/evaluation/broad-answers/protocol.json) were committed as `2c1e23a` before product changes: eight supported explanation/comparison/multi-source/qualifier cases and four absent controls, with pinned source excerpts and expectations. The original 40 retrieval queries remain unchanged. No private holdout or service configuration was accessed.

## Changes and source admission

Shared ranking now prefers an exact normalized title over a longer title containing the same words. Disk queries prioritize introductory paragraphs and comparison-subject titles, score at most 64 candidates, and bound each SQL expression to 64 rows (at most four expressions). Selection takes distinct source documents before a second passage from the same document, with four returned hits. This is bounded diversity, not a guarantee that four hits contain every needed fact.

Combined retrieval rejects a query when its content vocabulary is missing across candidate evidence. That conservative lexical veto removes the old small-pack OR leakage for invented queries, but also rejects legitimate paraphrases; it is not entailment. The new acid/proton-donation case exposes that cost and remains withheld. Source subject and dates accompany each excerpt in the bounded context. Original source text, edition citations and rights are not rewritten.

Only the exact task-211 reviewed edition is enabled under the prior broad-generation warning. Its identity selects the source disposition review; a hash does not establish factual entailment. Unknown/old broad editions retain their generation veto. Existing citation integrity, budget, completeness, number and temporal-scope checks remain active. The sealed pack provenance still contains its historical “Generation disabled” statement from construction; application admission now supersedes that gate for this one reviewed edition. It is not independent distribution clearance.

The first real JNI run revealed a controller defect: a sentence naming both comparison subjects bypassed the cross-subject screen. The model published dry-heat descriptions for both baking and boiling, and for both cooking and baking. Both are unsupported transfers. [Full failed outputs and receipts](broad-answers/failed-shared-property/) and a separate [builder review](broad-answers/failed-shared-property/builder-review.json) preserve those failures. The repair withholds a shared-property claim when it distributes terms established only for one subject, unless one excerpt explicitly covers the joint statement. It is a narrow conservative screen, not semantic entailment verification. The actual two failed drafts are regression fixtures; a supported shared-heat control and the prior temporal-boundary regression also pass. No prompt rewrite or seed search was used to make the matrix pass.

## Retrieval results, separate from answers

The contemporaneous [before run](broad-answers/before/results.json) reproduces 24/32 expected-article hits. Acid was third behind Chemistry of ascorbic acid, Cooking was absent, the distance-from-zero query missed Absolute value, and the Absolute value title query returned four paragraphs from that single article. Four of the eight absent controls returned small-pack hits (six hits total).

After the changes, Acid and Cooking rank first; Absolute value appears in the distance-from-zero top four; the title query returns distinct documents. All eight original absent controls return zero combined hits. Expected-article recall remains **24/32**: q14 and q25 improve, while q02 and q20 regress. Persistent misses are q04, q18, q24, q27, q28 and q30. This is a tradeoff, not an aggregate recall improvement. The expanded/current Algae text no longer says “eukaryotic” in its lead, and strict vocabulary/candidate selection remains brittle. A retrieved article is not an answer or evidence of full claim support.

## Actual JNI, citations and review

The before run withheld all eight supported cases without invoking the model because broad generation was disabled. The first enabled run published five outputs; two were unsupported and therefore failed source review despite structural citations. The repaired run uses the same frozen questions, model, source assets and generation budget. The final [raw JNI run](broad-answers/after/results.json) contains **3 GENERATED, 2 FALLBACK and 7 ABSTAINED** routes. All four new absent cases have empty retrieval and no invocation. The [builder review](broad-answers/builder-review.json) finds all three published claims supported, but only **2/8 supported cases fully answered usefully** (cooking and algae). The mixed boiling/evaporation commonality is supported yet incomplete as a comparison. The two unsafe dry-heat drafts remain byte-for-byte in raw evidence and are now withheld. Acid is blocked before inference; Absolute value and the algae length qualifier receive model abstentions. No extractive fallback is counted as generated success.

| Case | Final route | Builder source/usefulness assessment |
|---|---|---|
| Heat in cooking | GENERATED | Supported, complete for the narrow question, useful; near-verbatim source definition. |
| Algae definition | GENERATED | Supported, complete for the narrow question, useful; short source-faithful definition. |
| Boiling versus evaporation | GENERATED | Supported shared property; omits differences and is not a fully useful comparison. |
| Baking versus boiling | FALLBACK | Unsupported shared dry-heat property withheld. |
| Cooking versus baking | FALLBACK | Unsupported generalization of dry heat withheld. |
| Acid/proton donation | ABSTAINED | Conservative retrieval veto blocks related evidence. |
| Absolute value explanation | ABSTAINED | Actual model declines despite retrieved material. |
| Algae length qualifier | ABSTAINED | Actual model declines. |
| Four absent controls | ABSTAINED | No evidence or model invocation. |

The final APK SHA-256 is `5a5c047f161c44782ca85f6e1883a06df513cec7294cacc303ccd324b1be900e`. The unchanged broad pack SHA-256 is `b8d18801b099402205938979ab2bb44ee9a316f06f030aab789cf93ba3605012`; model SHA-256 is `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`. Three active collections still expose 1,113 documents and 40,891 passages. [Receipts](broad-answers/after/receipt.json) bind current production code, APK, protocols and every raw record; the verifier also compares retrieved/selected bytes with the pinned SQLite/TSV assets.

Each publication is assessed against the exact selected excerpts, separately from whether the controller labels it GENERATED. Verbatim or near-verbatim text generated by JNI is labeled as such; it is not an extractive-fallback route, but also does not demonstrate synthesis skill. A supported commonality between boiling and evaporation does not by itself fully answer their comparison. Builder assessments are not independent criticism or human acceptance.

The harness drives the real Activity and production controller/JNI, records raw drafts even when withheld, opens every published citation span and checks its source text, URL, date, rights and edition provenance. It samples native resource state, PSS/RSS/swap and Java heap every 100 ms while the combined disk/small-pack catalog and model are resident. Sampling can miss short peaks and adds observer overhead. Model unload/reload and unchanged saved catalog/model are checked. All measurements are from emulator-5560, not a physical phone or GrapheneOS.

Four generated citation spans were opened and checked; both the [Wikipedia Boiling](broad-answers/after/mixed-water-citation-0.png) and [USGS Evaporation](broad-answers/after/mixed-water-citation-1.png) dialogs were visually inspected. The original task-211 archive/source notice is retained in provenance, rather than erased to hide history.

Model-ready Activity startup took 1,350.601 ms, reload 431.424 ms; filesystem caches were not flushed. Seven requests invoked JNI. Prompt sizes were 419–645 tokens, outputs 4–37 tokens, all within the unchanged 2,048/256 budgets. Controller first-token times were 22,125.57–34,178.36 ms and totals 22,609.88–38,408.46 ms, including token counting/prefill but excluding initial model load and separate retrieval. UI wall time additionally includes retrieval/dispatch; each case is recorded independently. These heterogeneous cases are not a cold/warm speed benchmark and do not establish usable phone latency.

Across 1,856 memory samples, maxima were PSS **691,605 KiB**, RSS **784,512 KiB**, swap **23,004 KiB**, Java used **47,017,760 bytes**. Native maxima were one model lease, one live context, **485,452,288 model-buffer bytes**, **25,165,824 KV bytes**, and **78,709,248 compute-buffer bytes**. Context count returns to zero after every request. These are sampled observations with the combined index active, not OS OOM/thermal guarantees or evidence for a different/larger model.

## Reproduction and limitations

```sh
# Runs actual serial Android JNI and preserves a new ignored raw directory.
python3 tools/evaluation/broad-answers/run.py repaired
# After reviewing and freezing that run's exact outputs/receipts:
bash tools/android-build.sh
bash tools/evaluation/check_broad_answers.sh
```

Both required checks pass: [Android build](broad-answers/build-final.log) and [behavioral check](broad-answers/check.log). The acceptance check compiles controller regressions and verifies immutable behavioral receipts against the current APK, production sources, model pin and source assets. It rejects changed or missing raw JNI evidence. It does not silently rerun or replace source judgments. Raw output review remains required for a newly generated matrix.

The failed comparison publications and test-build API failure remain preserved. No user asset was deleted: catalog bytes and model hash are checked before/after. Airplane mode is enabled and Wi-Fi/mobile data disabled; no research network or remote inference is used. Acquisition/model binaries remain ignored. The release candidate identity has changed, requiring task 213 revalidation; historical source and release evidence is not relabeled as matching this APK.

Remaining concrete work is coverage-aware paraphrase/candidate selection and complete useful comparisons with the deployed model, using these exact failures rather than minor repeated wording changes. The conservative vocabulary/shared-property screens can over-withhold. Broad-source fidelity does not solve model entailment or question completeness. Physical Android/GrapheneOS, independent source review, production signing ownership, clean-machine reproduction and human acceptance remain open.
