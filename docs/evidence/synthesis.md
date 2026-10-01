# Synthesis development evidence — task 050

Status: validation in progress on the LLMRig AOSP x86_64 emulator. This is builder development evidence, not independent acceptance or physical Android/GrapheneOS evidence. Private holdout was not opened. No runner, service, global model preference or branch was changed by this task; no push was made.

## Artifacts and method

Questions and source review anchors were frozen in commit `2e47d39`, before synthesis tuning. `tools/evaluation/synthesis-cases.json` SHA-256 is `1eb30aa083e9f34be45b13ee09a67c7c7442d67a2ff81050b2d92b248450840e`. The five cases are phase comparison, evaporation explanation, groundwater/runoff synthesis, conditional recharge comparison and absent evidence. Four require actual generation. A separately labeled fictional sensor contradiction tests controls only; it is not factual corpus or a quality score case. No canned factual response is substituted for model output.

The real English pack contains 186 passages from 10 attributed documents; its SHA-256 is `567e9bbbaab896826809ec20f81ae1c4b3f421b011931edae0989d28cfce10ea`. Prompts include excerpts, dates and source URLs; raw reports retain retrieved passages as well as the actual selected prompt. The source dates may describe archived content and do not establish present conditions.

The runtime remains llama.cpp b10566 commit `bb4caa7540188872173c44d161602d9271386413`, CPU-only, two threads, fresh context per request, greedy sampling. Task 050 builds both ARM64 and x86_64; only x86_64 executes here. Context is 2,048 tokens, output reserve 256, batch 2,048 and microbatch 128. The native tokenizer counts the model's complete chat template. Native code independently rejects prompt plus output overflow.

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
