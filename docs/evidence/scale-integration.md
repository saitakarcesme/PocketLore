# Task 300: measured first-shard product integration

Status: **offline browse/import/JNI milestone, not full-product completion or acceptance**. Final APK SHA-256: `3d804882ea576fb5ebdd29144a88fa8002c99efbd97c45323928a7c8a1d2e98f` (15,669,266 bytes). All builds, artifact hashing and execution ran on LLMRig. Android observations are from the supervised x86_64 emulator-5560, with airplane mode enabled and Wi-Fi disabled; no physical or GrapheneOS measurements exist. No private holdout was accessed, model tuned, service restarted, branch switched or artifact published.

## Source and review integrity

Actual private Git metadata was inspected and fetched, without touching worker files. The exact tools/docs diffs were reviewed before selective integration:

| Lane | Actual commit | Actual tree | Integration boundary |
|---|---|---|---|
| Wiki | `db58d7015b176b2f4721a9fe9a221c9593456e14` | `60ce0c633c004b62354639d2882f67469b2814f7` | Tools, provenance and evidence only; no lane orchestration/state |
| Places | `9a04ac33488a05f61435d62f8be249fd7fe135af` | `649d0b9e097cdabf5bea14065913f037de655b01` | Tools/readers/evidence, then Android adapters |
| Android | `13b686c0a386921fb35d4b3d0c27f1168b6da3e0` | `4b82de8e3a5be66018152edf466ce72abf507901` | Reviewed application/import recovery changes |

[Lane identities](scale-integration/lane-identities.json), [actual artifact hashes](scale-integration/artifact-checks.json), and the three `*-actual-review.json` records preserve the corrected independent reviews. The launcher empty-baseline reviews remain historical invalid evidence in the lane handoffs. Corrected review permits integration development, not product, distribution or answer acceptance. No worker root `LOOP_STATE.json` was imported.

## Implemented behavior

A durable bulk catalog streams ZIP entries into owned staging, verifies declared lengths and SHA-256, validates SQLite schemas and installed counts, then atomically publishes the catalog. Failed/cancelled imports preserve existing collections and the model. Active bulk selections persist. Existing small-pack collections retain their separate compatible catalog. Bulk import has a 50GB hard admission check covering retained app-file assets plus incoming staging and a128MiB runtime allowance; free-space admission also preserves256MiB. This is not a measurement of total final installed overhead or arbitrary document-provider caches.

Android's SQLite3.44.3 has no FTS5 on this emulator; the actual failed probe is retained. A separate, pinned public-domain SQLite3.53.4 library provides read-only FTS5, a64MiB SQLite heap cap,4MiB connection cache, no mmap/extensions, bounded rows/results and cancellation/deadline checks. Platform SQLite and llama.cpp are unchanged. Source/build pins are in [sqlite-pin.json](../../tools/runtime/sqlite-pin.json); [upstream FTS5 build instructions](https://sqlite.org/fts5.html) and [public-domain dedication](https://sqlite.org/copyright.html) apply. ARM64 and x86_64 binaries were built; only x86_64 was executed.

Wiki search prefers exact titles when present and interleaves per-shard ranks rather than allowing the first shard to occupy all non-exact slots. This is not the lane host global-IDF ranking, and full multi-shard ranking/aliases remain unqualified. Block decoding streams to a selected-record temporary file, verifies block/record/text hashes and retains a64,000-character preview. Raw block admission128MiB, compressed64MiB and record32MiB are explicit; the8MiB producer target is **not a hard source bound**. Larger records are refused, not silently truncated into complete-source claims.

Places use bounded city aliases, category and radius filters over retained source blocks. Cities are proximity anchors, not municipal boundaries. Results preserve source UUID/ordinal, original attribution, dates, confidence and status fields. Current hours/diets are unknown; routing is unavailable. Source dialogs and offline license text are available through the actual controls. NFKC/lowercase city lookup is not complete Python Unicode casefold equivalence. Global semantic entity deduplication is not claimed.

**New bulk records remain browse-only.** `dataset_license_only_unreviewed` and other unresolved source-specific rights are not cleared by checksums, preserved wikitext, title links, contributor-history links or a dataset license. Task221-dependent useful source support remains mandatory before bulk model integration. No selected4B model or admission change occurred.

## Installed milestone versus sealed host inventory

| Component | Actually installed emulator milestone | Sealed host inventory, not installed |
|---|---:|---:|
| Wiki article count |413,151:82,022 full +331,129 leads |6,498,498:1,250,000 full +5,248,498 leads |
| Wiki files including manifest |1,424,169,186 bytes |21,853,451,129 bytes, all15 shards/aliases/notices |
| Places source UUID records |5,120,674 |81,455,423 across16 shards |
| Places first shard + cities/notices/manifest |1,172,547,596 bytes |16,817,700,864 bytes places;2,279,572,113 cities/travel/OSM/notices |
| Production Qwen2.5 0.5B |491,400,032 bytes |Same pin; no new weights downloaded |

The host places exact name/coordinate/category grouping has81,430,561 groups; this is not proven distinct real-world entities. Raw source country labels can be invalid and field fill does not establish factual correctness. The optional overlapping ZIM is excluded from the primary selection. Wiki retains historical August2025 Enterprise-derived content;282 recognized notice exclusions do not resolve all third-party exceptions. The lane's1.25M full articles do not fulfill its original2–3M full-text aspiration.

Archive bytes differ from installed payload bytes: wiki1,424,170,364; places1,172,549,792. Exact per-file/archive/model/APK/DEX/native hashes are in [wiki receipt](scale-integration/wiki-receipt.json), [places receipt](scale-integration/places-receipt.json), and [candidate identity](scale-integration/candidate.json). Unchanged sealed bytes were reused, not redownloaded. Assets stay outside Git.

[Joint budget](scale-integration/joint-budget.json) totals roughly41.46GB for all primary sealed data plus the current APK and production model, before retained small packs, extracted native/ART files, filesystem/provider overhead and update copies. Substituting the host-only4B file would make this subtotal roughly43.46GB; it does not authorize deployment. The provisional4GB places budget failed. The earlier27.2GB and22.383GB wiki projections remain preserved; only the final host inventory dropped below22GB. **Neither45GB target nor50GB full installed/update acceptance is established.**

Wiki import took4439ms and places3693ms on the emulator. Peak owned staging bytes were respectively1,424,169,186 and1,172,547,596, plus the separately present input archives. After the places import while its archive remained, `/data` used5,223,140KiB with716,792KiB available. After removing only these project-owned input copies (host originals retained), available storage was about1.8GiB. A full41GB installation cannot be exercised on this unchanged6GB userdata volume. Full-edition replacement/update peak has not been measured; current whole-edition admission would reject updates that exceed the joint bound instead of deleting old assets.

## Actual behavior and preserved failures

Raw final observations are under [final-run-5](scale-integration/final-run-5/run.json), with earlier runs retained. The frozen protocol contains eight topic queries,20 cities and four absent/time-sensitive controls. All eight first-shard topic queries returned related candidates; none of the intended exact titles was installed in this shard. Examples: Acid returned Hydroxykynurenic acid; Cooking returned Cooking Mama4; Athens returned Athens Suburban Railway. This is a coverage miss, not a useful answer. Source reads still resolved exact edition-aware identities and verified text bytes.

Only Mexico City returned nearby records among the20 frozen city queries at1km; the other19 returned zero place candidates in this shard. The positive query took roughly8–9seconds for30 candidates. Empty-result timings must not be presented as useful global-query latency. An absent category returned no records. Other time-sensitive controls could retrieve related text, but generation stayed disabled and live status unknown; this does not prove semantic answerability detection.

The first oversized read exposed a196,104,864-byte Java allocation with205,649KiB post-read PSS. [Failed run](scale-integration/inspect-failure-1.json) preserves this and a platform PRAGMA API failure. Streaming JSON decoding fixed the allocation while retaining exact text hashing. The same23,473,862-byte article/block subsequently took about2.4seconds, with roughly10MiB sampled Java usage and35MiB sampled PSS;20ms sampling is an observed sample maximum, not a universal allocation proof. Full RSS/swap snapshots are in raw `/proc/self/status` observations. Cancellation during this read took4ms in the recorded run. Metadata claiming a record over32MiB is rejected before allocation; this injected admission case does not prove OS OOM safety.

Corrupted import, cancellation before/during copy, over-limit admission, same-process valid retry, changed compressed-source block, read-only SQL and running-query cancellation all exercise actual code. Tests retain both collections, clean staging and verify the unchanged saved model. A preserved `final-run-4/ui.json` failure exposed the test reading before the asynchronous Apply handler executed; the harness now drains main-thread handlers before waiting on the worker. Actual UI controls inspect both source types and disable/re-enable a collection with durable state. Process-cold instrumentation reloads the catalog; this is not physical lifecycle acceptance or an unmeasured crash-during-rename guarantee.

## JNI evidence and source assessment

The unchanged production SHA is `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`. Runtime is llama.cpp `bb4caa7540188872173c44d161602d9271386413`, CPU,2 threads,2048 context. Real JNI load/generation/cancel/reset/close/reload ran while the bulk catalog was present and queried. The original catalog remained3 active editions,1113 distinct documents and40,891 passages; bulk counts are not added to generated-answer coverage.

Actual draft: `[S1] Headlamps are the recommended light source because they are hands-free.` The production controller rendered the exact namespaced NPS citation. **Builder assessment:** supported and complete for this narrow question, because the actual cited excerpt explicitly states this reason. It is near-extractive generated prose, not evidence of broad synthesis, task221 quality or generalization. Unrelated Constitution/Declaration retrieval candidates remain in the raw record as failures. No canned response or fallback is counted as generation.

The final frozen control loaded in354ms, first token25435.371ms, total controller time27168.603ms, with combined PSS576100KiB. Controller times start after initial retrieval and exclude model load. The largest-source read took2415ms; sampled maxima were35340KiB PSS and10502656 Java bytes across82 samples. See [measurement summary](scale-integration/measurement-summary.json) for observed RSS/swap and definitions. Every run's exact timings and observed RSS/swap remain in raw JSON. These are emulator CPU measurements, not phone performance. The selected4B candidate remains host-only, and its historical26/40 draft potential versus4/40 useful controller results are not superseded.

## Reproduction and gates

1. Reuse the sealed lane paths and recorded actual commits. `python3 tools/runtime/fetch-index.py` fetches the pinned SQLite amalgamation only if absent; `--verify-only` is offline. No corpus/model network inference is used.
2. `python3 tools/evaluation/scale-integration/build_bundles.py` creates deterministic first-shard archives in ignored `downloads/scale-integration`; existing outputs are retained. `build_source_fixture.py` creates a separately labelled real-source byte regression subset, never additional coverage.
3. `bash tools/android-build.sh assembleDebug assembleDebugAndroidTest -PpocketloreTestRunner=org.pocketlore.app.ScaleIntegrationInstrumentation`. Install on existing emulator-5560 without launching/restarting a service. Import archives serially through the bulk control or the documented instrumentation `mode=import`, retaining host originals before removing project-owned input copies.
4. `run_android.py negative inspect ui native --output <new evidence directory>` performs serial behavior checks. The receipt records actual installed application/test APK hashes. `seal_candidate.py` is an explicit freeze and refuses to overwrite an existing seal; it never marks tests passed.
5. Required checks: `bash tools/android-build.sh` and `python3 tools/evaluation/verify_scale_integration.py`. The latter checks exact source/build/model/run/archive/installed-file identities, mutates real copied run/model artifacts to prove changed/missing rejection, and runs fresh Android behaviors. A PASS is restricted to this measured milestone; it does not clear the gates below.

Remaining concrete work is queued as301-scale-inventory-and-shard-updates and302-scale-reviewed-source-answer-adapter. No orchestration state was changed or task dispatched. Full multi-shard/redirect quality, incremental update peak, OSM/Wikivoyage app interfaces, broad rights/fidelity clearance, useful source-bound bulk answers and selected-model Android qualification remain open. General answer-architecture task224 is reused rather than duplicating its old matrix.

Before competitive evaluation, freeze code, model, prompts, retrieval settings and corpus hashes. A **separate independent evaluator** must retain unseen/topic-held-out/source-held-out questions, distractors, paraphrases, multi-part/false-premise/absent/time-sensitive cases and compare named rival versions/frontier-web under matched conditions. Builder access remains prohibited. Development questions here are diagnostics, not generalization evidence; contamination and development/held-out results must be reported separately. No rival superiority, human acceptance, clean-machine reproduction, production signing or physical/GrapheneOS gate is claimed.

The current source/check freeze is a development candidate, not a final competitive freeze. The read-only held-out evaluation has not run. Follow-up work must issue a new immutable identity and separate evaluation; it must not silently reuse these public questions as unseen evidence.

### Required check results

Both required commands exited0 on the frozen candidate. [Build log](scale-integration/acceptance-build.txt), [behavioral verifier log](scale-integration/acceptance-verify.txt), [fresh emulator run identity](scale-integration/acceptance-run/run.json) and [receipt hashes](scale-integration/acceptance.json) preserve actual results. Missing and same-sized changed copies of the actual model and actual run JSON were rejected; original weights/evidence were not modified. This result certifies the explicit measured milestone only. The broader task/product remains partial with the release gaps above.
