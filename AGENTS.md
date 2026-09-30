# PocketLore development contract

Build a useful fully offline Android research application for bounty 31. All source, filenames, comments, prompts, UI and public documents must be English. Private original conversations remain verbatim and must never enter Git. Only direct user conversations may be Turkish; all persisted critic output must be English and limited to one sentence of at most 35 words.

All implementation, compilation, inference and data processing run on LLMRig. The Mac is a coordination client. Reuse installed tooling; do not change unrelated projects, services or global Codex configuration. The atlas project is read-only prior work, not a source tree to copy or automation to resume.

## Acceptance and evidence

- Android and compatible GrapheneOS hardware, maximum 12 GB device RAM and 50 GB total installed assets, no research-time network, no core Google Play Services.
- Explanations, comparisons, synthesis and reasoning must be useful and supported by inspectable sources. Retrieval or quoted text alone does not establish answer quality.
- Physical-device acceptance remains open until measured on real hardware. Desktop and emulator results must be labeled and never substituted.
- Freeze development and holdout evaluation before tuning. Do not inspect holdout for implementation. Preserve raw failures, exact artifact hashes, source provenance, timings and resource definitions.
- Never assert competitive superiority without comparable evidence. LLM reviewers are not human acceptance.

## Work lifecycle

Each task has an objective, editable scope, dependencies, checks and evidence artifacts. Builder completion is not acceptance. Validate, freeze evidence, obtain independent criticism, then checkpoint and dispatch the next ready task. The critic sees only goals and immutable artifacts/tests, not planning history.

Use explicit persisted Codex session IDs, never global `--last`. One runner owns the writer lock. Persist transitions atomically and handle repeated completion events idempotently. Resume existing work after crashes instead of duplicating it. Three identical failures require a changed approach, with failed evidence preserved. External dependencies block only dependent work.

Commit meaningful changes frequently. Keep failing experiments on checkpoint branches; main advances only with relevant checks and review. No empty commits, force pushes, destructive cleanup, credentials, private control archives, model weights, build binaries or bulk datasets in Git. Normal project commits and pushes are authorized. Preserve licenses and attribution for reused components.

## Release gaps

The private runner must continue concrete independent tasks while physical hardware is absent. Stop dispatching only when achievable release work is complete or all remaining work needs external changes; do not impose arbitrary total task caps or run an endless prompt loop.
