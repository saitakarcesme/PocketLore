# Full-scale Android capacity validation (task 303)

Status: protocol frozen; measurement pending. This is emulator capacity and reader validation, not physical-device, source-rights or generated-answer acceptance.

Recovered the useful task301 implementation through preserved checkpoint `49117a8926f299780eec7ce922ff92f16eaa123f` onto the existing checkpoint branch. Main at inspection was `0e09794`. Earlier 6.23 GB emulator failures and the rolling sweep remain historical evidence; they cannot satisfy simultaneous residency.

## Frozen measurement protocol

Use only isolated `emulator-5562`, AOSP API35 x86_64, nominal 4 GB RAM/two cores. Record boot fingerprint, boot completion, actual memory and `/data` capacity. Leave emulator-5560 and services untouched. Install the rebuilt APK, pinned production 0.5B model, three reviewed reference/science/broad editions, all fifteen wiki and sixteen places primary shards, shared aliases/cities/notices once, and the declared auxiliary OSM/Wikivoyage assets. Auxiliary residency does not imply an implemented reader. No downloads or inference.

Import cumulative version2 collections through the production shared-object transaction using bounded local ADB/FIFO transport; never retire old shards to fit. Hash sealed host inputs and installed objects. Keep all thirty-one shards resident during combined exact-title/redirect, twenty-city/category/spatial and absent-category checks from the existing frozen task301 protocol, source reads and restart. Preserve generation-denied rights flags. Exercise active selection persistence and cancelled/corrupt update rollback against the full resident catalog.

For an actual new-object atomic replacement, use the largest wiki shard (000_00003): a copy of its SQLite database with only the user_version header changed and its block container with one unused trailing newline. This explicitly labeled representation-only stress fixture changes no source records, formulas, rights or article offsets. It is not a new corpus edition or factual coverage. Replace both large objects together, preserving the original source inventory and recording transformed hashes. Measure precommit old+new residency, continuously sampled app logical/allocated bytes, device df and process memory. Restore the sealed original representation afterward, measuring the reverse transaction too. No full host corpus duplicate is made; at most one bounded delta archive and replacement shard copies are used.

Report installed app/assets/cache and maximum update footprint in decimal bytes against 45,000,000,000 target and 50,000,000,000 hard cap. The measured FIFO path avoids a provider archive copy; separately report the conservative additional provider-copy budget and do not call that an observed peak. Instrumentation captures a precommit point while old and new objects coexist; timed samples alone may miss instantaneous maxima. APK/test APK and Android runtime overhead are separated. Cold restart means app process restart, not emulator restart.

Acceptance must require whole simultaneous inventory hashes, actual full readers, rollback/restart, representative changed-object replacement and measured storage limits. Missing/changed artifacts must fail. A capacity pass cannot certify unique real venues, unreviewed rights, useful model answers, phone performance or human acceptance.

## Identity and provenance

The actual guest reports AOSP API35, `x86_64`, fingerprint `Android/sdk_phone64_x86_64/emu64x:15/AE3A.240806.019/12368160:userdebug/test-keys`, two logical CPUs, 4,014,868 KiB MemTotal and 3,011,144 KiB configured swap. `/data` capacity is 65,871,612 KiB (67,452,530,688 bytes). The initial ADB connection preceded boot completion; execution waited for `sys.boot_completed=1`. [Raw environment](full-capacity/run/environment.json).

The recovered application APK is `43894babe475f2719f3b2a732755b16860f88bee781fb86b5e99c850cbdb30ee`, 15,685,650 bytes. The capacity instrumentation APK is separately pinned in [runtime identity](full-capacity/run/runtime.json). The initial runtime receipt names the protocol commit before the new instrumentation was committed; the final receipt also binds the complete instrumentation source and exact test APK. No production application code was newly changed by task303 beyond recovery of the preserved task301 implementation. Both the explicit required build and instrumentation build pass; Gradle deprecation warnings remain in their logs.

Production remains Qwen2.5 0.5B Q4_K_M, 491,400,032 bytes, SHA256 `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`. It is stored and hash-checked, not loaded for inference in this experiment. The selected Qwen3 4B remains a host candidate, not a deployed model. Three reviewed packs were imported with the production pack importer, retaining 1,113 documents and 40,891 passages; exact archive/index/model hashes are in [seed assets](full-capacity/seed-assets.json).

The sealed lane identities remain wiki `db58d7015b176b2f4721a9fe9a221c9593456e14`, places `9a04ac33488a05f61435d62f8be249fd7fe135af`, Android `13b686c0a386921fb35d4b3d0c27f1168b6da3e0`. Their corrected actual-commit reviews are retained under `docs/evidence/scale-integration`; the earlier stale/empty-diff reviews were not treated as reviews of these changes. Those corrected reviews authorize staged integration only, with unresolved rights, performance and product gates.

| Sealed input component | Bytes |
| --- | ---: |
| Wiki compressed source blocks | 11,244,264,230 |
| Wiki shard indexes | 10,205,188,096 |
| Wiki shared aliases and metadata | 403,980,224 |
| Sixteen places compact shards | 16,817,700,864 |
| Shared cities | 120,569,856 |
| Auxiliary Wikivoyage and OSM databases | 2,158,661,632 |
| Total rehashed sealed inventory | 40,950,364,902 |

The application additionally retains notices, collection manifests, reviewed pack archives/index, the production model and runtime/test package files. Archive transport uses one bounded ignored host file at a time; there is no complete host corpus duplicate or Android input archive. [Host input hashes](full-capacity/run/host-inventory.json) and [auxiliary residency](full-capacity/run/auxiliary.json) are distinct from the final Android object audit.

Wiki counts distinguish full articles from leads; neither implies reviewed encyclopedic coverage. Places counts are source UUID records, not proven distinct physical venues. Dataset-level license labels and exact hashes do not resolve article-specific or third-party rights. Bulk generation remains denied. Current opening hours and diet suitability remain unknown; routing is unavailable. No inference, private holdout, service modification, publication, branch switch or main advancement is part of task303.

## Preserved sampler failure and recovery

The sixth places import (`places-05`) published its collection successfully, then instrumentation failed because a concurrent `Files.walk` saw the normally deleted FIFO and wrapped `NoSuchFileException` in `UncheckedIOException`. The production import did not report an integrity/capacity failure. [Original failure](full-capacity/failures/places-05-original/instrumentation.log), transport and df samples are retained, along with the original test APK.

The test-only sampler now retries that specific disappearing-file condition; other sampling errors still fail. The repaired instrumentation is separately pinned in `run/runtime-sampler-repair.json`. A dedicated reconciliation operation verified the already-published manifest against the exact attempted input and rechecked real SQLite schema/counts. The committed shard was not downloaded, copied or imported again. Its original elapsed and precommit peak fields were not persisted and are explicitly unavailable, not reconstructed or marked as successful measurements. Subsequent imports, full residency and representative replacement peaks are measured normally. Acceptance requires the reconciled manifest identity and final whole-inventory hash audit, while preserving this telemetry limitation.
