# Synthesis development evidence — task 050

Status: validation in progress on the LLMRig AOSP x86_64 emulator. This is builder development evidence, not independent acceptance or physical Android/GrapheneOS evidence. Private holdout was not opened. No runner, service, global model preference or branch was changed by this task; no push was made.

## Artifacts and method

Questions and source review anchors were frozen in commit `2e47d39`, before synthesis tuning. `tools/evaluation/synthesis-cases.json` SHA-256 is `1eb30aa083e9f34be45b13ee09a67c7c7442d67a2ff81050b2d92b248450840e`. The five cases are phase comparison, evaporation explanation, groundwater/runoff synthesis, conditional recharge comparison and absent evidence. Four require actual generation. A separately labeled fictional sensor contradiction tests controls only; it is not factual corpus or a quality score case. No canned factual response is substituted for model output.

The real English pack contains 186 passages from 10 attributed documents; its SHA-256 is `567e9bbbaab896826809ec20f81ae1c4b3f421b011931edae0989d28cfce10ea`. Prompts include excerpts, dates and source URLs; raw reports retain retrieved passages as well as the actual selected prompt. The source dates may describe archived content and do not establish present conditions.

The runtime remains llama.cpp b10566 commit `bb4caa7540188872173c44d161602d9271386413`, CPU-only, two threads, fresh context per request, greedy sampling. Task 050 builds both ARM64 and x86_64; only x86_64 executes here. Context is 2,048 tokens, output reserve 256, batch 2,048 and microbatch 128. The native tokenizer counts the model's complete chat template. Native code independently rejects prompt plus output overflow.

The optional candidate is upstream `Qwen/Qwen2.5-1.5B-Instruct-GGUF`, revision `91cad51170dc346986eccefdc2dd33a9da36ead9`, `qwen2.5-1.5b-instruct-q4_k_m.gguf`, 1,117,320,736 bytes, SHA-256 `6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e`. Its Apache-2.0 license and attribution are bundled; the explicit reproducible downloader and pin are under `tools/evaluation`. Weights stay ignored. The evaluator overrides only the model hash in a run-local copy of the frozen fixture. It uses `files/synthesis-tests/model.gguf`, preserving the app's original saved 0.5B model. The larger import bound is implemented but new-model SAF import/restart was not exercised in this task.

The initial 0.5B model SHA-256 was `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`. Changing the evaluation candidate does not change system/global model preferences.

## Preserved failures

- `synthesis/initial`: actual 0.5B outputs omitted citations and confused the direction of evaporation; the exact-term gate also blocked remove/removes. Overall FAIL.
- `synthesis/unconstrained-1.5b`: actual larger-model drafts still omitted citations, transferred cooling to evaporation and assigned aquifer recharge wells to runoff. Overall FAIL.
- `synthesis/constrained-first`: valid citation formatting did not establish support. The application published a cooling/evaporation error and a recharge-wells/runoff error; the conditions answer omitted the requested timing distinction. Overall FAIL. These are factual-support failures, not merely formatting failures.
- `synthesis/selected-context`: selecting one passage for each comparison aspect improved factual text. However, each phase-comparison sentence mixed sources while citing only one. The model abstained on the answerable deep/shallow case. Overall FAIL. The original cooling-transfer regex also falsely flagged a sentence whose second clause correctly described condensation; its later correction stops at the named condensation clause. The original failure summary remains untouched.

- `synthesis/combined-citations`: joint labels fixed the missing-half attribution pattern, but the lexical screen rejected generic second sentences in comparison and synthesis. Explanation generated; the answerable conditions case still abstained. Overall FAIL. The next candidate permits one or two claims instead of requiring an unnecessary second sentence and explicitly permits both claims to use one source.

- `synthesis/concise-claims`: one-sentence phase comparison and the explanation matched their cited excerpts. The groundwater/runoff draft transferred the destination "lakes" from the groundwater excerpt into the runoff clause; the coarse evaluator accepted that draft, but source review did not. Conditions still abstained. Overall FAIL. A specific destination-transfer regression was added, and the next prompt requests qualified qualitative comparisons when exact numbers are unavailable.

Early summaries sometimes counted passage IDs in fallback text as a citation check success; their overall results were still FAIL. The current evaluator requires GENERATED before checking generated citations and verifies exact case/model/pack identities. The combined-source grammar prevents the observed missing-half attribution pattern by requiring the supplied source set on each comparison claim. This may overcite; it is not semantic proof or fine-grained provenance.

## Implemented controls and limits

See [implementation and reproduction](../SYNTHESIS.md). Native constrained decoding supplies format and source-label choices, never answer facts. The model can abstain. Raw drafts remain intact while emitted short labels resolve to stable passage IDs. Final Android citation spans call the source inspection callback; the instrumentation invokes these actual spans and checks exact IDs. This is narrower than a physical tap and dialog usability test.

The lexical support threshold and exact-number screen are conservative heuristics. They can reject a supported paraphrase and accept a false relationship assembled from source words. Broad entailment, premise checking and conflict reconciliation are not solved. The conflict signal covers identical statements with opposite explicit negation; the fictional test model failed to disclose disagreement, so the application withheld its draft and displayed a potential-conflict warning with both source IDs. This safe fallback is not a generated synthesis success.

At most two sentences of 220 characters each sharply limit depth; grammar forbids internal periods, restricting decimals and abbreviations. Context selection can omit necessary evidence, and the absent-term gate still misses paraphrases. No general claim of useful research, unseen accuracy or competitive superiority follows from these development cases.

## Measurement definitions

`load_ms` measures native load of the already provisioned model. Per-case `first_token_ms` starts at entry to the answer controller and includes context selection, token preflight and prefill until the first token callback, often a citation label. `total_ms` includes final validation but excludes earlier pack indexing/model load. Token counts are native emitted tokens; prompt counts include the real chat template and system instructions. No first-useful-content, cold-cache, repeated p50/p95, peak RSS/PSS, thermal or battery measurement is claimed. The model is reused across cases, while each generation creates a fresh context. OS/file caches are uncontrolled.

The emulator reports 2,532,896 kB MemTotal and 1,899,668 kB SwapTotal in the final environment snapshot. These virtual-machine values do not establish physical phone memory suitability. No GPU inference job was run. Assets, model copies, swap, installation peaks and all caches have not been totaled for release acceptance.
