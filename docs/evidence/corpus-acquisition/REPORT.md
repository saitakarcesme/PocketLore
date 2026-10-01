# English licensed corpus staging evidence

The final private snapshot meets the requested corpus staging thresholds: **1,076 distinct source documents and 26,660 unique body passages**, with at least 50 documents in every area. These are frozen rule-based area assignments, not human acceptance of topical relevance, answer usefulness, or release quality.

| Area | Distinct documents | Unique passages |
|---|---:|---:|
| Science | 148 | 3,826 |
| History | 143 | 4,486 |
| Geography | 147 | 6,068 |
| Mathematics | 135 | 2,265 |
| Computing | 143 | 2,911 |
| Civics | 143 | 2,901 |
| Practical reference | 80 | 1,682 |
| Travel | 137 | 2,521 |
| Total | 1,076 | 26,660 |

## Source and rights

Five pinned bulk shards from Wikimedia's English November 2023 Wikipedia snapshot were acquired at dataset commit `b04c8d1ceb2f5cd4588862100d08de323dccfbaa`; 781,445 source rows were examined. The public [manifest](manifest.json) records shard hashes, exact record hashes, licensing sources and validation counts. Bulk text, raw shards and receipts stay outside Git.

[Wikimedia's Terms of Use, section 7](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use), effective June 7, 2023, and its [dump licensing notice](https://dumps.wikimedia.org/legal.html) establish CC BY-SA 4.0 obligations. The upstream extracted dataset card's conflicting CC BY-SA 3.0/GFDL declaration is preserved in the private provenance manifest. Text is not represented as CC0. Article titles, source URLs, Wikipedia contributor credit, contributor-history references, license URLs and modification notices are retained. The full license text is staged for offline packaging; adapted text must retain attribution and share-alike obligations.

The upstream extract lacks per-article revision IDs, timestamps and contributor lists. Those values are null; the dump date is not substituted for an edit date. Article/history URLs provide the attribution method allowed by Wikimedia's terms, but do not constitute frozen contributor lists. Primary rights pages and the dataset card have acquisition receipts and hashes. Explicit imported-text and fair-use markers trigger rejection; this cannot establish exhaustive sentence-level copyright clearance after upstream extraction.

## Validation and resources

Every retained source's complete extracted text, title and URL matched its pinned upstream shard. Each passage matches an exact contiguous source substring and UTF-8 SHA256; character offsets and normalized hashes are checked. No generated factual passages are included. Document identity/URL/normalized-text and global normalized passage deduplication yielded zero duplicate records in the final corpus. Every retained document has at least ten unique passages. Full validation found zero corrupt chunks and zero missing required rights fields.

Sixteen mutation tests passed with no skips: genuine subset acceptance, missing license and attribution rejection, false history links, unknown dataset rights, duplicate documents/passages, corrupt source/chunk text, bad offsets, incorrect topic, fabricated revision, license downgrade, chunk-attribution loss, back-matter inclusion and curated-topic exclusion. A missing `/usr/bin/time` prevented an initial timing wrapper from starting; its raw failure log is preserved, and validation then used Python's installed resource/timing facilities successfully.

Acquisition used CPU affinity 0–1, a 2 GiB address-space cap, single HTTP concurrency, at most two attempts per URL and a 600 MiB per-file limit. Five shards total 1,738,494,300 bytes. Version-4 acquisition took 130.892 seconds with 540,164 KiB peak RSS; full final validation took 13.781 seconds with 787,472 KiB peak RSS. Curation is separately timed in the private count report. These are LLMRig measurements, not Android/device results. No GPU inference, app/emulator/service changes, private holdout access, or main-builder edits were performed.

## Preserved development evidence

The single-shard snapshot was partial: 1,014 documents and 26,049 chunks, with only 39 practical-reference documents. Expanding to three pinned shards increased the candidate population; inspection found entertainment and abstract-title false matches. Stricter rules were frozen before rebuilding, producing a second partial result with only 40 practical-reference documents. The five-shard bound retained these stricter rules and produced 1,139 candidates. A separately frozen conservative curation policy removed six identified practical-reference mismatches and 57 documents with fewer than ten body passages after excluding back matter, without refilling quotas. Final counts above supersede candidate counts. Earlier snapshots, decisions and failures remain private.

## Handoff and limits

The sealed snapshot is `/home/isa/PocketLore-control/corpus-acquisition/snapshot-final`; its 28 inventoried files total 1,866,834,008 bytes, excluding the inventory file. The `ARTIFACTS.json` SHA256 is `849b9b065940b2dc7019c306eac1805fa43fc09c9d9eb396e0d7740a9e9e8810`. Read-only permissions deter accidental mutation; hashes are the integrity authority. The final handoff is `/home/isa/PocketLore-control/corpus-acquisition/HANDOFF.json`.

The attached worktree's Git metadata was mounted read-only. Authorized commits therefore reside on `codex/source-corpus-acquisition` in the independent repository `/home/isa/PocketLore-control/corpus-acquisition/branch.git`, copied without hardlinks. The main Git metadata was not modified. No merge or push was performed.

This ordered, bounded sample is not representative of Wikipedia. Topic classification remains heuristic and some biographies or institutions may remain; practical reference includes sanitation infrastructure and agriculture, while travel includes historical transport. Exact normalized deduplication does not prove absence of near duplicates. Body passages can contain headings/lists and cut sentences; upstream template extraction can omit mathematical formulas, numbers, units or context. The 2023 text is stale for current travel, civic and practical decisions. Additional source-specific rights/attribution review and product import/UI work remain open. This is corpus preparation, not model-answer, physical-device, human, or bounty acceptance.

## Independent criticism

An independent LLM critic reviewed only goals and frozen artifacts/tests; this is not human acceptance.

> Verified hashes, 1,076 documents, and 26,660 unique verbatim passages meet numerical thresholds, but missing mathematical formulas and broad practical-reference classification limit usefulness, while omitted third-party attribution notices require review before redistribution.
