# Task370 — bounded verified-source preview caching

The audited production retrieval is lexical, not an embedding hybrid. This task improves its measured reader cost with a bounded verified-preview cache; it does not claim a new semantic model, higher retrieval relevance, supported answers or phone acceptance. Both required commands pass on the existing **API35 x86_64 emulator-5562 with all31 shards installed simultaneously**.

## Audit and frozen scope

`ResearchEngine` uses deterministic weighted postings, existing term expansions, title/opening relevance and distinct source handling; disk-backed bulk `ScaleWiki` uses exact titles, redirects, FTS5/BM25 and round-robin shard ranks. `ScaleWiki.read` streams complete compressed blocks through SHA-256, extracts and verifies one record/text and retains at most64,000 preview characters. Before this change it repeated decompression/hash work on every source reopening. No production semantic embedder was found and none is added without a pinned license/resource/quality comparison.

The actual competitor matrix was inspected at the worker's `repo/output/COMPETITOR-FEATURE-MATRIX.md`, because the requested top-level output directory is absent. Its cache/semantic feature descriptions are static source evidence, not measured competitor success; the source audit's rework, acquisition violation and Git-identity limitations are not resolved here. No competitor implementation or branding was copied.

[Public protocol](../../tools/evaluation/hybrid-retrieval/protocol.json) froze eight literal/paraphrase/cross-topic/invented-token queries and the resource procedure before cache implementation. [Baseline](hybrid-retrieval/baseline.json) measures the actual current corpus and old reader. Selection of the largest raw block is a predeclared resource stress rule, not broader semantic coverage. No held-out cases, model inference, bulk download or new indexing were used. Independent unseen relevance/answer evaluation remains separate.

## Implementation

The process-local LRU keeps at most four verified previews and524,288 accounted bytes. Accounting includes UTF-16 text/key/scope sizes plus1,024 bytes per entry; it is a conservative bookkeeping bound, not an exact heap allocation measurement. No disk cache or full decompressed block is retained. Keys bind edition/shard/article/revision/text identity, record/block checksums, offsets/length, canonical backing path, file size and modification time. A new edition or changed metadata cannot reuse the old key. Warm hits still resolve current block metadata and check cancellation before return.

Only fully checksum-verified record/text results enter the cache. Returned Read objects are copies; callers cannot mutate stored previews. Eviction removes least-recently-used entries. MainActivity and ScaleActivity memory callbacks clear it. Cancellation during decompression still deletes the temporary record. The cache never changes `mayGenerate=false`, source rights, exact offsets, preview truncation, model identity or answer policy.

The key assumes app-private admitted collection bytes remain immutable; it does not rehash the entire backing block on every hit. Deliberate in-place data tampering that also preserves all file metadata is outside this cache's threat model. Collection integrity and immutable update admission remain required. Memory-clear testing invokes the cache clear path; it does not simulate OS OOM or establish recovery from arbitrary process memory exhaustion.

## Actual measured results

[Required build](hybrid-retrieval/build-required.log), [passing receipt](hybrid-retrieval/passing/receipt.json), [raw results](hybrid-retrieval/passing/report.json) and the first cache pass are retained. Current installed APK SHA-256 **6546874f1b99dec5a732c8e005c96f50a82ab76d32d7993df8b1d4b6099a0c1d**,22,702,878 bytes. The final behavior check has185 assertions and compares exact ordered query result identities to the frozen baseline.

| Measurement | Baseline | Cached candidate |
|---|---:|---:|
| Largest actual raw block |28,440,308 bytes |same block/article identity |
| First source read |3,086.107ms |3,053.769ms |
| Second source read |3,083.638ms |1.375ms |
| Third source read |3,051.969ms |1.213ms |
| Warm temporary record bytes |28,440,308 |0 |
| PSS during the three reads |26,233–42,094KiB |41,412–41,540KiB |
| Mid-stream cancellation |4ms |4ms |
| Final cache snapshot |none |4 entries,157,622 accounted bytes,6 evictions |

Times run from reader invocation to returned verified preview using Android elapsed realtime; repeated reads occur in one process. Three observations are not a p95, sustained thermal result or competitive benchmark. PSS values are snapshots, not process peaks. The largest raw block exceeds both the historical23MB observation and the8MiB target; this implementation streams it rather than claiming that target is a hard bound. Its selected record also requires28,440,308 temporary disk bytes on cold read.

All eight ordered result lists are unchanged, including the invented-token empty result. Query times are recorded individually (27–598ms in the final run); differences from baseline are not attributed to the preview cache because search itself is unchanged and filesystem state differs. Relevance, paraphrase completeness and factual support were not graded or improved by these timings. Existing OR-match/relevance limitations remain.

The actual installed catalog reports15 wiki and16 place shards. The test scans block metadata across all wiki shards and searches across all of them, reads the largest block, exercises distinct-source eviction, rejects changed record checksum reuse, rejects caller mutation, checks warm and mid-stream cancellation and rereads after clear. It does not rehash all41GB of unchanged source assets or qualify every article. Catalog and saved model hashes remain unchanged.

Unique app data after the final run is41,701,310,876 bytes; plus this APK is41,724,013,754 bytes. Adding the measured single cold-record file gives a calculated41,752,454,062-byte reader envelope, not a sampled total-device/update peak. ART/OS code overhead and arbitrary concurrent provider/update copies are not included. This new full-installed reader measurement does not reuse task303's old APK identity as current evidence. No model is loaded/generated in this reader test; combined native-model/KV/reader peak and physical12GB RAM acceptance remain open.

## Remaining gates

No embedding asset, new license or global preference is introduced. A semantic retrieval experiment would need separate immutable model/license pins, frozen matched relevance judgments and an installed resource comparison; similarity alone cannot certify support. Full candidate import/APK-update temporary peaks, simultaneous model/reader peak, physical ARM64/GrapheneOS, sustained thermal behavior, unseen relevance/answer comparisons and human acceptance remain open. Bulk sources remain browse-only. This measured cache improvement is not task302 source clearance or rival superiority.
