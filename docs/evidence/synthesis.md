# Synthesis development evidence — task 050

## Repair 050-synthesis-repair-1

Checkpoint `bb7eb8633239c953d1ae68ca3511203f579e4d1e` was rejected: its generated groundwater claim incorrectly attached slow movement to the period before saturation. The old automated PASS does not establish supported synthesis. Original `synthesis/final/` artifacts remain unchanged.

This repair restores the prior implementation on the current checkpoint branch and adds a conservative temporal-speed publication screen. A cited sentence must contain the speed, temporal boundary and endpoint terms together; separate sentences cannot jointly license the relation. This is a narrow lexical safeguard, not semantic entailment; it can withhold valid paraphrases and miss other unsupported relations.

The exact real-model rejected draft and actual source rows are frozen under `tools/evaluation/regressions/temporal-scope/`. Replay fails before the repair and passes after it; both logs are under `synthesis/repair-1/`. Corrected text and fictional speed/boundary/endpoint controls test code only and are not model-quality evidence. No corrected answer is substituted into the application.

The unchanged model, prompt, sampler and public cases were exercised again on 2026-10-01. Both named checks exit 0: `bash tools/android-build.sh` and `bash tools/evaluation/check_synthesis.sh`. The checker permits only a specifically verified safe withholding of this synthesis failure, explicitly reporting `synthesis_generated: false`; arbitrary fallback is not success. Citation and multiple-source check booleans are publication-policy checks (generated support structure OR specifically verified withholding), not a claim that fallback generated citations. Other generation cases remain required. Supported generated multi-source synthesis remains unaccepted.

### Actual repair run

Run: `downloads/synthesis/run-20261001T010029Z`, existing supervised `emulator-5560`, AOSP x86_64, CPU only. No physical Android or GrapheneOS measurement. [Raw outputs](synthesis/repair-1/results.json), [check summary](synthesis/repair-1/summary.json), [standalone build](synthesis/repair-1/build.log), [instrumentation build](synthesis/repair-1/instrumentation-build.log), and [environment](synthesis/repair-1/environment.txt) are preserved. The run-local ignored directory also retains both APKs.

Runtime: llama.cpp `bb4caa7540188872173c44d161602d9271386413`, 2,048-token context, two CPU threads; Qwen3 non-thinking claims use temperature 0.7, top-k 20, top-p 0.8, presence 1.5/256 and seed 42. Model `Qwen3-1.7B-Q8_0.gguf`, 1,834,426,016 bytes, SHA-256 `061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a`; model load **634.618 ms**. Pack and frozen question hashes remain those listed below. No model, prompt, source, seed or question was changed to obtain this repair result.

| Case | Visible route | Prompt / output tokens | First token ms | Total answer ms | Generated citation callbacks |
| --- | --- | --- | --- | --- | --- |
| Phase comparison | GENERATED | 440 / 42 | 20322.794 | 26106.955 | 4 |
| Heat explanation | GENERATED | 459 / 20 | 20189.820 | 22780.854 | 1 |
| Groundwater/runoff | FALLBACK | 597 / 79 | 26406.659 | 37242.042 | 0 |
| Conditional recharge | GENERATED | 399 / 74 | 17631.716 | 27079.051 | 2 |
| Absent evidence | ABSTAINED | 0 / 0 | 0 | 2.036 | 0 |
| Fictional conflict | FALLBACK | 287 / 9 | 13003.175 | 14204.996 | 0 |

All six raw drafts and prompts are byte-identical to the rejected checkpoint's final run, as recorded in [prior comparison](synthesis/repair-1/prior-comparison.json). The groundwater draft still says “moves slowly until it reaches saturated rock material.” That claim is unsupported by its cited excerpts; the source separately describes downward movement until saturation and slow movement within groundwater. The whole draft is withheld, with the stable temporal-scope reason. The displayed fallback contains original retrieved passages and explicitly says it is not a generated explanation or verified answer. Zero generated citation spans remain on that withheld draft.

Direct review of the three unchanged generated cases against their actual prompts finds the phase direction and inverse, evaporation's energy/heat relation, and conditional deep/shallow example in the supplied excerpts. The shallow claim retains **may**, substantial precipitation and coastal south Georgia. Joint citation sets still overcite; these observations are bounded builder source review, not independent acceptance. The seven generated citation callbacks resolve exact passage IDs; this does not test physical taps or a new model SAF import. Native overflow/cancellation and host routing/conflict controls pass. The exact rejected-draft regression retains both its pre-repair assertion failure and post-repair success; additional fictional controls reject mismatched speed, boundary and endpoint while allowing explicit support.

APK SHA-256: `a47d90ab6d31d387a0b93fc025cba3c7ac36a4da5590a0048af86d970785559f`. Test APK: `7c61415ec9c92844b5c68248610f277513edc1d0eada1571506b7b33d233fc92`. Raw report: `7b9fb76aef16f0e73b0859a08b1f2b84ca90800f809a6f26d0b49b9495e94fd7`. [Artifact identities](synthesis/repair-1/artifact-identities.json) include both built native ABIs; native libraries are unchanged from the rejected checkpoint. [Repair SHA256SUMS](synthesis/repair-1/SHA256SUMS) freezes these evidence files.

Limitations: this repairs the reported publication failure by withholding, not by obtaining a good synthesis answer. General source entailment, other temporal paraphrases and relationships, implicit conflict, usefulness, unseen evaluation, peak resources and physical-device acceptance remain open. The guard tests lexical co-occurrence within one sentence, not a semantic parse, and can both over-withhold and miss other scope errors. The earlier memory snapshot is historical, not a measurement of this repair run. No private holdout, orchestration, services, global preferences, branch switch or push was involved.

## Historical task 050 report (preserved context)

Historical pre-review status (superseded by repair below): both named checks PASS on 2026-10-01; bounded development behavior is validated on the LLMRig AOSP x86_64 emulator. Broader research-quality acceptance remains open. This is builder development evidence, not independent acceptance or physical Android/GrapheneOS evidence. Private holdout was not opened. No runner, service, global model preference or branch was changed by this task; no push was made.

## Artifacts and method

Questions and source review anchors were frozen in commit `2e47d39`, before synthesis tuning. `tools/evaluation/synthesis-cases.json` SHA-256 is `1eb30aa083e9f34be45b13ee09a67c7c7442d67a2ff81050b2d92b248450840e`. The five cases are phase comparison, evaporation explanation, groundwater/runoff synthesis, conditional recharge comparison and absent evidence. Four require actual generation. A separately labeled fictional sensor contradiction tests controls only; it is not factual corpus or a quality score case. No canned factual response is substituted for model output.

The real English pack contains 186 passages from 10 attributed documents; its SHA-256 is `567e9bbbaab896826809ec20f81ae1c4b3f421b011931edae0989d28cfce10ea`. Prompts include excerpts, dates and source URLs; raw reports retain retrieved passages as well as the actual selected prompt. The source dates may describe archived content and do not establish present conditions.

The runtime remains llama.cpp b10566 commit `bb4caa7540188872173c44d161602d9271386413`, CPU-only, two threads and a fresh context per request. Earlier trials use greedy sampling; the final Qwen3 claim sampler is specified below. Task 050 builds both ARM64 and x86_64; only x86_64 executes here. Context is 2,048 tokens, output reserve 256, batch 2,048 and microbatch 128. The native tokenizer counts the model's complete chat template. Native code independently rejects prompt plus output overflow.

The earlier optional candidate was upstream `Qwen/Qwen2.5-1.5B-Instruct-GGUF`, revision `91cad51170dc346986eccefdc2dd33a9da36ead9`, `qwen2.5-1.5b-instruct-q4_k_m.gguf`, 1,117,320,736 bytes, SHA-256 `6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e`. Its Apache-2.0 license and attribution are bundled; the explicit reproducible downloader and pin are under `tools/evaluation`. Weights stay ignored. The evaluator overrides only the model hash in a run-local copy of the frozen fixture. It uses `files/synthesis-tests/model.gguf`, preserving the app's original saved 0.5B model. The larger import bound is implemented but new-model SAF import/restart was not exercised in this task.

The initial 0.5B model SHA-256 was `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`. Changing the evaluation candidate does not change system/global model preferences.

## Preserved failures

- `synthesis/initial`: actual 0.5B outputs omitted citations and confused the direction of evaporation; the exact-term gate also blocked remove/removes. Overall FAIL.
- `synthesis/unconstrained-1.5b`: actual larger-model drafts still omitted citations, transferred cooling to evaporation and assigned aquifer recharge wells to runoff. Overall FAIL.
- `synthesis/constrained-first`: valid citation formatting did not establish support. The application published a cooling/evaporation error and a recharge-wells/runoff error; the conditions answer omitted the requested timing distinction. Overall FAIL. These are factual-support failures, not merely formatting failures.
- `synthesis/selected-context`: selecting one passage for each comparison aspect improved factual text. However, each phase-comparison sentence mixed sources while citing only one. The model abstained on the answerable deep/shallow case. Overall FAIL. The original cooling-transfer regex also falsely flagged a sentence whose second clause correctly described condensation; its later correction stops at the named condensation clause. The original failure summary remains untouched.

- `synthesis/combined-citations`: joint labels fixed the missing-half attribution pattern, but the lexical screen rejected generic second sentences in comparison and synthesis. Explanation generated; the answerable conditions case still abstained. Overall FAIL. The next candidate permits one or two claims instead of requiring an unnecessary second sentence and explicitly permits both claims to use one source.

- `synthesis/concise-claims`: one-sentence phase comparison and the explanation matched their cited excerpts. The groundwater/runoff draft transferred the destination "lakes" from the groundwater excerpt into the runoff clause; the coarse evaluator accepted that draft, but source review did not. Conditions still abstained. Overall FAIL. A specific destination-transfer regression was added, and the next prompt requests qualified qualitative comparisons when exact numbers are unavailable.

- `synthesis/qualified-prompt`: the qualitative-comparison instruction produced a deep-aquifer claim but omitted shallow aquifers. The model still transferred the destination "lakes" to runoff. Overall FAIL. The next candidate requests one comparison line per subject and adds a conservative cross-subject lexical leakage screen.

- `synthesis/clause-screen`: the revised draft avoided the destination transfer, but exact-word support rejected "infiltration" against "infiltrates". The conditions case again abstained. Overall FAIL. The next candidate retains the threshold, adds limited word-form normalization, and places a subject-by-subject comparison outline at the end of the prompt. The outline contains only question subjects, not factual answers.

- `synthesis/optional-comparison-stop`: after adding nominal word forms and a question-only subject outline, the model stopped after describing evaporation. Its partial output, APK hash, build and instrumentation interruption are preserved. The builder deliberately stopped this isolated test app after observing the incomplete comparison; remaining cases were not evaluated. The next native grammar requires two claims for comparisons, while retaining the explicit abstention branch.

- `synthesis/forced-pairs-qwen2.5`: the two-claim grammar produced both phase directions, but the model again transferred a destination into runoff and the application withheld that draft. The recharge comparison still omitted shallow aquifers. Overall FAIL. Rather than weakening checks, the next candidate changes the model family to Qwen3.

- `synthesis/qwen3-greedy`: the larger alternative generated a supported explanation and a more explicit groundwater/runoff draft, but left the reverse phase direction implicit and its conditional recharge paraphrase failed the lexical screen. Source review also flags that the groundwater sentence omitted the source's "may" before eventual discharge. Overall FAIL; this is not a fully supported synthesis result. The next candidate uses the publisher's non-thinking sampling recommendations, retaining all validation checks.

- `synthesis/qwen3-sampling`: fixed-seed upstream-style sampling restored explicit phase directions, but groundwater discharge still lost "may" and the conditions paraphrase was withheld. Overall FAIL. The final candidate simplifies the accumulated prompt and explicitly preserves modal uncertainty and example scope; sampling seed, model, source pack, lexical threshold and checks are unchanged.

- `synthesis/phase-check-false-negative`: all four required cases generated, absence abstained, and conflict withholding passed. The only automated failure required the condensation direction to be restated literally, despite the answer explicitly giving evaporation's direction and citing the source's inverse relation. The final evaluator accepts that equivalent only when the inverse phrase is also present in the actual supplied prompt; the failed summary is preserved. No generated output, question, source, model or seed was changed for this evaluator correction.

Early summaries sometimes counted passage IDs in fallback text as a citation check success; their overall results were still FAIL. The current evaluator requires GENERATED before checking generated citations and verifies exact case/model/pack identities. The combined-source grammar prevents the observed missing-half attribution pattern by requiring the supplied source set on each comparison claim. This may overcite; it is not semantic proof or fine-grained provenance.

## Implemented controls and limits

See [implementation and reproduction](../SYNTHESIS.md). Native constrained decoding supplies format and source-label choices, never answer facts. The model can abstain. Raw drafts remain intact while emitted short labels resolve to stable passage IDs. Final Android citation spans call the source inspection callback; the instrumentation invokes these actual spans and checks exact IDs. This is narrower than a physical tap and dialog usability test.

The lexical support threshold, exact-number screen and comparison leakage screen are conservative heuristics. For explicit two-source comparisons, the leakage screen recognizes named subjects in newline/while/whereas clauses and rejects words present only in the other subject's excerpt. It skips ambiguous clauses and can reject valid paraphrases; it is not a parser or entailment model. They can reject a supported paraphrase and accept a false relationship assembled from source words. Broad entailment, premise checking and conflict reconciliation are not solved. The conflict signal covers identical statements with opposite explicit negation; the fictional test model failed to disclose disagreement, so the application withheld its draft and displayed a potential-conflict warning with both source IDs. This safe fallback is not a generated synthesis success.

At most two sentences of 220 characters each sharply limit depth; grammar forbids internal periods, restricting decimals and abbreviations. Context selection can omit necessary evidence, and the absent-term gate still misses paraphrases. No general claim of useful research, unseen accuracy or competitive superiority follows from these development cases.

## Measurement definitions

`load_ms` measures native load of the already provisioned model. Per-case `first_token_ms` starts at entry to the answer controller and includes context selection, token preflight and prefill until the first token callback, often a citation label. `total_ms` includes final validation but excludes earlier pack indexing/model load. Token counts are native emitted tokens; prompt counts include the real chat template and system instructions. No first-useful-content, cold-cache, repeated p50/p95, peak RSS/PSS, thermal or battery measurement is claimed. The model is reused across cases, while each generation creates a fresh context. OS/file caches are uncontrolled.

The emulator reports 2,532,896 kB MemTotal and 1,899,668 kB SwapTotal in the final environment snapshot. These virtual-machine values do not establish physical phone memory suitability. No GPU inference job was run. Assets, model copies, swap, installation peaks and all caches have not been totaled for release acceptance.

## Alternative model candidate

The later candidate is [Qwen3-1.7B-GGUF](https://huggingface.co/Qwen/Qwen3-1.7B-GGUF), upstream Apache-2.0, pinned revision `90862c4b9d2787eaed51d12237eafdfe7c5f6077`, file `Qwen3-1.7B-Q8_0.gguf`, 1,834,426,016 bytes, verified SHA-256 `061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a`. The upstream license and attribution are separately bundled, preserving the earlier model notices. `tools/evaluation/synthesis-model.json` pins this candidate; `synthesis-model-qwen2.5.json` preserves the earlier pin. No conversion was performed.

The pinned llama.cpp legacy formatter emits plain ChatML. For the `qwen3` architecture only, the adapter validates the expected assistant suffix and template capability and appends the upstream non-thinking prefix `<think>\n\n</think>\n\n`. This follows the `enable_thinking=false` branch inspected at upstream base-model revision `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`. Both native budgeting and generation share this exact formatting path. No reasoning text is generated or substituted for answer content. This is a local per-model adapter, not a global model preference change. The larger Q8 artifact increases resource pressure; its suitability for phones is unmeasured.

Qwen3 claim decoding subsequently uses temperature 0.7, top-k 20, top-p 0.8 and presence penalty 1.5, following the [publisher guidance](https://huggingface.co/Qwen/Qwen3-1.7B-GGUF#best-practices). The local penalty window is 256 generated tokens and the seed is fixed at 42 before observing this candidate's outputs; no seed search is performed. Other model architectures retain greedy decoding. The constrained output budget is intentionally much smaller than the publisher's general recommendation and remains a limitation.

## Final checks and artifact identity

- `bash tools/android-build.sh`: PASS, standalone offline build, 5 seconds; ARM64 and x86_64 libraries are packaged. Gradle reports deprecation warnings for a future Gradle 9 upgrade; this check uses the existing 8.13 toolchain.
- `bash tools/evaluation/check_synthesis.sh`: PASS, real model/JNI execution on existing `emulator-5560`. Four factual development cases generate; the absent case abstains without generation. The fictional conflict draft becomes explicitly labeled fallback, not a generated-success case.
- Host controls pass, including conflict withholding, raw citation mapping, unsupported numbers, context overflow, cancellation, cross-subject leakage and word forms. Fourteen earlier answer routing/citation/cancellation regressions also pass; these host fixtures are not model-quality evidence.
- Android instrumentation independently rejects native context overflow before output, checks native pre-cancellation, and invokes 11 actual generated citation spans, verifying their exact source-ID callbacks. This task does not repeat physical taps, new-model SAF import/restart, in-flight cancellation latency, or actual source-dialog usability with the larger model.

[Raw final outputs and prompts](synthesis/final/results.json), [behavioral summary](synthesis/final/summary.json), [standalone build](synthesis/final/standalone-build.log), and [exact artifact identities](synthesis/final/artifact-identities.json) are frozen. The final rerun produced byte-identical raw drafts to the preserved phase-check failure run; timing fields differ. This demonstrates repeatability for this configuration, not robustness across seeds or unseen questions.

Implementation/evaluator source commit: `3ac4122f6b54ff2f2aa46e33899b8606a078c6c3`. Final APK SHA-256: `b726fe8c6364a4a42e6526802d00de5af1427b3e804d3e7ec95eed4e05ce2676`. Test APK SHA-256: `7c61415ec9c92844b5c68248610f277513edc1d0eada1571506b7b33d233fc92`. Raw final result SHA-256: `8e68cc1bce95ee7521c62f2f391f9e1e8c8cc37acb4a02618e0ef9924e63c711`.

Native library SHA-256 values:

- `lib/arm64-v8a/libpocketlore.so`: `47878f01fe41b989ebc952c3dc21d11c2753d09e6a9b5b994e75ee4e471d53c5`
- `lib/x86_64/libpocketlore.so`: `35ff53c5a71792e9a35ab4f08e37fa490d1d166412d6fef03df5d9f289d95815`

## Final emulator timings

Model load: **816.963 ms**. These are individual warm/uncontrolled-cache development measurements, not phone latency or a p50/p95 study.

| Case | Route | Prompt / emitted tokens | First token ms | Total ms | Citation callbacks |
| --- | --- | --- | ---: | ---: | ---: |
| comparison | GENERATED | 440 / 42 | 20322.698 | 25895.203 | 4 |
| explanation | GENERATED | 459 / 20 | 20127.691 | 23021.911 | 1 |
| synthesis | GENERATED | 597 / 79 | 26228.480 | 37041.422 | 4 |
| conditions | GENERATED | 399 / 74 | 17449.423 | 26621.226 | 2 |
| absent | ABSTAINED | 0 / 0 | 0.000 | 3.107 | 0 |
| conflict-fixture | FALLBACK | 287 / 9 | 13011.924 | 14164.709 | 0 |

A [single memory snapshot](synthesis/final/memory-snapshot.txt), taken during the preceding repeat with this same APK, reports Android TOTAL PSS 2,129,461 kB, TOTAL RSS 1,919,164 kB and TOTAL SWAP PSS 226,354 kB. These are the platform-reported aggregates, not a measured peak. Swapping and the emulator's small memory configuration affect interpretation. The saved app model still has its original 0.5B hash, as [verified separately](synthesis/final/saved-app-model-sha256.txt).

## Builder claim-to-source review of final output

| Case | Actual generated claims and cited support | Review and limitation |
| --- | --- | --- |
| Phase comparison | Liquid-to-vapor evaporation, then condensation as its opposite; linked to `evaporation-398183fefbcbafbf` and `evaporation-dd7620163089bbe8` | Both statements are directly in their excerpts. The reverse direction is inferable rather than restated. Both labels on both claims overcite; this is a brief comparison, not deep reasoning. |
| Heat explanation | Heat removal requires energy to separate water molecules; linked to `evaporation-460a70d340b737c3` | Matches the cited causal explanation. One concise generated claim, with heavy source wording reuse. |
| Groundwater/runoff synthesis | Infiltration toward saturated rock versus runoff factors and the approximate one-third portion; linked to `groundwater-abbc88d938b327f2` and `runoff-cee7b48b52dc99d4` | REJECTED in review: slow movement within groundwater does not establish slow movement before saturation. The complete generated answer is unsupported and must be corrected or withheld; other sourced clauses do not rescue this claim. The repair report above supersedes the original builder assessment. |
| Conditional recharge | Deep aquifers refill slowly; a shallow aquifer in substantial precipitation, such as coastal south Georgia, **may** refill almost immediately; linked to `infiltration-6bdab6adeed3d925` | Both clauses are directly supported and retain the shallow example's location, precipitation and uncertainty. The answer does not invent a universal numeric recharge time. |
| Absent evidence | No model draft; missing cure/diabetes coverage is disclosed | Correct bounded abstention for this pack/case; not general premise or medical-safety validation. |
| Fictional conflict control | Model states active and not active without resolving the conflict | Application withholds that draft, names both source IDs and explicitly discloses potential unresolved disagreement. This is safe fallback, not successful model conflict reasoning or factual corpus evidence. |

The automatic PASS covers the named behavioral and bounded meaning checks, not all semantic implications in the review above. The model-generated text remains short and close to source wording. General multi-source reasoning, implicit contradictions, counterfactuals, long answers, source uncertainty preservation across arbitrary inputs, blind human review, physical Android/GrapheneOS and release resource limits remain open. No external dependency prevented the rig checks; the remaining quality limitations are engineering/evaluation gaps, not a hardware-blocker claim.

Historical artifact files are listed in [SHA256SUMS](synthesis/SHA256SUMS). Model weights, APKs and bulk source assets remain in ignored paths rather than Git.

Final APKs are also retained in the ignored run directory recorded in `artifact-identities.json`. Earlier trial raw outputs, prompts, check failures and APK hashes are retained; earlier trial APK binaries were not separately archived, so no bit-for-bit replay of every intermediate APK is claimed.
