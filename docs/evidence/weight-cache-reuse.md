# Native owned cache reuse: bounded synthetic qualification

The required Android build and `check_weight_cache_reuse.sh` pass. This qualifies a linked native policy and bounded synthetic controls only. No actual model header, hash, slice, payload, mapping, advice, load or inference occurred; no device command was issued.

## Implementation and frozen rules

Accepted535 e8eefab remains the native ownership/random-fault base. Useful536 supervisor/validator source was selectively recovered from failed cae17c4 without importing its acceptance packet or generated files. Its wall-timeout failure remains unchanged. Native source checkpoints20c973f,089a6c2 and562023e implement the separate opt-in policy; subsequent checkpoints freeze and repair evidence handling.

`File::enable_budgeted_cache` requires a dedicated verified readonly random-policy owner before mapping, rejects unsupported budgets and preserves ordinary JNI/default admission. The future exact-asset diagnostic flag `--exact-sparse-budget-diagnostic` selects a fixed2GiB ceiling. The existing force-drop diagnostic remains available and the current536 runner still selects that old route; no model dispatch was added. Actual `scalar_step` synchronizes completion and releases its reader before invoking `File::advise`, which now dispatches to force-drop or bounded reuse.

The frozen synthetic ceiling is8MiB, chunk1MiB, bookkeeping ceiling4MiB, at most two cyclic map sweeps and five seconds, with both the original operation deadline and final elapsed-time check. Full current mincore and verified readonly mapping geometry precede decisions. At or below budget, no DONTNEED is issued. Above budget, only owned chunks containing cached pages are advised; residency is remeasured and unresolved budgets fail closed. Cursor state resets on registration, including smaller remaps. The partial final page uses kernel page rounding for advice and preserves logical byte boundaries; a1056-byte-short tail mapping is independently exercised. No weights, experts, anonymous/transformed buffers or source content are removed or classified as disposable.

Cache observations retain budget/policy/cursor, before/after residency, observed reduction, advised bytes/calls, monotonic interval, minor/major faults and explicit failure. Mincore observes file-cache residency, potentially shared across processes; it is not exclusive charge attribution or an aggregate memory entitlement. A syscall return alone does not establish an eviction effect.

## Actual frozen comparison

Two new32MiB files share exact deterministic bytes and begin independently cold after own-file verification/advice. The fixed sequence reads4MiB, repeats it, reads12MiB of disjoint pages, reaccesses the first4MiB, reads16MiB elsewhere and reaccesses4MiB. Every accessed byte is checked, not just a counter or checksum declaration. Timing includes bounded snapshot/inspection overhead and is one deterministic development sequence, not a benchmark distribution.

| Phase | Force major faults | Reuse major faults | Force ms | Reuse ms | Reuse after boundary | Reuse advice calls |
|---|---:|---:|---:|---:|---:|---:|
| First4MiB | 1024 | 1024 |25.145|37.368|4MiB|0|
| Repeat4MiB |1024|0|25.855|2.795|4MiB|0|
| Pressure12MiB |3072|3072|74.246|96.771|8MiB|8|
| Reaccess4MiB |1024|1024|25.457|37.994|8MiB|4|
| Rollover16MiB |4096|4096|98.494|100.219|8MiB|16|
| Final4MiB |1024|1024|24.979|26.157|8MiB|4|

The repeat begins with1024 verified cached pages under reuse and zero under force-drop. It has zero unnecessary advice and zero major faults. Pressure boundaries reach the fixed8MiB ceiling; cursor positions0,0,8,12,28,0 demonstrate deterministic progress and rollover. Reaccess remains byte-correct after eviction. Several nonrepeat phases are slower with reuse: no general speed superiority is claimed.

Current native controls also pass partial-tail and smaller-remap safety, real child-local seccomp failures of mincore/advice, and successful-syscall/no-effect injection that refuses after bounded passes. Existing current-linked ownership controls cover identity/hash/size/ranges/alignment, absent maps, aliases/readers, cancellation/expiry, exceptional callbacks, deferred teardown, random-policy setup failures, dedicated-description independence and double ownership. Owned hung/read-error workers are reaped. Thirteen corrupted-packet cases fail against a genuine current positive; altered raw bytes are re-encoded consistently so semantic checks must reject them. Namespace/source/PID/startticks, exact VMA/mount/readonly identity, byte sums, mincore/counter consistency and chronology are independently checked.

The initial force native run succeeded, but collection failed because the inherited supervisor combines stderr into stdout and does not create a separate stderr file. That complete failed attempt remains retained. Collection was materially corrected to explicitly preserve the combined stream, with invalid-UTF8 and unreadable-file controls; a separately recorded attempt reused the unchanged frozen pattern and native policy. No guard or file was deleted or overwritten. Total newly created fixture content across both attempts is196MiB, below256MiB; the new attempt has132MiB. Initial unused and superseded input freezes remain distinct. There was no adaptive budget or timing selection.

## Resource and linked-build evidence

The reuse process sampled RSS maximum25407488B and PSS22254592B; synchronous native snapshots report HWM30072832B. The larger HWM is retained, not replaced by sampled RSS. Force RSS/HWM21692416B and sampled PSS18501632B are separate observations. Maximum sampled supervisor current across the seven native policy runs is2832748544B; lifetime peak3403882496B includes earlier builds/tooling and is not each process's memory. Swap is zero. Raw status/stat/smaps/mincore, file/mount/namespace identities, current/peak/events and per-phase CPU/fault timing are embedded.

Supervisor9GiB/swap0/CPU200/four affinity CPUs/Tasks512 and fresh host-availability observations remain host containment only. The native policy's2GiB clean-page ceiling is inside the unchanged future7.5GiB aggregate stop,9GiB supervisor and12GB device requirements; it cannot guarantee aggregate fit. The original150/160CPU,180s,context1024/thread2/output128 and original two prompts are unchanged.

Both Android ABIs, host CLI, lifecycle/fault/reuse controls and packaged APK link successfully. Repeated same-input builds after normal checkpoints reproduce all seven hashes, with exact ELF machine and16KiB Android LOAD/ZIP checks. Actual Android runtime remains unexecuted. The shared pinned checkout is unchanged; isolated derivations truthfully identify upstream bb4caa754 plus modified input identity.

* Host CLI: `0554c8678739846fd919d63b9196d6f6ed4817d544e57d1492091ae815914f53`
* Reuse controls: `c4642016786602b4e69c96ab5e3a445959cb6314dc891d5cd8b11dea4f893a93`
* ARM64: `377ccd80fa17ee1a582a021e7308f8b9083192e1103a443d8b07fda888190918`
* x86_64: `645af126a9ff01ee26396c938291cbd56139251769b948c08067420607505e52`
* APK: `488ec0e01fc137a7339175efbc470b0dc0ba936ec1d32aff5d1ad1aa309e8566`

The declared review JSON freezes source text, exact configuration/derivation/executable/input versions, raw positive and failed attempts, final build/check logs, historical536 independent failure packet and independent criticism. Generated binaries/build trees/fixture data remain in ignored downloads. There is no new dependency or license substitution.

## Historical failures and unqualified gates

536 remains a180-second timeout after14/379 prefill steps, zero output and case2 unrun: sampled aggregate2859622400B versus kernel lifetimepeak2861633536B, processRSS/HWM1948565504B and CPU79.5s, swap/OOM0. Its5952290 process major faults and force-drop source support churn investigation, not a sole storage/readahead bottleneck diagnosis.531/534 failures, guards, costs and raw source identities remain retained; current synthetic success does not relabel any generation failure.

No model throughput, complete working-set fit, first-token latency, useful explanation/comparison/synthesis, entailment or competitive quality was measured. Original500/524/531/534/536 useful-generation, actual Android JNI/UI/cancel/reuse/restart/noGMS, physical12GB, full-source admission and45GB target/50GB complete installed/provider/temp/update/rollback, human and unseen matched rival gates remain open. Any future changed-model screen requires separate review; this checker never launches one.

Independent criticism: The packet supports bounded synthetic reuse, pressure eviction, remap safety, and 13 corruption refusals, with lower repeat-access faults in this fixture; model throughput, full working-set fit, generation quality, and Android behavior remain untested.
