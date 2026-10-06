# Task 539: cache receipt semantic repair

The bounded synthetic checker passes the three repaired contracts: parsed kernel events, exact pressure/tail/remap page geometry, and mandatory verified ownership. This is evidence-validator engineering, not model or Android runtime acceptance.

## Scope and preserved history

Accepted task538 checkpoint `410eabce5a18fb0f3616994fa7596588a71a0bd5` remains historical acceptance. Its actual runs did not have OOM or corrupt pages. The independently frozen review demonstrated contradictory *mutated receipts* accepted by its validator. Before editing, all three exact counterexamples were reconstructed and accepted again; the original positive also passed. The retained red packet is embedded in the review artifact.

This repair parses unsigned, complete memory.events counters for the same supervising cgroup before, during and after each run. New failure events refuse at `events-new-failure`; prior cumulative counters are not attributed to the child. Missing, malformed, unknown and decreasing counters refuse separately. A constructed unchanged-history boundary is labeled synthetic, not a real historical kernel event.

Auxiliary snapshots now require sorted unique in-range pages, ceiling-page cardinality, exact logical byte length, offset, read-only VMA geometry and live owner identity. Pressure requires actual touched RSS before injected failure. The non-page-aligned 33,553,376-byte tail remains valid. Remap records independent old 32MiB and new 4MiB observations with cursor reset. Every native auxiliary family requires one correctly ordered verified-owner event; hung/read-error supervisor cases retain their explicit no-native-mapping contract.

## Executed evidence

- Required Android build: exit 0, linked ARM64 and x86_64 production libraries, checked ELF machines and 16KiB LOAD/ZIP alignment.
- Required cache checker: exit 0, current source/binary/derivation bindings, genuine native positive runs and 98 negative controls: 33 new semantic, 52 retained auxiliary/family, 13 basic.
- All 85 recorded auxiliary deltas are reconstructed and rejected at their declared guards; each mutation first revalidates the unchanged positive.
- Forced same-input relinks across checkpoint `d5fb3f4` produced byte-identical hashes for all six native artifacts. The packaged APK SHA256 is `d2149c550e2d2088cc1919de18bdc01e6bebb54d734954cbb228bf709e1ea377`.
- Final native receipt directory: `downloads/cache-semantic-539/named-pid-guard`; complete raw bytes, frozen inputs, build logs, mutations and hashes are embedded in `cache-semantic-repair-review.json`, not supplied only as external paths.

The actual supervisor is the dedicated pocketlore-cache-semantic-20261006.service cgroup, with 9GiB memory, swap0, CPU200%, four affinity CPUs and Tasks512. Fresh heavy-phase availability checks required at least11GiB. Current/peak supervising memory, process RSS/PSS and global mincore file-cache residency remain distinct quantities.

## Repairs and failed collections retained

The first collection hit a real process-exit race reading smaps_rollup after an exit0 native refusal control. Its failure and cleanup survive. The collector now records the original read exception and confirms direct-child exit within a bounded wait; it does not fabricate a final process sample. Two subsequent checker failures exposed a superseded marker guard and an unnamed PID guard. Both failed packets survive; the strict parser replaces the marker and the existing PID rejection now has a stable name.

Fresh current-source runs followed each material code correction. Immutable fixture bytes were reused without deletion or reseeding. Total new task fixture bytes are204MiB (64 +132 +4 +4), below256MiB; no file exceeds128MiB. The frozen per-complete-fixture-set132MiB description is not a claim about cumulative task allocation. Cache algorithms, access patterns, <=8MiB fixture budget, <=2GiB future ceiling, ordinary JNI admissions, prefetch/repack and force-drop behavior are unchanged.

## Independent criticism and limits

The independent reviewer reconstructed the exact OOM-kill, duplicate-pressure and missing-tail-verification deltas and checked all33 named guard replays against the immutable positive packet; its hash and statement are retained in the JSON.

The packet supports repaired event, pressure-page, and verified-owner contracts with 33 targeted refusals and 52 prior replays, while bounded synthetic evidence establishes neither full-model behavior, useful generation, nor Android acceptance.

No model bytes were opened and no device was accessed. The terminal emulator remains untouched. Full-source admission, useful generation, Android JNI/UI and lifecycle, physical12GB/noGMS, complete50GB installed/provider/temp/update/rollback and unseen comparative gates remain open. No model dispatch or main advancement occurred.
