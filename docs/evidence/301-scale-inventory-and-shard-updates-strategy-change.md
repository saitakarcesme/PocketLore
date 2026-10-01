# Task301 strategy change: stream a bounded Android shard sweep

## Preserved failures

The original shared-object implementation validated host inventory and two installed places shards, but the full 41+GB candidate could not fit the roughly6GB emulator. Repair1 repeated subsets without changing that dependency. Repair2 correctly rejected insufficient capacity early but supplied no additional Android shard coverage. All checkpoints, raw failures and the full-install/update gate must remain intact.

## Materially different design

Use an explicitly labelled **rolling Android compatibility sweep**, transferring each sealed shard through a bounded local ADB/FIFO stream instead of storing a second incoming archive on the emulator. Exercise the actual shared-object importer, native SQLite reader and source inspection for every wiki/place shard in turn, retain shared lookup objects where possible, and reclaim only sweep-owned test content between probes. Preserve the existing installed collections and saved model. Freeze per-shard identities and deterministic probe selection before running the sweep; retain exact hashes, counts, source identities, resource observations and failures. No new corpus acquisition, model inference or source-rights approval is involved.

This changes the validation unit from a repeated small subset to every complete sealed primary shard, without pretending that sequential residency is simultaneous residency. It can establish Android format/reader compatibility across the inventory on the existing device. It **cannot establish full installed coverage, full-inventory cross-shard rank behavior or full-scale update storage peaks**. Those gates still require coordinator-approved persistent storage; no service resize/restart, external mount, replacement emulator or host filesystem substitution is authorized here.

## Discriminating checks

1. First prove local streaming transfer works with an existing real-source fixture, including EOF/failure cleanup and retained model/catalog hashes; do not allocate the incoming archive on Android.
2. Freeze all15 wiki and16 places shard identities from the sealed inventories and source-specific exact probe IDs before Android execution. Shared cities/aliases remain shared objects, not repeated per-shard installed copies.
3. For each full shard, import through the production transaction, verify actual database counts, perform a real indexed query and inspect a source record with its hash/provenance. Record omissions and exceptions as failures, not silently skipped successes.
4. Measure owned retained/new/temporary bytes and process memory during the sweep; compare them separately with the already-preserved two-full-shard update and full-host arithmetic. A rolling sweep must never set the full-install acceptance flag.
5. Keep the required inventory command failing when simultaneous full installation/update evidence is absent. Do not use sequential residency, sparse-file padding, host mounts or preflight success as substitutes.

Execution is initially unvalidated. If local IPC or remaining free space prevents the sweep, preserve the exact failure and stop dependent work without altering services or deleting unrelated data.

## Actual result

The local FIFO smoke check passed, followed by the complete frozen sweep: **15/15 wiki and16/16 places primary shards passed** actual Android import/schema/count verification and their predeclared source probes. The sweep imported6,498,498 article rows and81,455,423 place source rows over time, never simultaneously. Each primary shard was retired before the next; shared aliases/cities remained in a metadata-only collection. The importer now permits an explicitly marked version2 metadata-only collection with zero declared source rows, while rejecting unmarked empty-shard manifests. These empty collections do not confer content or generation rights.

The actual sweep took484.534seconds. Maximum observed sweep-owned precommit storage was1,920,628,479bytes, and maximum post-operation PSS57,414KiB. These are transaction-boundary logical bytes and post-operation memory samples, not continuous peaks, whole-app totals, model-loaded memory or phone observations. Full-shard import timings span3,581.197–25,223.460ms and the deliberately narrow query-plus-inspection probes9.751–530.245ms; they include local FIFO transfer and warm rig/emulator caches, and do not replace the earlier8.5second Mexico City query.

Actual FIFO premature EOF and unmarked empty-shard inputs both failed with their expected error classes and left no committed files in the owned sweep catalog. Saved model, small-pack catalog and original two-full-shard places catalog hashes match before/after. Smoke/shared-metadata fixtures were archived only within the ignored rig run before retiring their owned directories; originals, raw manifests, transfer hashes and source inventories remain available. No unchanged asset was downloaded.

[Raw sweep](full-scale/sweep/run/summary.json), [frozen probes](full-scale/sweep/plan.json), [wiki attribution](full-scale/sweep/wiki-probe-attribution.json), [metrics](full-scale/sweep/metrics.json), [runtime identities](full-scale/sweep/run/runtime.json) and [immutable artifact receipt](full-scale/sweep/receipt.json) separate execution from interpretation. Each shard has its complete manifest, input-archive hash, raw instrumentation output, source identity/preview and filesystem observation. Place records retain original provenance and unknown-hours/diets/routing disclosures. Wiki source-specific rights remain unreviewed; preserving attribution does not clear them. The probes use actual Android readers under instrumentation, not GUI-dialog interaction or new generated answers.

`python3 tools/evaluation/full-scale/verify_sweep.py` passes all31 rows, metadata retirement, negative-stream results, retained-asset comparison and actual changed/missing receipt regressions. `bash tools/android-build.sh` passes with APK `43894babe475f2719f3b2a732755b16860f88bee781fb86b5e99c850cbdb30ee`. The mandatory `python3 tools/evaluation/verify_full_scale_inventory.py` still exits1 at the unchanged capacity prerequisite; [logs and exits](full-scale/sweep/required-exits.json) are preserved. The sweep's actual application/test APKs are hash-matched to the installed binaries and retained in ignored storage; the normal update instrumentation was subsequently rebuilt without changing app identity.

## Remaining dependency, not acceptance

This materially different execution closes the previous **unexecuted-shards compatibility** gap, not the critic's simultaneous-installation/update requirement. It neither reruns the same subset matrix nor lowers the41+GB target. The unchanged6.23GB userdata filesystem still cannot host the candidate. A coordinator-approved larger persistent Android environment is necessary for full residency, combined global queries, full-inventory replacement peaks and allocated disk/cache/memory observations. No service restart/resize, host mount, surrogate physical-device measurement, private holdout, production-model change, publication or main advancement occurred. Task301 remains blocked at that explicit gate.
