# Task301: shared shards and full-inventory validation

Status: **independent rig work measured; full Android installation remains blocked**. The required Android build passes. The required inventory verifier passes its host, integrity and Android subset/update checks, then deliberately exits 1 because the full inventory and full-scale update peak have not been measured on an approved Android environment. This is not release or product acceptance.

The final APK is `a0cebabd78b9246fa5e1272e4bea1587c7ca80e2785fe31f2ee73048a1719de9`. The large-shard measurements used the prior `b5e0afdbcf6ee92e5022eb7ecca6276c5709274276cd48698148b09ec71e1362` app, before the post-commit cleanup-error guard; final fresh subset/restart checks exercise the final app. Historical identities are preserved.

The existing emulator has a 6,082,144 KiB userdata filesystem. No service was resized/restarted, model changed, private holdout read, branch switched, main advanced or artifact published. Task300 sealed assets were reused without downloads. Task213's fresh install had archived the earlier task300 bulk fixtures; this task began with its three small/reviewed editions and saved production model intact.

## Implemented transaction and reader behavior

Version 2 bulk manifests describe a complete logical collection, the exact prior manifest being replaced, content SHA-256, declared lengths and which files are included in the delta. New files stream into owned staging, pass hash/length and actual SQLite schema/count checks, and enter an immutable shared object directory. Unchanged objects are rehashed and referenced directly. The catalog changes with an atomic rename; only then are obsolete manifests and unreferenced objects reclaimed. City and redirect databases appear once per collection, regardless of shard count. A process-wide writer lock serializes catalog mutation and interrupted-stage recovery.

The initial hard-link design failed on this Android environment with `AccessDeniedException`; [that failure](full-scale/failed-hardlink-android.log) is retained. The implemented design does not require hard links or copying the unchanged edition. Version 1 collections remain readable. Reusing a version 1 edition as a delta base requires an explicit migration carrying its content; absent shared objects are rejected rather than silently copied outside the budget.

The [builder](../../tools/packs/build_shared_scale.py) emits deterministic manifests and optionally ZIP deltas with fixed timestamps. `--shard-limit` plus `--base` supports successive admission; archives with more than 2 GB of incoming payload are refused. Full inventory manifests can be planned without producing a duplicate full-edition archive. Two separately produced first-place-shard archives have identical bytes and SHA, recorded in [deterministic build evidence](full-scale/deterministic-build.json). Earlier pre-canonical ZIPs remain preserved as the actual import inputs.

Admission includes retained app files, new object bytes, metadata allowance, another incoming-payload allowance for a provider copy and 128 MiB runtime/package allowance; free-space admission separately reserves 256 MiB. The UI discloses an admission estimate above the 45 GB target; 50 GB remains a hard rejection. External providers can retain additional unknown caches, and filesystem allocation differs from logical bytes, so this is not a universal device-footprint proof.

Wiki exact titles precede redirects and round-robin per-shard ranks. Redirects resolve only into present shards and retain exact source identity. The first host audit mistakenly interleaved redirect candidates before a later shard's exact title, returning ACiD Productions before Acid; [the failed ordering record](full-scale/host-before-order-fix/wiki-queries.json) remains. The corrected audit matches the Android exact-first ordering. Lowercase normalization is not complete Unicode casefold equivalence. No global-IDF, semantic relevance or general answer-support claim follows from rank diversity.

## All sealed host bytes, not installed coverage

[Host file checks](full-scale/host/files.json) rehash all pinned wiki and places handoff assets. [Actual SQLite counts](full-scale/host/counts.json) cover 15 wiki shards and 16 places shards:

- 6,498,498 wiki articles: 1,250,000 full and 5,248,498 leads.
- 81,455,423 place source records; these are not proven distinct real-world entities.
- 40,950,364,902 bytes across the audited host inventory, including auxiliary assets.

All eight frozen exact topic queries now return their intended title first on the complete host inventory; USA, NYC and UK resolve to United States, New York City and United Kingdom. [Raw queries](full-scale/host/wiki-queries.json) preserve IDs, shards, route and timing. All twenty frozen cities return 30 nearby candidates and ten restaurant-category candidates within the frozen 1 km radius. Exact original source records and provenance are retained in [city results](full-scale/host/cities.json); the invented category returns none. City centers are proximity anchors, not municipal boundaries, and current hours/diets/live status remain unknown.

The corrected host audit took 103.686 seconds and observed process maximum RSS 509,616 KiB. Its per-city timings combine unrestricted search, category search and first-source extraction, so they are not comparable to a single Android query. These are public development diagnostics; no unseen or competitive evaluation occurred.

All unreviewed source-specific rights remain browse-only. Dataset licenses, counts, hashes, preserved wikitext and retrieved snippets do not clear third-party exceptions or establish generated factual support. The full host auxiliary inventory includes formats not yet integrated as Android readers; primary wiki/place manifests do not imply OSM/Wikivoyage interfaces are complete.

## Actual Android transactions and coverage

The [large-shard evidence](full-scale/large-android/large-update.json) comes from the real production importer on emulator-5560, not a host mock. The first full places shard and shared cities/notices installed in one process. A different process applied a second-shard delta to the same collection:

| Measurement | First admission | Second-shard update |
|---|---:|---:|
| Source records retained |5,120,674|10,186,606|
| Input archive bytes |1,172,549,841|1,090,924,091|
| New bytes written, including manifest |1,172,547,925|1,090,923,857|
| Observed precommit app-file bytes |3,218,982,158|4,228,313,698|
| Conservative admission estimate |4,526,793,263|5,454,500,450|
| Import/update elapsed milliseconds |3,973.244|6,513.019|
| Post-operation PSS KiB |30,065|33,909|

Precommit measurements include the still-present input archive, saved model, reviewed small packs and diagnostic fixtures. They count logical file bytes at a transaction boundary, not a continuously sampled filesystem peak. New bytes count streaming writes promoted into shared storage, not only bytes simultaneously in a temporary directory. The provider-copy allowance deliberately double-counts an incoming archive already under app files in this test. The input archive was then removed from the emulator, with exact originals retained on the rig. The city database resolves to the same content object before/after; the new delta does not carry it. No complete edition copy was made.

A later distinct process queried the installed two-shard catalog. [All twenty Android city outcomes](full-scale/large-android/large-inspect.json) are preserved: Los Angeles and Mexico City return 30 candidates, while eighteen cities remain empty. Mexico City takes 8,502.4 ms for city lookup plus unfiltered nearby search; source inspection follows separately. This does **not** improve the earlier roughly 8-second latency or establish global Android coverage. Full host results cannot replace these misses. The current actual bulk installation is these two full places shards, not the full inventory and not a full wiki installation.

A separately labelled real-source subset exercises the same importer/readers with Acid and Cooking from different sealed wiki shards and unchanged real place blocks around London/Mexico City. It verifies exact titles, cross-shard diversity, source hashes/inspection, positive city/category queries, absent category, content reuse, corrupt payload rejection, cancellation before/during copying, changed/missing shared objects, interrupted staging, removal/reclamation, same-process retry, active selection and separate-process reload. Constructed manifests/subsets are test assets, not additional corpus coverage. No generated answers are counted.

For the measured small wiki update before the final restart/removal extensions, retained bytes grew from 74,702 to 138,598; observed precommit bytes were 139,459 and new writes 64,756. Cancellation operation time was 9.807 ms, including unwind/cleanup; this is not a stalled-provider or OS cancellation guarantee. The [preserved intermediate receipts](full-scale/android-before-process-restart/android.json) and final required-check receipts distinguish each execution. Real two-city subset operations took roughly 17–24 seconds including category filtering and source inspection; they are not a speed claim. Source block extraction retains raw record hashes and scope.

The saved model remains Qwen2.5 0.5B SHA `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`. Production configuration and Android inference admission are unchanged; selected4B is still host-only. No new inference was necessary for this storage/retrieval task.

## Joint budget and exact remaining gate

[Budget arithmetic](full-scale/budget.json) conservatively adds the audited full data inventory to the measured release-v5 app-files baseline and new APK: 41,628,740,516 bytes. One same-sized replacement of the largest wiki shard, retaining old content and one provider delta copy plus allowances, estimates 44,797,067,832 bytes. This is below the 45 GB target under its declared assumptions; unknown provider caches, filesystem overhead, multiple updates, auxiliary integration and a selected-model change can invalidate it. The largest shard is 1,516,530,506 bytes. Real two-shard measurements above do not validate a full 41+GB installed system.

**External dependency:** coordinator-approved Android/emulator storage sufficient for the complete installed inventory plus bounded incoming update, with enough free reserve. This task is not authorized to resize/restart the existing emulator. Once provisioned, progressively install the sealed manifests/deltas, verify every object and query all frozen cases, then measure a full-inventory shard replacement including actual allocated disk/temp/cache and memory. Do not accept a host manifest or a supplied success flag as that measurement. The verifier currently fails explicitly at this unmeasured gate.

Rig follow-up remains useful-answer/source-rights integration under the existing task302 and answer-architecture work; no duplicate tasks or orchestration state were written. This application change invalidates release-v5 as a current candidate identity. Exact candidate release checks must be rerun after the pending scale/model integration; historical release manifests remain unchanged. Physical Android/GrapheneOS, selected4B qualification, independent clean-machine reproduction, production signing ownership, independent unseen matched comparisons and human acceptance stay open.

## Reproduction

1. Read the frozen [public protocol](../../tools/evaluation/full-scale/protocol.json). Reuse sealed lane assets read-only.
2. Run `python3 tools/evaluation/full-scale/audit.py downloads/full-scale/<new-run>` for actual host hashes/counts/queries; it refuses an existing output directory.
3. Build successive collections with `python3 tools/packs/build_shared_scale.py places --shard-limit 1 --output <first.json> --archive`, then `--shard-limit 2 --base <first.json> --output <second.json> --archive`. Wiki uses the same interface. Keep incoming deltas serial; never create a full duplicate edition archive.
4. Build the instrumentation with `bash tools/android-build.sh assembleDebug assembleDebugAndroidTest -PpocketloreTestRunner=org.pocketlore.app.ShardUpdateInstrumentation`. Subset fixtures come from `fixtures.py` and `places_fixture.py`; preserve prior run directories.
5. Required commands: `bash tools/android-build.sh` and `python3 tools/evaluation/verify_full_scale_inventory.py`. The latter checks exact source/APK/test/fixture/run hashes, all sealed bytes, actual installed shared objects, changed/missing copied artifacts, fresh Android behaviors and separate-process reload. It then fails the still-unmeasured full installation gate. Never turn this into a presence-only check or remove that gate to report success.

The [candidate identity](full-scale/candidate.json) distinguishes immutable historical runs from the current implementation. Process-restart and simulated interrupted-stage checks do not prove abrupt power-loss durability at every filesystem boundary; parent-directory fsync/power-cut qualification remains unmeasured. No phone RAM, thermal, OOM, generalization, superiority or product acceptance claim is made.

## Final required-check records

[Required build](full-scale/required-build.log) exits0. [Required verifier](full-scale/required-verify.log) exits1 only after passing its independent checks, with the full-install gate explicitly blocked. [Fresh final Android receipts](full-scale/final-android/android.json) and [separate-process reload](full-scale/final-android/restart.json) preserve the actual final execution. No passing status substitutes for full installation.

Older test-owned subset directories were archived on the rig before scoped removal; the [archive receipt](full-scale/stale-fixture-archive.json) lists exact paths/hash. The production shared collection and original small-pack/model assets were untouched. [Final storage](full-scale/final-storage.json) records app files2,926,780KiB, cache72KiB, code cache8KiB and `/data` used3,757,088KiB at that snapshot. The saved model and small-pack catalog retain their original hashes. These observations include remaining test inputs and do not claim a clean full-scale footprint.

## Repair1: unchanged external storage dependency

The repair branch began at release-v5 rather than at the failed task301 tip. All five task301 commits through `48b607ecf127401686431428116b17bdee27ffee` were recovered in order with normal cherry-picks, without conflicts, resets or branch switches. A Git comparison confirms recovered Android, pack tooling and evaluation code exactly match that preserved checkpoint. No source, fixture, threshold, model or measured failure was changed to manufacture acceptance.

[Fresh environment inspection](full-scale/repair-1/environment.json) finds only emulator-5560 attached, boot completed, with6,082,144KiB total userdata and2,182,820KiB free at inspection. `/storage/emulated` uses the same backing filesystem; tmpfs is RAM, not additional persistent inventory storage. Even deleting all current app data cannot make the complete41+GB inventory fit this filesystem. No user data was removed, service resized/restarted or replacement emulator launched.

[Repair build](full-scale/repair-1/build.log) reproduces APK `a0cebabd78b9246fa5e1272e4bea1587c7ca80e2785fe31f2ee73048a1719de9`. [Required verifier](full-scale/repair-1/verify.log) and [actual exit codes](full-scale/repair-1/check-exits.json) record the fresh required-check execution. These are recovery checks, not a new coverage or quality experiment; no corpus download, query revision or inference was performed. The critic's full-installation/full-update blocker remains unresolved.

The next dependent action requires the coordinator to supply an explicitly approved Android environment with persistent capacity for the complete candidate, a bounded incoming shard and free reserve. Then run progressive full imports, exact installed-object verification, frozen cross-shard/city queries and an actual full-inventory update with allocated disk/cache/temp and memory observations. Provisioning must not be inferred from a repeated repair assignment. The current verifier deliberately cannot mark this gate passed without implementing and executing that full measurement; its preserved host/subset successes are insufficient. No additional repetition of the same small experiment repairs the missing environment. Task301 is blocked, not complete or accepted.

Repair1 actual results: build exit0; verifier exit1 after passing its host integrity and fresh Android subset/reload checks. [Hashed receipt](full-scale/repair-1/receipt.json) and [fresh Android execution](full-scale/repair-1/android/android.json) preserve the run. The full-install gate remains failed for the unchanged external dependency.

## Repair2: fail early on the measured capacity dependency

Recovered all commits through `56a0ff76921749a1a04a562f226a8539d8189a18` on the assigned checkpoint branch; application code and prior raw failures are unchanged. Current inspection still finds only emulator-5560 and the same persistent filesystem. Instead of repeating the rejected subset experiment, the verifier now validates its pinned preflight code/budget, reads actual `/data` capacity and exits before expensive inventory hashing, artifact copies, APK installs or subset execution when total capacity is below the declared candidate plan.

[Capacity evidence](full-scale/repair-2/capacity.json) records6,228,115,456 total bytes versus the41,628,740,516-byte planned candidate. The JSON field `installed_lower_bound_bytes` denotes the required capacity for that declared conservative plan, not a measured minimal encoding of the corpus. Emulated external storage shares the volume. No app data was deleted or service changed. A larger-capacity prerequisite result alone cannot pass the downstream full-install/update gate, which remains unchanged and unmet.

Five [behavioral regressions](full-scale/repair-2/capacity-tests.log) cover the real recorded small filesystem, a larger volume admitting only the prerequisite, exact byte boundaries, malformed/tmpfs/external-mount rejection and ambiguous mount rejection. They run without installing anything. [Required build](full-scale/repair-2/build.log) exits0 and reproduces the unchanged app SHA; [required verifier](full-scale/repair-2/verify.log) exits1 at the new preflight, with [actual exits](full-scale/repair-2/exits.json). No host/subset tests or inference were rerun or counted as new coverage. The prior candidate manifest is preserved before adding the new verifier/helper identities.

This is a bounded verifier repair, not resolution of task301's product objective. Coordinator-approved persistent Android capacity and subsequent actual full installation/update observations remain necessary. Repeating task301 in this unchanged environment cannot supply that evidence. No orchestration state, branch switch, push, main advancement, publication or private holdout access occurred.
