# Complete-claim output repair — task 200

2026-10-01, LLMRig. Builder implementation and measurements, **not independent acceptance**. The fixed 220-character claim cutoff and mandatory second comparison claim are removed. The original 24-case screen improves from **2/19 to 3/19 fully supported, complete, useful published answers**, but the eight new cases regress from **1/8 to 0/8** under the frozen expectations. Across all 27 answerable cases, the count therefore stays **3/27**. This is a bounded output-format repair with a negative overall usefulness result, not a research-quality success.

## Identity and frozen procedure

- Development fixtures: original [24 cases](../../tools/evaluation/model-capability/protocol.json), SHA-256 `d7c8e3d83c83fc3eee6ef767077b241a9fcbc8f3dbb0f0a2021e59f950975f9c`, and [eight new cases](../../tools/evaluation/complete-claims/protocol.json), frozen in `b11a314` before product changes in `5b9bafd`. New questions cover DNA transcription/regulation, recurring volcanoes and ash transport, conditional magnetic storms, Yosemite seasonal comparisons, emergency supplies and historical property rights. Exact licensed excerpts, dates, expectations and pack hashes are in the fixture; no synthetic factual corpus or holdout is used.
- Fixed **evaluation anchor**: Qwen3 1.7B Q8_0, 1,834,426,016 bytes, SHA-256 `061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a`, Qwen/Qwen3-1.7B-GGUF revision `90862c4b9d2787eaed51d12237eafdfe7c5f6077`, Apache-2.0. Existing model/license receipts remain in [task 190](supported-answer-capability.md). The model stays ignored under downloads.
- **Role correction:** the actual production/demo pin in `tools/answers/model.env` remains Qwen2.5 0.5B, SHA-256 `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`. The coordinator withdrew the earlier claim that Qwen3 was deployed. Task 200 explicitly specifies Qwen3 as its comparison anchor; neither the app model pin nor Android admission limit is changed. Historical task-190 raw measurements remain intact.
- Runtime: llama.cpp `bb4caa7540188872173c44d161602d9271386413`, CPU; context 2048, generation ceiling 256, KV f16, one sequence. Qwen3 non-thinking sampling remains temperature 0.7, top-k 20, top-p 0.8, presence penalty 1.5 over 256 tokens, seed 42. No seed search, repeated wording experiments, GPU setup or global preference/service change.
- Host: committed native-ISA configuration, six inference threads, one process. Android: x86_64 CPU emulator-5560, two inference threads and unchanged 2 GiB admission. ARM64 JNI also builds but is not executed on physical hardware. Host and emulator timing/output differences are not interpreted as a backend speed comparison.
- Before: reuse the exact preserved task-190 Qwen3 24-case run, plus one eight-case run against the old library, SHA-256 `2af1eb5011a3cf3fa58af7c074cc8b14126bf0d67efd2d65bdb804de1cfbe67f`. After: one 32-case run against the changed architecture. Both use the production controller/template for that version and identical evidence. Withheld questions also receive explicitly marked **diagnostic-only** JNI generations; these are never counted as published answers.

## Product change and limits

The native grammar permits one through four cited, period-terminated sentences under the global token budget. A comparison can finish in one sentence; the grammar no longer forces padding or truncates a body at 220 characters. Prompt instructions describe this output contract. Citation labels, evidence selection, absent-evidence gating, context budgeting, conflict disclosure checks, cross-subject and temporal-scope protections remain in place.

Publication adds a conservative surface-completeness check: reject empty/number-only claims, dangling endings, unrecognized predicates, non-Latin letter scripts, generated URLs, more than four claims and final words without a source-supported lexical form. This is **not a grammatical parser, English language detector or entailment proof**. In particular, Latin-script non-English prose and some syntactic fragments may pass; legitimate English verbs or paraphrases may be withheld. Periods still delimit sentences, so decimal/abbreviation handling is limited. Token-exhausted drafts are withheld rather than published as complete.

The final-word check rejects the old cut stems without inventing a factual dictionary, but it also rejects valid paraphrases ending in “production” and “resources” in new-02/new-06. These false positives are preserved and not tuned away after observing the matrix. All published drafts were separately inspected against their cited excerpts by the builder.

## Actual results and source review

| Frozen suite | Version | Generated / fallback / abstained | Fully supported, complete, useful published | Unsupported published, builder assessment | Absent withheld |
| --- | --- | --- | --- | --- | --- |
| Original 24, 19 answerable | Before | 2 / 2 / 20 | 2/19 | 0 | 5/5 |
| Original 24, 19 answerable | After | 4 / 0 / 20 | 3/19 | 0 | 5/5 |
| New eight, all answerable | Before | 5 / 0 / 3 | 1/8 | 0 | Not applicable |
| New eight, all answerable | After | 3 / 2 / 3 | 0/8 | 0 | Not applicable |

These ratings follow the existing task-190 rubric, including its central-answer interpretation for headlamp and clothing questions. Full semantic completeness is distinct from a grammatically complete clause. Scores are builder judgments, not independent verdicts. Fallback and diagnostic text earn no generated-publication success.

- **Recovered cap-02:** “[science-magma-b214c1cb4647b3fc] Magma is molten rock that is underground, while lava is molten rock that breaks through the Earth's surface.” Both distinctions occur in that exact cited excerpt. The old compulsory second line added unsupported crustal-process claims; this run finishes after the supported single comparison.
- **Still useful cap-05/cap-17:** the host publishes the supported DNA packaging/fit explanation and hands-free headlamp reason. The newly published cap-01 is supported but incomplete: it omits stress overcoming friction, sudden slip and energy waves.
- **Format gains without publication gains:** cap-13 now has a complete body longer than 220 characters but omits several requested rights; cap-21 gives a complete comparison with Valley-only elevation gain. Both remain diagnostic-only because the unchanged coverage gate withholds them. They are not generated product successes.
- **Source-link failure retained:** cap-03 attributes upward movement/crust weakness to the storage/terrain excerpt, although those details belong to the other excerpt. cap-08 invents a cat chromosome count of 42 in its diagnostic draft. Both remain withheld. These failures demonstrate why sentence shape and citations cannot certify support.
- **New-case regression:** new-05 previously compared Hetch Hetchy/Wawona late-summer conditions correctly. After the change it publishes a true Hetch Hetchy spring/fall crowding fact with both labels, failing the requested seasonal comparison. The second source adds no support. New-01 still says only “two-step process,” without explaining either step. New-08 supplies four complete, supported diagnostic clauses but omits the frozen smallest-particle/global-distance detail and stays withheld.

Every before/after rating and reason is in [builder assessments](complete-claims/builder-assessments.json); [source-review inputs](complete-claims/source-review-inputs.json) retain exact questions, expectations, full sources, actual selected prompts, raw/resolved drafts and published routes. [Summary](complete-claims/summary.json), host [before](complete-claims/before/manifest.json)/[after](complete-claims/after/manifest.json) receipts, per-case raw records, partial drafts and stderr are preserved. Independent source review remains pending; this document does not impersonate it.

## Real Android JNI subset

The frozen subset ran once in isolated `files/complete-claims` on the existing emulator. Saved user model/pack files were not replaced, and no emulator/service was launched or restarted. App APK SHA-256: `9663b5ffd49b5d7a7b090f0b3363cb55ee1a22327b65abae6b314d1c74ddae1e`; test APK and device-side model hashes are recorded in the [receipt](complete-claims/emulator/manifest.json). Instrumentation completed with code -1. Model load: **1122.973 ms**.

| Case | Route | Tokens | First token ms | Generation total ms | Builder source assessment |
| --- | --- | --- | --- | --- | --- |
| cap-02 | GENERATED | 27 | 14778.110 | 18444.247 | Same supported complete magma/lava comparison as host; useful |
| cap-05 | FALLBACK | 64 | 14760.565 | 22592.690 | Four-clause draft includes “cell nuclei,” absent from the cited cell-packaging excerpt; draft withheld, not success |
| new-01 | GENERATED | 17 | 18530.892 | 20691.231 | Supported but incomplete two-step-process statement; not useful explanation |

[Raw JNI records](complete-claims/emulator/) retain different Android outputs rather than assuming CPU builds are token-identical. First-token time is generation call to first native callback; total time is generation call through completion. Load is measured separately, and controller time remains a distinct raw field. Host new-eight before execution took about 44 seconds and after-all32 about 178 seconds; these contain different case counts and do **not** establish a speedup. Per-case timings, prompt-token counts and runtime identities are preserved; no phone, thermal or battery claim follows.

## Checks, reproduction and preserved failures

Both required commands pass:

```sh
bash tools/android-build.sh
bash tools/evaluation/check_complete_claims.sh
```

The behavioral check compiles current production Java and executes nine malformed historical-draft regressions, all **11** task-190 source-reviewed unsupported drafts through the controller, all five absent questions with a generator that fails if called, positive complete-clause/noun-fragment/five-claim boundaries, and the prior temporal-scope regression. It also verifies all 64 before/after records, real model/pack/source hashes, native token/context bounds, three actual Android records, ratings/route accounting and missing/changed evidence rejection. It does not infer factual entailment from overlap or require inflated usefulness scores to pass.

For a new explicitly declared measurement run, use the installed toolchain and existing pinned ignored assets:

```sh
bash tools/runtime/build-host.sh
python3 tools/evaluation/complete-claims/run_host.py after
bash tools/android-build.sh assembleDebug assembleDebugAndroidTest \
  -I ../tools/evaluation/complete-claims/source.gradle \
  -PpocketloreTestRunner=org.pocketlore.app.CompleteClaimInstrumentation
python3 tools/evaluation/complete-claims/run_emulator.py
```

The emulator runner intentionally refuses to overwrite existing result files; archive a prior attempt before an authorized new attempt. It constructs inputs directly from the frozen public protocol; the measured subset uses identical inputs to the preserved host run. The `before` mode refuses a changed old-library hash; reproduce historical architecture from its recorded source checkpoint in a separate checkout, never silently rerun “before” using current code. `assemble_evidence.py` documents the exact collection and builder rating procedure; it is not a scoring oracle or part of the acceptance check.

The initial Android test compilation failed because the host harness used `Files.writeString`, unavailable in the Android compile API. Its [failed build log](complete-claims/android-build-failed-java-api.log) is preserved. An Android-compatible harness adapter uses byte writes/Paths and the same controller/JNI flow; no model, grammar or prompt was changed after the host screen. An early incomplete acceptance invocation also stopped on the not-yet-created verifier; its [log](complete-claims/check-in-progress-failed.log) remains. Successful final build/check logs are adjacent to this report.

## Remaining work

No overall useful-answer gain was measured across the expanded suite. The next bounded product investigation should address **coverage-aware context selection and multi-part completeness**, with explicit per-question obligations and sentence-to-source review: cap-10 drops reversal evidence, cap-06/18 omit a source, new-01 omits explanation steps, and new-05 answers another season. Replacing the final-word heuristic requires held-fixed regressions and source review, not merely relaxing it to increase publication. Model selection remains separate; this screen provides no basis to deploy Qwen3 or claim larger-model/phone suitability.

A new exact candidate release freeze, independent criticism, unseen evaluation by a separate authorized evaluator, physical Android/GrapheneOS resources and human acceptance remain open. No private holdout/context, orchestration/state, branch switch, push, main advancement or production key/publication action occurred.
