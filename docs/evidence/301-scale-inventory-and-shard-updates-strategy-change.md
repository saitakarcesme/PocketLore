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
