# Multi-pack library — task 200-multi-pack-library

2026-10-01, LLMRig. Both task checks pass on the existing **API 35 x86_64 emulator-5560**. This is builder evidence for a durable offline collection catalog, combined retrieval and source inspection. It does not establish generated-answer support, physical Android/GrapheneOS acceptance or broad research coverage.

## Product behavior

The Activity now retains content-addressed pack archives in `files/pack-library` and commits a small active-selection catalog atomically. Import adds an active collection rather than replacing the reference edition. **Choose collections** selects which editions are searched; **Reload library** reconstructs the active index after memory release. Selecting none produces an explicitly empty library, not an unexpected starter fallback. With no imported collections, the bundled starter remains available.

Existing `knowledge.plpack` is verified and migrated once without deleting or rewriting it. Import stages are copied/fsynced, verified, admitted and indexed before archive/catalog commit. An interrupted operation preserves the prior catalog; a crash before catalog commit can leave an unreferenced archive, cleaned only inside the app-owned catalog directory. Saved models are not modified. Process restart is tested; sudden power-loss/filesystem durability is not proven.

Identity is `p<full archive SHA-256>_<original passage ID>`. Reimporting identical bytes is idempotent. Distinct valid editions with the same display ID remain separate. Original document/passage identifiers, raw-source and passage hashes, dates, URLs, rights and immutable edition hashes appear in source inspection. Duplicate text is indexed once only when source URL/raw hash and all displayed passage metadata match; every contributing active edition remains listed in provenance. Different snapshots or rights remain distinct. The first active edition in catalog order supplies the canonical indexed citation; disabling it may expose another edition's stable citation, rather than pretending those editions are identical.

The existing source packs remain byte-for-byte unchanged and retain their licenses. Historical pack notices that describe replacement behavior are labeled as older-version notices, followed by the current retention behavior. Source-dialog titles use readable document titles; the full citation and hashes remain in scrollable details. Collection switching clears stale answers and citation links without marking inference permanently busy. Merely hiding the UI for Android's document picker is no longer treated as a low-memory event.

## Frozen cases and real coverage

[Protocol](../../tools/evaluation/multi-pack-library/protocol.json) was committed in **064d4e6** before implementation. It freezes cross-pack queries, disabled collections, exact and same-document duplicates, conflicting IDs, corrupt/cancelled imports, combined admission, restart, low-memory reload and actual controls/source dialogs. Mutation fixtures retain licensed factual text; duplicate-edition and whitespace-padded-manifest fixtures are explicitly test-only, not additional corpus.

| Real edition | Archive SHA-256 | Bytes | Documents | Passages |
| --- | --- | ---: | ---: | ---: |
| English reference 2026-10-01 | `567e9bbbaab896826809ec20f81ae1c4b3f421b011931edae0989d28cfce10ea` | 159327 | 10 | 186 |
| Science supplement 2026-10-01-v1 | `c69f31299553f4a1168eaa0400129fd5e41f21b4354248a0e2b97a87546ff274` | 31183 | 8 | 24 |
| Active combined catalog | Separate licenses/provenance retained | 190510 | **18** | **210** |

There are 18 distinct source URLs and 18 distinct URL/raw-hash document snapshots in these two editions. Coverage remains narrow: water science and introductory genetics/geology/geomagnetism, a small historical reference, practical outdoor material and dated park travel guidance. Combining them does not add new facts, cities, live availability or routing. Attribution remains in the original notices and pack manifests; no new third-party dependency or factual source was acquired.

## Bounded admission and measured costs

Task 170 observed 13,764 repetition-only passages, 4,429,788 text characters and 444,074 postings with a 42,688,512-byte incremental Java heap observation. Its vocabulary was only 1,770 terms, and it did **not** prove that two maximum-size diverse indexes fit simultaneously. This implementation therefore uses lower combined ceilings, not per-pack multiplication:

- All retained editions, active or inactive: at most **8 collections**, **16 MiB archive bytes**, **16 MiB expanded bytes**, **2 MiB manifest bytes** and **1000 document entries** in aggregate.
- Active deduplicated index: at most **5000 passages**, **1,000,000 text characters**, **200,000 title/text token occurrences**, and separately **1,000,000 provenance characters**. Token occurrences conservatively bound postings. Duplicate aliases also consume the provenance budget.
- Before the single combined index is allocated: estimated additional heap is `16 MiB + 256 × token occurrences + 4 × text characters + 4 × provenance characters + 2048 × passages`, with a **32 MiB free-heap reserve**. One collection request may reclaim short-lived verification garbage before rechecking. This is a conservative admission estimate, not an allocation/OOM guarantee; available heap is measured while the old live index can still exist.
- There is no retained per-pack index plus combined index. Archive verification runs without constructing individual indexes. The Activity swaps the new immutable combined index only after success. Import requires stage space plus the existing **256 MiB filesystem reserve**. Stage allowance is at most one additional 16 MiB archive; a retained legacy pack can add up to another 16 MiB outside the catalog budget. There is currently no collection-removal UI; inactive collections still consume retained-storage limits.

The actual catalog has **2052 vocabulary terms, 6922 postings and 69,818 passage-text characters**. Combined manifests occupy **47,170 bytes**; total expanded pack entries are **190,062 bytes**. The catalog file is **368 bytes**. Archives plus catalog are **190,878 bytes**; including the untouched 159,327-byte legacy reference gives **350,205 bytes**. Indexes are rebuilt in memory, with no persistent index disk cache. Test archives and screenshots are isolated project fixtures and excluded from product-library counts.

Science import through the Activity took **232.351 ms wall time**, including the monitored framework picker result, validation, indexing and UI readiness; this is not isolated parser time or a performance SLA. Memory snapshots are whole-process observations with the native model deliberately unloaded through its real control:

| Phase | PSS KiB | RSS KiB | VmSwap KiB | Java used bytes |
| --- | ---: | ---: | ---: | ---: |
| Reference before import | 114453 | 199020 | 22360 | 5321888 |
| Both collections ready | 108719 | 193600 | 22360 | 7238064 |
| New process, both re-enabled, before trim | 120084 | 205780 | 22620 | 45435040 |
| Immediately after trim callback | 120519 | 206392 | 22620 | 45530304 |
| Active catalog reloaded | 83729 | 170328 | 22104 | 6339040 |

Java max heap was **201,326,592 bytes**. These are snapshots, not sampled peaks or exclusive index allocations. Garbage collection and process history explain why immediate Java/PSS values need not fall when references are released. No host memory was exhausted and no injected callback is described as OS OOM safety.

## Actual Android evidence

[Exercise record](multi-pack-library/measured/exercise.json) and [restart record](multi-pack-library/measured/restart.json) retain raw retrieval hits, visible dialog text, answer routes, memory values and negative results. The two instrumentation invocations use different PIDs. Airplane mode was on, Wi-Fi/data disabled, and no research network permission or network inference was introduced.

- Both real editions are imported/retained. The query **“magma headlamps”** retrieves hits from both collections in one ranked result. Separate frozen queries inspect science and reference documents through actual source buttons.
- Actual collection checkboxes and Apply are exercised. Disabling science yields **1 of 2 active, 10 documents, 186 passages**. That disabled selection survives a new process. Re-enabling science restores **2 of 2, 18 documents, 210 passages**.
- `adb shell am send-trim-memory org.pocketlore.app RUNNING_LOW` delivers the real Android lifecycle callback. The test waits for the live index to become null, taps **Reload library**, and inspects the same stable science citation after reconstruction. This is a platform-delivered trim test, **not naturally occurring memory exhaustion, low-memory-killer or phone evidence**.
- Every reported source's text, URL, date and rights is compared independently to the pinned pack row; raw-source hash, original citation and edition hash must match the original manifest. [Science dialog](multi-pack-library/measured/science-dialog.png), [reference dialog](multi-pack-library/measured/reference-dialog.png), [collection controls](multi-pack-library/measured/collections-dialog.png) and [reload dialog](multi-pack-library/measured/reload-dialog.png) preserve actual screens. Source text is selectable and scrollable; URLs are provenance labels, not opened websites.
- The real import button requests Android's picker; an `Instrumentation.ActivityMonitor` intercepts exactly that request and supplies the pinned fixture URI through the framework Activity-result path. The final catalog test exercises the production controls/ingestion but **does not browse a live provider picker**. Earlier stalled-provider evidence is preserved separately.
- Identical imports do not multiply editions. A same-document edition and a distinct valid same-name edition preserve aliases without increasing 210 indexed passages or 18 documents. Changed bytes under a stale source ID/hash and invalid ZIP reject; both cancellation before copy and after the first short read preserve catalog bytes and clean staging. Cancellation observations were **0.474 ms** and **0.589 ms** in this deterministic fixture, not arbitrary provider latency guarantees.
- Two individually valid reference manifests padded with whitespace exceed the **combined** manifest budget when retained together; the second is rejected and prior catalog bytes remain unchanged. Eight policy-limit negatives plus the heap-reserve boundary execute directly. These metadata stress fixtures add no factual coverage.
- Saved model SHA `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db` and legacy reference SHA are identical before/after. Only known project catalog editions are archived before deliberate test replacement; unrelated user assets cause the verifier to stop rather than delete them.

The model is unloaded for the retrieval/UI measurements. Actual answers remain explicitly abstained or fallback; the magma question still abstains on the unchanged coverage gate. **Retrieval and citation display are not generated-answer success or an entailment assessment.**

## Checks and identity

```sh
bash tools/android-build.sh
python3 tools/evaluation/verify_multi_pack_library.py
```

Both exit 0. The Python verifier rebuilds deterministic fixtures, builds and installs the actual app/test APKs, runs isolated catalog regressions and production Activity controls, cold restarts the app, requests Android trim, verifies source provenance and unchanged assets, and saves raw receipts. It does not pass based on file presence or self-reported status alone. The existing emulator must already be booted; it never launches or restarts supervision.

App: **11,921,193 bytes**, SHA-256 `2d1588d0f9ddc1227621ad28afe3fcb329f7619599368d9357ac6c10d145b26a`. Test APK: **249,522 bytes**, SHA-256 `001c9b6e32aba7797070dcef8f9b669f328795deed70c01dca8fb662a86bd81d`. Exact protocol, source, fixture and raw-record hashes are in the [measurement receipt](multi-pack-library/measured/summary.json). [Build log](multi-pack-library/android-build.log) and [acceptance log](multi-pack-library/acceptance.log) are preserved. All builds/data processing run on LLMRig; no branch switch, push or main advancement occurred.

## Failures, limitations and required follow-ups

All attempts are retained under [failure evidence](multi-pack-library/failures/), with earlier passing behavior runs under `prior-pass` and `prior-pass-7` (their collection screenshot timing was not yet validated):

1. Startup library load skipped because the saved-model loader was busy; the corrected startup permits independent pack loading without clearing model busy state.
2. Recovery harness assumed an initially empty library directory already had a catalog; it now archives only a verified project catalog or an empty owned directory.
3. Heap admission rejected a small rebuild while transient verification objects awaited GC; one collection request precedes the unchanged reserve check. The rejection was an admission failure, not OS OOM.
4. Accessibility exposes the dialog button as `CLOSE`; matching was made case-insensitive. A later cold-start selection test needed accessibility initialized before Activity launch and readiness checked on the UI thread. Failed screenshots/raw outputs are retained. A later attempted live-picker foreground synchronization stalled because a stale DocumentsUI Activity occupied PocketLore's test-owned task. Two interrupted attempts retain partial reports and diagnostic logs, never labeled complete. The final harness uses a deterministic ActivityMonitor result and launches its own fresh Activity task with CLEAR_TASK; it does not reset app files, unrelated tasks or emulator services. Actual source/collection dialogs are awaited by visible content before capture.

Current corpus remains small; diverse large-corpus transitions, a user-facing collection-removal workflow, power-loss durability and arbitrary provider/OS pressure remain limitations. Saved models and active catalog survive the exercised failures, but this does not close physical <=12 GB/GrapheneOS, sustained-performance or human acceptance gates.

The explicitly required concrete revalidation tasks have been queued as specifications only, with [public copies and receipts](multi-pack-library/follow-ups/queue-receipt.json): **201-multi-pack-answer-revalidation** covers real production JNI, source support/citation links and combined native/index memory; **202-multi-pack-release-revalidation** covers the changed APK/dependency/asset identity and fresh offline candidate flow after that integration. They depend on this task; release revalidation also depends on answer revalidation. No runner state, orchestration, private holdout/context or service supervision was changed, and no task was dispatched. Independent criticism and these follow-ups remain open.
