# Complete-source production safety

This is a host engineering milestone, not full-source admission. The revised single-worker producer preserves the accepted compact codec and engineering check. No Android candidate, model, original source job, service, orchestration state or main branch was changed. A long production job has **not** been launched: the user bus returns `Failed to connect to user scope bus via local transport: No data available`. The frozen launch specification requires fresh parent-coordinator preflight and actual child-cgroup enforcement; it is not a successful launch receipt.

## Frozen scope and architectural changes

The readiness packet reviewed the exact executed 12,000-record prototype, SHA256 `644d84c9f3c639327a92bed08719fe7b6656ab6af52e269a9946e937516b5c9b`. Its critique is retained verbatim alongside its manifest. Later accepted tests and the Reader-only change also exist; their absence from that older packet does not invalidate them. The original `compact.py` and engineering acceptance check remain unchanged.

The separate `production.py` replaces the fixed 300-CPU-second policy with explicit short (at most 180 seconds) and long modes. Both apply a wall/absolute deadline, CPU limit derived from remaining time, one-core affinity and 384MiB address-space limit. These are process limits, not total-memory proof. Long mode additionally refuses to run unless its actual cgroup enforces MemoryMax at most512MiB, swap0, CPU at most400%, and TasksMax at most32. The selected launch specification uses100% CPU and one worker. No four-worker pool is qualified or promised to scale linearly.

SIGTERM, SIGINT, SIGXCPU and wall alarms retain failure receipts and the committed sequence. A ten-second emergency alarm bounds stalled cleanup but may preclude a final receipt if the process/kernel/filesystem cannot make progress; prior durable status and the external journal remain necessary. An external cgroup OOM kill likewise cannot be guaranteed a Python cleanup receipt. The parent must retain its unit exit/journal and never infer success from an interrupted status.

Originals are fetched in at most64-row batches, stopping after8MiB compressed input, plus the last bounded record. The source connection closes before parsing. Every raw digest, staged identity, license list and metadata status is verified; a final pass rechecks every original binding without one long source read transaction. Prefix mode requires its exact final sequence; follow mode waits for contiguous committed records and matching whole acquisition/staging receipts. A partial prefix cannot establish complete archive coverage. Per-record malformed JSON/metadata, invalid rights, unsafe transformations, oversized originals and revision conflicts remain counted. Conflicted or unverifiable pages stay quarantined rather than reviving an earlier safe revision.

A run-level nonblocking file lock now covers creation/resume, status updates, database work, rollback and final hashing. Independent review found this missing in the first safety checkpoint; its critique and pre-lock measurements are retained. SQLite transaction locking alone was insufficient. Explicit resume is allowed only for a committed ingest boundary with unchanged code/configuration; interrupted finalization cannot silently replay. There is no automatic retry.

The output stores one article capsule per page, not duplicate candidate/final body tables, and does not run VACUUM. SQLite progress handlers cover indexing and integrity work; parsing checks source tokens and nesting, and file hashing checks each1MiB chunk. Disk checks retain100GiB free plus512MiB write margin. Page/freelist counts, owned logical/allocated files and open SQLite temporary descriptors are sampled. Samples are not continuous peaks or whole-host accounting; the original archive, staging database and its live WAL are reported separately. Concurrent external writers can consume free space between samples; no reservation over unrelated host writers is claimed.

## Validation and reconstruction

The frozen protocol predates implementation. Constructed controls exercise cross-batch late/unsafe/conflicting revisions, malformed records/metadata, oversized originals, changed source snapshots, disk-reserve refusal, missing cgroup limits, WAL checkpointing, explicit restart, finalization restart denial, and incomplete-archive/no-promotion gates. Deterministic deadline controls expire inside SQLite progress and after a hash chunk, as well as parser/phase boundaries. These are injected development controls, not naturally exhausted CPU or disk. SIGTERM and SIGXCPU are separately delivered to actual owned subprocesses; no disk is filled.

A real six-thousand-original prefix, interrupted and explicitly resumed, is compared against all5,944 frozen engineering article identity/capsule hashes. Thirty-two deterministic article samples include records beyond5,000; their original JSON/HTML bytes are bundled for an independent byte/UTF16 oracle. Three preserved real4.0-license originals supplement the all3.0 prefix without inflating its counts. The oracle compares literal source slices, decoded entities, explicit separator/break transformations, raw/HTML hashes, dates, revision URLs, contributor-history links and exact license identifiers/URIs. Original HTML remains retrievable from the retained host stage; it is not embedded in the Android product. Math/table/media exclusions and review flags remain visible, not silently cleared.

The first fine-grained FTS interruption fixture was too small to reach SQLite's1,000-op callback; that failing test/log is retained. The strengthened fixture uses500 constructed records and demonstrates callback interruption. It does not count as factual coverage. Required check logs and exact statuses, process commands, source hashes, immutable SQLite identity, signal failures, concurrency rejection, source samples and sampled storage are listed in the JSON review packet.

## Actual bounded result

The final lock-protected invocation is `actual-20261006T004628Z`. Its SIGTERM stop retained sequence63; the one explicit manual resume completed sequence5,999 in63.027seconds; the separate delivered SIGXCPU stop also retained sequence63. Both signal exits are1, completion exit0. A concurrent resume returned1 with “owned producer already active” while the owner remained running. These injected signals are not a claim that a real kernel CPU exhaustion or OOM was observed.

| Measurement | Actual host observation |
|---|---:|
| Original records / transformed distinct articles | 6,000 / 5,944 |
| Passages / blocked pages | 15,752 / 55 |
| Dispositions | 5,944 transformed,55 excluded,1 superseded |
| Final compact SQLite bytes | 47,538,176 |
| Unused SQLite freelist bytes retained | 655,360 |
| Peak process RSS | 54,317,056 bytes |
| External storage samples, requested50ms interval | 1,255 |
| Largest sampled rollback journal | 1,207,088 bytes |
| Largest sampled top-level owned allocated bytes | 47,759,360 |
| Final producer-owned allocated sample including event receipts | 47,685,632 |

The external sampler includes the active SQLite journal and transient status file but not the event subdirectory; the producer's final sample includes events. The maxima have different scopes and are not combined into a fabricated continuous peak. No output WAL or VACUUM temporary copy was observed/used. Original-stage WAL size is separately captured in host-preflight; only the constructed independent writer/checkpoint control establishes no pin from our returned batches. It does not attribute the live external WAL size to this reader.

Only40 prefix articles lack transformation-review flags; none is rights-admitted. All5,944 article identity/capsule-hash tuples match the prior frozen oracle. The source snapshot at the refreshed preflight remains provisional and is recorded byte-for-byte, not promoted using its raw record count. The full-source job has no active handle. The launch spec's1worker/100%CPU/512MiB/swap0/32tasks policy must be externally enforced and freshly measured; the current parent cgroup is unbounded and does not qualify.

Both required commands pass for the explicitly classified engineering result. The original check exercises9 codec,6 transaction tests and its actual source packet. The new check exercises10 constructed safety tests, immutable real subprocess/SQLite/source receipts, and six stale/missing/corrupt/false-admission controls. All pre-lock observations and the undersized FTS test failure remain in the packet. A successful checker does not authorize source admission or imply the blocked long job ran.

## Remaining gates

All source-admission/distribution flags remain false. The1.25M distinct eligible floor and2–3M target, whole original archive identity, all-record eligibility, independent rights/fidelity, full-current-source freshness, Android reader/import/citation/restart/export and complete installed/update45GB target/50GB hard cap remain unproven. Current raw-stage counts are originals, not transformed or admitted articles. The March2025 archive is older than the rival August2025 source; historical equal-revision samples do not establish equal rendered content or eliminate later-revision gaps.

The combined model/places/corpus/provider/staging/rollback budget,12GB physical device qualification, matched quality/speed, unseen evaluation, GrapheneOS, rights and human acceptance remain open. These host measurements establish neither Android behavior nor useful generated answers. The exact next operational step is a parent-launched, freshly checked single cgroup job from the immutable specification, or retention of the blocked result if the source/capacity/deadline preflight fails; source admission remains a separate task.
