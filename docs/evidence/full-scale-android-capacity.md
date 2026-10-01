# Full-scale Android capacity validation (task 303)

Status: required build and behavioral capacity verifier pass on emulator-5562; independent criticism and product acceptance remain open. This is emulator capacity and reader validation, not physical-device, source-rights or generated-answer acceptance.

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

Production remains Qwen2.5 0.5B Q4_K_M, 491,400,032 bytes, SHA256 `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`. During import/hash/reader instrumentation it is stored and hash-checked, without creating a model session. The later normal Activity navigation may automatically load this baseline through the existing UI lifecycle; no answer generation is requested, and that observation is separate from the storage-run memory samples. The selected Qwen3 4B remains a host candidate, not a deployed model. Three reviewed packs were imported with the production pack importer, retaining 1,113 documents and 40,891 passages; exact archive/index/model hashes are in [seed assets](full-capacity/seed-assets.json).

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

## Full-catalog redirect failure

The first simultaneous reader run returned the eight exact titles correctly and restaurant candidates in all twenty cities, but `USA`, `NYC` and `UK` fell through to unrelated FTS titles. These raw failures remain in the inspection reports; their instrumentation status reflects completion of the capacity/read exercise, not correctness of every redirect. Inspection of the sealed aliases database found acquisition shard names ending in `.parquet`; Android normalized only `.sqlite`, so it silently skipped the actual targets. The existing host protocol's target IDs/titles are frozen in `tools/evaluation/full-capacity/redirect-regression.json` before the narrow Android mapping repair. Final acceptance additionally requires actual installed Android resolution and source inspection for those exact targets. Existing storage/import measurements remain tied to the earlier APK; the repaired candidate is separately identified and does not change shared import/update code or source bytes.


## Actual results and current candidate

The final candidate APK is **`634d60fd48284ffdb7a568125930fff9a4e42e146ce7ddb9366eec102689b7d3`**, 15,685,650 bytes. [Candidate identity](full-capacity/run/runtime-redirect-repair.json) pins its DEX/native/manifest hashes, actual installed test APK and unchanged import-code hashes. Storage transactions were measured on the separately preserved `43894b…30ee` APK; the final production change only corrects redirect shard-name normalization. The final candidate then resolved/read all three frozen redirect targets and opened the actual source dialog with the same complete catalog. No import behavior or asset bytes changed in that repair.

All **31 primary shards** remain installed simultaneously: **6,498,498 wiki records** (1,250,000 full articles and 5,248,498 leads) and **81,455,423 places source records**. The Android audit verifies **84 distinct bulk objects / 40,950,708,231 bytes**, including 343,329 bytes of retained notices beyond the initial sealed input table. Both the initial and restored full-object audits pass. The reviewed editions and saved model retain their exact hashes before/after; shared cities and aliases are stored once, not once per shard.

| Measurement | Decimal bytes / result |
| --- | ---: |
| Final app-data allocation after UI | 41,612,550,144 |
| Installed application code allocation | 15,716,352 |
| Installed test package allocation | 335,872 |
| Final installed allocation including test package | **41,628,602,368** |
| Largest-shard replacement precommit logical app files | 43,127,620,900 |
| Inverse replacement precommit logical app files | 43,128,006,822 |
| Maximum sampled app allocation plus larger measured package-code allocation | **43,145,453,568** |
| Maximum sampled whole-emulator `/data` usage, including OS/other guest files | 43,436,118,016 |
| Conservative one-provider-archive allowance plus 128 MiB reserve | **44,796,211,667** |

The observed installation and replacement fit the **45 GB target and 50 GB hard cap** for this candidate and delivery path. The provider figure is an accounting bound using the measured peak plus the 1,516,540,371-byte inverse archive and 134,217,728-byte reserve; it is **not an observed provider-copy peak**. Retaining every input archive on the device would add another complete inventory and is not qualified by this result. The measured local FIFO transport retains no Android incoming ZIP. Application/test code is measured separately with `du`; the final table conservatively includes the slightly larger final test package. Temporary peaks, APK update overhead, unrelated user files and provider behavior must not be silently conflated.

The representative changed-object update took **61.822 seconds**, and restoration took **59.596 seconds**, including retained-object verification. Both changed large objects coexist with the old version before catalog publication; obsolete objects are reclaimed afterward. A real cancellation after more than 1 MiB of incoming data and a corrupt notice payload both reject without changing the published catalog or saved model. The cancelled attempt's 12.394 seconds includes retained-hash verification, so it is not a cancellation-signal latency claim. Active selection survives an actual process restart; all collections were re-enabled for final inspection.

The three full reader passes each return restaurant candidates in **20/20 frozen cities** (results capped at 30, not a venue census). The initial exact-title/source checks took 297–507 ms; first-pass city queries took **1.713–19.139 seconds**. Mexico City took 8.688 seconds and New York 19.139 seconds. This is a remaining usability gap, not rival-level speed. The original redirect misses remain visible in all pre-repair reports; the final repaired lookup resolves United States, New York City and United Kingdom with exact expected shard/article IDs and source reads in **282–396 ms**. No generated answers were requested or scored.

Observed import/reader instrumentation PSS peaked at **88,226 KiB** across successfully captured samples (including the final redirect regression), with raw RSS/swap/process snapshots in each result. This excludes the lost sampler fields already disclosed. The normal UI source dialog snapshot reports **569,978 KiB PSS, 693,440 KiB RSS and zero process swap**, after the ordinary Activity lifecycle may load the pinned 0.5B model. It is a separate single snapshot, not a sustained model qualification, OOM, thermal or physical-phone result. Guest MemTotal and swap configuration remain explicit in the environment receipts.

[Actual UI source dialog](full-capacity/ui/source-dialog.png), [active collections](full-capacity/ui/active-collections.png), accessibility dumps and source/provenance text are preserved. Two UI-driver failures are retained: case-sensitive matching of an uppercased Android button, then tapping an 18-pixel clipped result over system navigation on the 320×640 display. The final driver scrolls the target fully into view. These were test-driver repairs; no failed attempt was relabeled as a successful UI run.

## Checks, limitations and next step

- `bash tools/android-build.sh`: **PASS**, final APK identity above; [required build log](full-capacity/required-build.log).
- `bash tools/evaluation/check_full_scale_android_capacity.sh`: **PASS**; [behavioral/integrity results](full-capacity/verification.log) and [immutable receipt](full-capacity/receipt.json). Changed/missing model bytes and run artifacts, subset counts and an unmeasured replacement peak are all rejected by actual negative mutations.
- Original sampler/UI/redirect failures, prior task301 failures and both earlier APK identities remain preserved. No full-corpus redownload, repeated inference or emulator service change occurred. Emulator-5560 was not modified.

The capacity environment dependency is resolved for this measured baseline candidate. Remaining independent work includes a bounded end-user shard-delivery/import workflow with one incoming archive at a time, and profiling/optimizing the measured dense-city query cost without dropping source fields. Update the release/distribution identity after those product changes and the separately authorized model work; do not reuse release-v5 hashes. Auxiliary database residency is not reader integration. Rights/source fidelity, supported generated answers, selected-4B Android admission/load/cancel/reload/resource qualification, independent unseen matched evaluation, clean-machine reproduction, production signing ownership, physical Android/GrapheneOS and human acceptance remain open. No private holdout, global preference, orchestration, service or main change is part of this checkpoint.
