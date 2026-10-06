# Indexed original-wikitext search

Task542 adds a separate version542 engineering capsule and `tools/packs/current-xml/indexed.py` CLI. Exact Unicode-scalar trigrams are stored as UTF8 BLOB dictionary keys with WITHOUT ROWID postings. No normalized text or second whole body is stored. Queries use bound SQL parameters, seed candidates from the rarest gram, intersect all query grams and verify each candidate against the unchanged original text. The actual accepted541 behavior is preserved: body before title, first occurrence, one result per revision, stable page/revision order and half-open UTF16 source ranges.

Queries shorter than three scalars are explicitly refused. A search examines at most256 seed candidates and returns at most20 hits; incomplete results carry a query/output-hash-bound continuation cursor. There is no hidden whole-capsule scan fallback. Inspection and exact original export inherit the unchanged541 source/hash contract. SQLite3.53.4 B-tree capabilities and actual covering-primary-key query plans were observed; this is not a claim about Android FTS5 availability.

## Checks and provenance

`bash tools/android-build.sh` passed, with APK SHA256 `d2149c550e2d2088cc1919de18bdc01e6bebb54d734954cbb228bf709e1ea377`. `bash tools/evaluation/check_indexed_xml_search.sh` passed as `PASS_HOST_INDEXED_ENGINEERING_ONLY`. The checkpoint lineage is accepted541 `06d7ced` → initial542 `5c4cc8d` → repaired542 `167f67e` → final evidence checkpoint. No branch/main/push, archive, model, device or unrelated service operation occurred.

The CC0 fixture,8192 records (each title+body <=512UTF8 bytes), exact algorithm, five-query order and ten trials were frozen before timing. The same input files were reused read-only across correctness repairs, never regenerated or tuned from timing outcomes. Final trials use current code; the performance index artifact was reused only after exact unchanged adapter/index-builder/fixture hashes and its database hash matched. Its older build receipt remains identified as historical, rather than being relabeled as a current supervisor run.

Independent pre-derivation review found and repaired a stale SQLite progress callback, weak derivation/mutation bindings and cleanup that depended on fallible procfs reads despite holding a pidfd. Current controls include an aged-reader positive, transaction cancellation/deadline and owned input-race refusals, six actual corrupted child databases, five query-receipt mutations and eight worker-receipt mutations. Genuine positive baselines precede the mutations. Hung-worker TERM→KILL/reap and initial-stat/collection failures exercise actual owned cleanup; raw streams and failed staging remain retained. Prior summary logs and build/control receipts remain distinct; only final trials provide current query timing evidence.

## Frozen host query measurements

Ten warm repeated trials per query, fixed legacy-then-indexed order; query time excludes reader-open validation. Nearest-rank p95 is the largest of ten observations. These are self-baseline host measurements, not cold-storage, UI, device or rival benchmarks.

| Literal query | Legacy p50 / p95, ms | Indexed p50 / p95, ms | Legacy / indexed decompressions |
|---|---:|---:|---:|
| `LateNeedleZXQ` | 185.857 / 194.234 | 0.104 / 0.232 | 8192 / 1 |
| `AbsentNeedleZZZ` | 186.202 / 194.577 | 0.018 / 0.022 | 8192 / 0 |
| `Common source` | 0.543 / 0.554 | 0.963 / 0.994 | 20 / 20 |
| `😀é` | 0.523 / 0.582 | 0.686 / 1.215 | 20 / 20 |
| `(OR "quoted")` | 0.512 / 0.651 | 0.939 / 0.984 | 20 / 20 |

All50 results matched the legacy reader and independently authored exact-string oracle. Rare/absent queries avoided full-body scans; frequent queries were slower, and no parameter was tuned to hide that result. Combined open/hash/index validation for both readers took **1.229448937seconds**, separately from query timings. Startup validation scans index structures, though it does not decompress original bodies; a warm-query gain does not establish a fresh-open latency win. Raw CPU, major/minor faults, candidates, decompressions and decoded-byte counts are in the review artifact.

## One derivative of the accepted prefix

Exactly one new indexed capsule was derived from the existing541 database, SHA256 `1c58d27e72af460b549f868a1d2ce72401281400e322c4825aaf44aa20629daf`. The XML archive and its attempt guard were not opened or modified. All256 complete original record rows—including metadata and lexical BLOB bytes—were compared exactly, with independent text/lexical/metadata hash manifests and source-open/export checks. Input inode/version and complete database hash remained unchanged.

The resulting database is **22,110,208bytes**, SHA256 `5cff5b277f6bc151a2eb1719f262ee49c449d8f0e4e9024c307796e874adbef1`, with **126,205 terms** and **1,255,814 postings**. Build time was **10.062070531seconds**. Original source BLOB bytes remain **4,116,933**. Database page accounting records13,578,240 posting bytes,1,953,792 term-table bytes and1,703,936 term-key-index bytes; other schema/source/metadata/order indexes are enumerated separately. The original database was4,804,608bytes: this index has a substantial measured storage cost, without a whole-corpus projection.

The actual derivation worker had39 live samples bound to PID7/startticks50801505, stable namespace/source/interpreter identities, exit0 and confirmed reap/absence. Sampled worker RSS/PSS maxima were36,995,072/28,012,544bytes. Sampled supervising current was966,066,176bytes; the distinct cgroup lifetime peak was1,434,017,792bytes. No new sampled swap/OOM/max event was observed. Host9GiB/swap0/CPU200/four-CPU/Tasks512 containment is not device12GB qualification.

At the inventory observation, all retained task files totaled113,321,963 logical bytes, including earlier builds, failures and race fixtures. The primary fixture inputs totaled13,287,424bytes; small owned race copies are separately listed. A per-index64MiB cap and120MiB task-directory polling guard reserve8MiB for bounded logs/review under the128MiB task budget. **Individual transient journal/temp byte peaks were not separately sampled**; the guard is not an exact filesystem high-water measurement. No installed/provider/update/rollback profile is thereby qualified.

## Independent criticism and limits

The packet supports exact 256-record preservation and selective-query gains, while frequent queries remain slower; local replay dependencies and unmeasured temporary-storage peaks limit reproducibility and resource claims, with Android behavior unqualified.

The reviewer independently verified242 envelopes in packet `33f42974508303c94e641d96a3bd717985be19ef656b9870ea2d6cf1114ac31e`, both database identities, all256 original rows/hash manifests,50 trial results and the actual derivation worker. The final packet additionally freezes that criticism, resource/storage accounting and check logs without changing executed inputs. It excludes bulk SQLite databases and the APK from Git; complete replay requires the explicitly hash-bound local fixtures/capsules/mutants/APK. The reviewer accessed only those bounded artifacts, not the archive, model or device.

This qualifies host indexed engineering only. Original wikitext remains inert, unrendered and rights-unreviewed; no source-pack admission, whole-archive/latest census, >=1.25M eligible full articles, full50GB/45GB target installed/provider/temp/update/rollback fit, useful model output, physical12GB/no-GMS/Android runtime or unseen matched rival result is claimed. The26.9GB host archive and12.29GB model remain separate future profile liabilities. No automatic producer, model screen or device action follows.
