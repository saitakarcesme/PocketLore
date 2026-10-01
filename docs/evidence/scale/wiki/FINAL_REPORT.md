# Complete English encyclopedia staging result

All fifteen pinned English FineWiki shards were acquired, hashed and processed on LLMRig. The selected edition contains **6,498,498 articles: 1,250,000 full texts and 5,248,498 explicit leads**, with **10,100,398 direct redirect aliases**. The sealed installed set is **21,853,451,129 bytes (21.853451129 GB; 20.352612370 GiB)**, including its inventory, leaving **146,548,871 bytes** below the provisional 22,000,000,000-byte text/index budget.

This is complete bulk staging, not Android, distribution-rights, human answer-quality or rival acceptance. The original 2–3M full-text target was explicitly reduced to 1.25M after oversized complete-shard measurements. The full original target was not achieved. Lexical paraphrase retrieval remains weak; no useful-synthesis claim is made.

## Exact contents and structural checks

| Item | Measured count or bytes |
|---|---:|
| Pinned Parquet sources | 15 files; 37,722,458,405 bytes |
| Raw source rows | 6,614,655 |
| Installed canonical identities | 6,498,498 |
| Full / lead articles | 1,250,000 / 5,248,498 |
| Excluded raw rows | 116,157 |
| Raw recognized-rights-marker exclusions | 282 |
| Other nonselected canonical-source rows | 115,875 |
| Retained full-text UTF-8 bytes | 18,553,104,556 |
| Retained lead UTF-8 bytes | 2,741,138,693 |
| Retained wikitext supplement UTF-8 bytes | 8,981,336,771 |
| Compressed block files | 11,244,264,230 |
| SQLite catalogs, including FTS and metadata | 10,205,188,096 |
| Selected redirect database | 403,890,176 |
| Other installed metadata, licenses and inventory | 108,627 |
| Shared compressed blocks | 102,273 |
| Largest raw block / record | 28,440,308 bytes |
| Installed payload files plus inventory | 53 + 1 |

Every admitted ID/title/source-row/tier matches the frozen priority. All source positions are covered exactly once by an article or exclusion. Block offsets and slices have no gaps, overlaps, unreferenced tails or out-of-bound records. All fifteen SQLite integrity checks passed. The actual reader verified 1,754 sampled records in 1,752 distinct blocks, including each shard's largest record; this is not exhaustive source-content re-extraction.

The installed-source audit passed all 67 available canonical source samples, exact full/lead text, original field hashes, retained wikitext ranges, structured infoboxes and source math tags. Five real math/chemical/unit/CIA checks and twelve actual unresolved-marker exclusions passed. The strict frozen title “Museum Plaza” remains absent; its direct alias resolves to “Louisville Museum Plaza,” without rewriting the expectation.

All 10,100,398 logical aliases matched their preserved parent after schema-2 normalization, saving 183,562,240 bytes. Rights screening is heuristic: 897,709 admitted records have recognized notice candidates, while remaining records retain the dataset-license-only/unreviewed status. Source-specific rights and notice-detection false negatives remain unresolved.

## Frozen query results

| Original category | All expected titles in top 10 |
|---|---:|
| Head | 16 / 16 |
| Intended tail | 15 / 16 |
| Paraphrase | 1 / 16 |
| Math and units | 15 / 16 |
| Multi-part | 3 / 8 |
| Supported-title cases total | 50 / 72 |

All eight absence controls returned related hits. The tool generates no answers and implements no answer-abstention judgment. There is no post-result recall threshold, human usefulness result, private holdout result or factual-answer score. Raw results preserve every miss, including the absent strict locator. No query or ranking tuning followed these runs.

The separately frozen sixteen low stored-count tail probes scored **12/16**: eight literal titles passed and four of eight lead paraphrases passed. Every frozen source identity/hash/lead binding matched. These records were selected deterministically from the first canonical shard; their stored view counts and unknown aggregation period do not establish current popularity or a random sample.

| Host query metric | Original 80 | Supplemental 16 |
|---|---:|---:|
| Median latency | 774.97 ms | 946.39 ms |
| p95 latency | 1676.71 ms | 1602.05 ms |
| Maximum latency | 2055.96 ms | 1906.27 ms |
| Process peak RSS | 108,396 KiB | 103,876 KiB |
| Total run time | 69.44 s | 17.32 s |

These sequential Linux passes ran after builders and structural verification finished, with no deliberate concurrent lane compute job. OS cache was not reset; source-audit reads can warm later queries, and other host contention was uncontrolled. Search latency excludes subsequent source-audit reads and inference. These are not Android latency or memory measurements.

## Processing resources and source contracts

The fifteen final children ran without failure over **10,382.764949 seconds** (about 2 h 53 min), excluding acquisition, prototypes and initial dispatcher priority hashing. Summed child wall time was 19,911.232645 seconds and overlaps across workers; it is not CPU time. Maximum builder process RSS was **3,144,412 KiB**. The largest Arrow output batch was **33,994,202 bytes**, independently below the 2 GiB batch limit. Whole-edition verification took 221.329683 seconds with 312,240 KiB process RSS. Process RSS is not concurrent host total or physical-device memory.

At most two CPU workers used affinity CPUs 6 and 12, library thread fan-out was disabled and final SQLite auxiliary sort workers were zero. Acquisitions used at most two HTTP requests with bounded streaming and backoff. No GPU job, article-by-article crawl, bulk embeddings or per-record LLM call was used. The first two builders retained the 256 MiB SQLite-cache producer; later builders used a documented 768 MiB resource-only variant. Every stored producer-file hash matches its recorded checkpoint; content/index semantics stayed fixed.

FineWiki revision `8bd13e72e6a002407649b3e898535f42ceb1aeb9` contains an August 2025 Enterprise-derived snapshot. Priority uses NeuML revision `b5559579fdfbd52faef3c2d68372161b6c06c790`; its pageview aggregation interval and separate database rights remain unknown. Direct aliases use the primary 2026-09-01 redirect SQL and multistream title index, newer than the text; the page-table inventory entry was not acquired or used. Exact hashes, dates, rights statements and limitations are in [SOURCE_CONTRACT.md](SOURCE_CONTRACT.md) and the bound inventories.

The actual format is shared zlib6 blocks, schema-3 article catalogs, contentless positional FTS5, disk-backed term statistics, schema-2 redirects and lazy validated text. Full text is source-identical; leads are explicitly labeled. Wikitext supplements preserve exact original ranges with declared scopes and original hashes; they do not expand templates or establish complete attribution clearance. [ANDROID_READER_SCHEMA.md](ANDROID_READER_SCHEMA.md) describes byte/codepoint offsets, limits and token behavior. Existing PocketLore FTS4 imports require a new FTS5 adapter; no Android integration was built or accepted here.

Pinned AndroidLM and BOAR primary documents were reviewed for layout/ingestion ideas, with licenses and receipts preserved. No rival source tree was copied and no comparative superiority is asserted.

## Sealed evidence and open work

| Inventory | SHA-256 |
|---|---|
| Installed set | `5160f3a8fa683065707aaa70ccaa87ad475cd32d87561cc70e3a977332835df5` |
| Sources, prototypes and recovery evidence | `5a785b5c801b2f4b17afb1ff3dfa5c3ce8fcc996ad3d9266b58b85735430f035` |
| Final execution and check evidence | `613a92dbaf1f7b3787ed062152f1f76090aa6f448590528856cc90e96057a7ad` |

A fresh second hash pass verified all installed payload files and the exact installed total in 25.61 seconds. Source sealing freshly checked all pinned input hashes and preserved 276 files totaling 58,927,639,335 bytes. Final evidence sealing binds 68 files, including raw query case receipts, completed logs and the archived pre-normalization alias copy. Failed acquisition probes, the duplicate-ID census failure, interrupted block tails, oversized variants, negative controls and the initial incorrect glob-based footer count remain preserved. Sixteen contract regressions passed; syntax checks are separate from behavioral checks.

Independent criticism remains pending against the sealed review packet. Follow-on work includes separately budgeted semantic/answering improvements for the recorded misses, an Android FTS5 reader adapter, source-specific rights review and physical Android/GrapheneOS measurements. The 50 GB total-app asset limit and 12 GB device RAM limit remain unmeasured on hardware. No canonical checkout, supervisor state, holdout, secret store, existing cache or unrelated service was modified. The final private commit, transport bundle, artifact paths and review allowlist are bound by the lane's `HANDOFF.json`.
