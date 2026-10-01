# Scale model quality: in-progress host comparison

Task 220 is not complete or accepted. Task 212 results and its unsupported first-run drafts remain in [broad-answer evidence](broad-answer-integration.md); the older complete-claim result remains 3/27 useful answers. No optional model has replaced the deployed Qwen2.5 0.5B Q4_K_M model (`74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`).

## Frozen comparison

Commit f9522c5 froze 48 new public development questions across eight topic pairs, including literal, explanation, comparison, multi-part, false-premise and absent questions. A documented pre-generation source amendment in 45d4ea4 selected the paragraphs explicitly establishing BST worst-case complexity and negative apparent magnitude, without changing questions or expectations. The current protocol hash is `061bb57fb3c0fa6715762846ad8ef1c72f004417e41ad5426b2534d8c90a512b`.

Every candidate receives the same six pinned real paragraphs and deterministic obligation plan. This is an oracle-evidence capability screen, not production retrieval. The experimental controller is not wired into the application UI. Expectations are not included in prompts. There is one greedy generation per case, 4096 host context tokens, 512 output tokens and six CPU threads per process. No prompt retries or seed search are used. Android retains its 2048/256 limits and 2 GiB model ceiling.

Candidates are the actual 0.5B baseline, reused Qwen3 4B Q4_K_M (2,497,280,256 bytes), Qwen2.5 7B Q4_K_M (4,683,074,240 bytes), and Qwen1.5 MoE A2.7B Q2_K (5,890,164,032 bytes; 14.3B total/2.7B active parameters). Exact revisions, SHA256 values and licenses are in the frozen model pins and THIRD_PARTY_NOTICES. The MoE has a custom Tongyi license, not Apache 2.0; its redistribution, commercial-scale and model-training restrictions remain explicit. No weights are committed or published.

## Preserved resource failure and execution revision

The initial run is `downloads/scale-model-quality/matrix-20261001T092716Z`. The baseline completed 48 calls. The 4B job completed all 48 calls in 1,808.879 seconds. Both larger models initially produced 48 zero-token buffer-admission errors: these are failed resource attempts, not quality measurements, despite the harness process exiting normally.

CPU_Mapped plus CPU_REPACK weight buffers measured about 7.8 GB for 7B and 8.22 GB for MoE, exceeding the original file-equals-buffer assumption. Peak process RSS on those failed attempts was 7,674,200 KiB and 8,317,828 KiB respectively, with zero sampled swap. No host memory exhaustion was attempted.

Commit 097fe24 declared a resource-only revision before either larger model generated: file cap remains 6,000,000,000 bytes; host native weight-buffer cap becomes 9,000,000,000 bytes; KV/compute caps remain 768 MiB/1 GiB. Numerical kernels, CPU repacking, decoder, prompts and model pins are unchanged. One revised large-model job runs at a time, reserving 10 GB for 7B or 10.5 GB for MoE plus 2 GiB available host margin, with a 10.5 GB sampled RSS kill ceiling. The existing 4B job can continue, for at most two inference processes. Successful baseline/4B generations are not repeated. The revised matrix is `downloads/scale-model-quality/buffer-v2-20261001T094434Z` and is still partial.

Timing is CPU host timing under declared concurrent work, not an isolated speed ranking or phone result. The session cannot access a working GPU driver interface; the preserved preflight is not evidence that the host lacks GPUs. No service or GPU stack was changed.

## Assessment and current limitations

Builder source assessments are recorded separately in `scale-model-quality/reviews`. Completed baseline/4B review finds respectively 1/40 and 26/40 fully useful supported drafts, and 4/8 versus 8/8 useful absent-case responses. Machine candidates are 0 and 5; one of those five 4B candidates is incomplete. These are draft/screen outcomes, not production publications. The partial 7B run includes a source-scope error in s16 that passes the lexical controller: a benefit of smaller pruning wounds is recast as the general purpose of removing unwanted material. No parser or prompt change is being made during the matrix. A draft can be semantically useful yet withheld by the sentence-citation gate; this is reported as draft capability, never published success. Correct absent answers are counted separately from the 40 supported/false-premise cases. All candidate text still needs independent source criticism. No selection is made from partial runs.

The existing emulator has approximately 2.42 GiB total RAM and cannot establish these larger candidates' mobile suitability. Its admission limits remain unchanged. The sealed Android worker handoff was hash-checked read-only and is not merged: it retains the same model ceiling, reports an answer-check failure also seen at its baseline, and has no emulator execution evidence. No private worker state, holdout or services were read or altered.

## Checks so far

`bash tools/android-build.sh` passes after the conditional host-profile changes (40 seconds; raw log `downloads/scale-model-quality/android-build.log`). The required quality verifier deliberately fails while selection and complete review artifacts are absent; the preserved partial failure is `downloads/scale-model-quality/verifier-partial.log`. Controller replay, exact source checks and missing/changed artifact regressions are implemented, but final matrix validation is pending.

Remaining work: finish all actual model runs, inspect every draft against its exact citations, freeze raw receipts and metrics, choose a supported model/architecture next step, record precise integration/resource gaps, and obtain independent criticism. Host results cannot close physical Android, GrapheneOS, thermal, clean-machine, signing-owner or human acceptance gates.
