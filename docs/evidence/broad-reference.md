# Task 210 repair 1: source-faithful broad edition

Current repair is in progress; the default objective verifier intentionally fails until a new edition, source-body semantic reviews and actual Android behavior are available. The prior report below is preserved failed evidence, not current acceptance. The critic rejected missing formulas/units, unresolved attribution and keyword-derived topic quotas.

The repair uses bounded official Wikipedia revision lookup and rendered oldid HTML, preserving exact acquisition receipts. It copies mathematical TeX and rendered numeric units, excludes quoted prose/media, retains references and source-specific attribution notices, and excludes unresolved extra licensing terms. Seven extraction regressions pass on actual source defects plus negative fixtures. The initially fast per-title API requests reached HTTP 429; they were stopped, failures retained, and replaced by batched metadata lookup with serial paced HTML acquisition that stops on any further 429. No source worker staging is modified.

Partial source-body reviews, exact supporting excerpts/revisions/hashes and explicitly pending areas are in [the review record](broad-reference/repair/semantic-review.json). These are builder judgments, distinct from independent review. A title shortlist never counts as a completed quota. The original 40 questions and 1,000/10,000/eight/50 targets are unchanged. Current source/pack construction and new-fixture Android tooling are checkpointed as unvalidated until actual runs complete.

---

## Preserved failed task 210 report (checkpoint 9681055)

# Task 210: broad reference, disk-backed retrieval

Builder status: **technical checks pass; breadth/rights/useful-answer release gates remain open**. The local evaluation edition installs 1,076 distinct real Wikipedia-derived documents and 26,660 unique source-substring passages. Together with the retained reference/science editions, Android searches three collections, 1,094 documents and 26,870 passages. This is measured emulator coverage, not merely a staging count. No generated-answer success, distribution clearance, phone acceptance or rival superiority is claimed.

The task's frozen numerical targets remain 1,000 documents, 10,000 passages, eight areas and 50 documents per area. The first two are independently verified. Eight heuristic area buckets exceed 50 each, but **50 semantically suitable documents per area is not established**. The source-specific extraction and attribution defects prevent closing the distributable broad-reference objective. Concrete follow-ups below retain these targets rather than lowering them.

## Acquisition, rights and source limitations

The explicitly authorized sealed handoff was read without writing the worker's staging/worktree. Commit `1ae494d95aaf7ab15af8f76b599a629a946b2ada` was inspected against its actual base `41de899329e05def1669372c996a6c460e33210b`: 15 changed files. Fourteen tools/docs files were imported; acquisition tools were relocated from `tools/corpus` to `tools/packs/corpus`; the worker's `.gitignore` and unrelated branch history were not imported. No branch switch or merge occurred.

The reused dataset is `wikimedia/wikipedia`, `20231101.en`, revision `b04c8d1ceb2f5cd4588862100d08de323dccfbaa`. All five unchanged parquet shards were reused, not downloaded again. [Acquisition records](broad-reference/acquisition/receipts.jsonl), [inventory](broad-reference/acquisition/ARTIFACTS.json), [rights provenance](broad-reference/acquisition/license-provenance.json) and [handoff receipt](broad-reference/handoff-receipt.json) preserve immutable pins. Inventory SHA-256 is `849b9b065940b2dc7019c306eac1805fa43fc09c9d9eb396e0d7740a9e9e8810`. The host independently compared every retained source title/URL/text against the pinned parquet and checked all 28 inventoried files: 17.161 seconds, peak host RSS 785,856 KiB; 16 acquisition mutation tests passed. These are host measurements, not phone RAM.

Wikipedia text is not generic public-domain content. The edition records CC BY-SA 4.0 attribution to each article's Wikipedia contributors, original article and contributor-history URLs, license URL, source/dataset/shard hashes, extraction modifications and historical snapshot date. The offline archive contains the actual English legal code, inspected through Android's License button. Attribution/share-alike and third-party exceptions remain applicable; see [Wikimedia terms](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use) and [dump licensing guidance](https://dumps.wikimedia.org/legal.html). The upstream dataset card's older 3.0/GFDL wording and the 2023 Wikimedia terms basis for 4.0 are explicitly preserved in the rights record, not silently erased.

The snapshot has no exact per-article revision timestamp/ID or contributor snapshot. Its history URL is an attribution route, not an immutable author roster. An edit date is never invented: every source says “Historical 2023-11-01 dataset; article edit date unknown.” The source extraction may have lost third-party attribution, formulas, units and text rendered through templates. Hashes cannot repair or clear those omissions. Therefore `distribution_ready` remains false, every broad source carries the warning, and the production answer controller blocks generation when broad extracts enter selected evidence. No weights, bulk corpus or pack binaries are committed or published.

Concrete observed defects include Algae's missing kelp length, Absolute value's missing variables and result of the example, Alkane's absent formula, Aruba's absent dimensions, and Transport in Belgium's missing network lengths. The builder flags 549 suspect passages with a narrow diagnostic expression; this is neither a complete detector nor an exclusion/repair count. No facts were invented to fill gaps. The acquisition worker's exclusions remain unchanged; this task makes no additional hidden exclusions and counts no duplicated stress passages.

The frozen [topic audit](broad-reference/topic-audit.json) examines the first twelve titles/leads in source order per assigned area (96 total). Builder judgments identify a linguistics article under geography, an abandoned Louisville building proposal and a manufacturer/component under travel, and Futurist cooking under practical reference. Biographies and sector overviews are related background, not equivalent to conceptual explanations or practical instructions. This sample is not an independent semantic review of all 1,076 documents, and keyword counts do not certify the quota.

| Heuristic area | Documents | Unique passages |
|---|---:|---:|
| Science | 148 | 3,826 |
| History | 143 | 4,486 |
| Geography | 147 | 6,068 |
| Mathematics | 135 | 2,265 |
| Computing | 143 | 2,911 |
| Civics | 143 | 2,901 |
| Practical reference | 80 | 1,682 |
| Travel | 137 | 2,521 |

## Implementation and reproduction

`tools/packs/broad/build.py` creates a content-addressed ZIP containing the manifest, SQLite FTS4 index and legal HTML. Documents and passages retain exact hashes, source offsets, stable edition-aware citation IDs, rights and provenance. Document bodies and passage rows are read lazily; the whole corpus is never made into Java passage/index objects. Android uses a 2 MiB SQLite page-cache setting, disabled mmap, at most 64 unique broad candidates and four returned rows. The pre-existing small-pack object index retains its measured admission bounds; combined candidates can additionally include those bounded small-pack matches.

Admission allows one retained broad edition, maximum 128 MiB archive/256 MiB database, 5,000 documents/100,000 passages, bounded metadata/source/passage sizes and available-disk reserve. The current archive is much smaller than these caps. Import validates the private staged database schema, FTS integrity, document/passage hashes and exact UTF-16 source substrings before atomic catalog publication. Opening rehashes the saved database. Failed/cancelled imports remove owned stages and preserve catalog/model bytes. Small packs continue using their existing format; two real editions remain installed and searchable together with the broad edition. There is no broad-edition replacement/removal UI yet; admitting a second broad edition is deliberately refused.

Reproduction on the installed rig toolchain (Python 3.14.7, SQLite 3.53.4):

```sh
python3 tools/packs/broad/build.py --out downloads/broad-reference/v1
# Use a new directory on recovery; the builder refuses to overwrite an experiment.
python3 tools/packs/broad/build.py --out downloads/broad-reference/repro
bash tools/android-build.sh
python3 tools/evaluation/broad-reference/run_android.py
python3 tools/evaluation/verify_broad_reference.py
```

The builder requires the read-only sealed snapshot path recorded in its source; it validates all bytes before use. A second independent build on this same rig produces identical full pack and index hashes. Cross-machine/SQLite-version byte equality is not established. Acquisition scripts and immutable requests are included for reconstruction; the README commands have been adjusted to `tools/packs/corpus` here, with a warning not to run report-writing commands against the sealed snapshot. Android validation requires the existing `emulator-5560` with the pinned saved model and two prior project fixture editions. The driver reuses an already imported broad edition after recovery rather than silently deleting/reimporting it; it neither launches an emulator nor restarts supervision.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| Final debug APK | 11,921,193 | `767e1aa89b39f6b9d905fabe4d5692c57e7bf066f1297771df22dcbb3f579df7` |
| Broad archive | 46,822,920 | `915f82f041f59d3cd0e82a8b6fd9dbdb2d12187c2e969c5891de6e3ad46dd67c` |
| SQLite index | 125,472,768 | `2b142df934c53d5f54a979fe0e3639e2a5e6b592ca98a34b317a9a778d062067` |
| Source JSONL | 30,250,745 | `8e33e513d28cebc411252315e8b3de71b6b45537e4e85ab6ac672ecbb4c44a10` |
| Passage JSONL | 45,965,002 | `9aaa7e56e246d45869bdd985ca60332f94d125cc4a5f77273809aa9b6b92d97b` |
| Saved production Qwen2.5 0.5B | 491,400,032 | `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db` |

The production model is unchanged. No optional Qwen3 evaluation artifact is relabeled as deployed.

## Actual emulator behavior and retrieval

The [protocol](../../tools/evaluation/broad-reference/protocol.json) was frozen in commit `1c5fe27` before product retrieval changes: two articles per area, each with a literal and paraphrase query, plus eight invented-telemetry absent controls (40 queries). Exact source hashes and supporting lead excerpts are pinned. This small development sample measures article retrieval, not comprehensive factual or passage-level answer coverage.

The first full UI import took **26,748.375 ms** and installed all broad rows alongside the small editions. That run later failed source navigation for Constitution; its complete [raw failure](broad-reference/failures/android-20261001T074000532651Z/import.json) is retained. Initial retrieval found 26/32 expected articles. Ordinary body matches exhausted the 64-candidate cap before relevant title matches, and small BM25 scores were not comparable with broad overlap scores. The repair prioritizes title FTS candidates and uses a common overlap ranking for mixed index results. It changes neither frozen questions nor corpus. Final recall is **29/32**, with regressions on literal Acid and Cooking and the persistent distance-from-zero paraphrase miss. Full before/after IDs appear in [metrics](broad-reference/metrics.json).

Final [import/resume](broad-reference/run/import.json) and [new-process restart](broad-reference/run/restart.json) records bind the current APK/source files to the same saved edition. These runs explicitly report `existing_broad_reused:true`; they are not falsely labeled fresh full imports. Eight real Activity source buttons per run expose edition/citation/source hashes, source dates, rights and contributor-history links. [Source screenshot](broad-reference/run/restart-source.png) and [offline license screenshot](broad-reference/run/restart-license.png) were visually inspected. The import button and production import worker are exercised, but instrumentation returns the fixture URI through an ActivityMonitor: browsing a real external SAF provider is not tested anew here. Airplane mode is enabled, Wi-Fi/data disabled; no research-time network is used.

All eight absent queries have zero **broad** hits and controller route ABSTAINED. Four still retrieve unrelated small-pack OR matches; combined retrieval is not universally empty. Every supported case is withheld from generation/falls back under the source-quality restriction. Source-button navigation is not generated citation-span or model-entailment evidence. Top results can include multiple passages from one article, sometimes a tangential or broken passage; a found article alone does not establish an answer.

Across the 40 final restart queries, measured retrieval/serialization p50 is **4.488 ms**, p95 **20.302 ms** (nearest-rank: sorted observation at ceil(p*N), no interpolation). These exclude model generation, source-dialog UI and cold process/model startup. They are emulator timings and are not mixed with host inference or phone speed claims.

Corrupted-index rejection is measured twice with distinct meanings: the UI refuses a second broad edition by admission policy; a separate empty fixture directory exercises the real production parser and rejects an altered index with **Index SHA-256 mismatch**, leaving no stages. Only the latter establishes byte-integrity rejection. The real Cancel pack import control rejects the operation with catalog/model unchanged and zero stages. Final `cancel_ms` **140.514 ms** is the entire instrumented import/cancel call, not click-to-idle latency, blocked-provider cancellation or OS low-memory safety. No unrelated assets were removed.

## Resources and checks

The final new-process catalog opening took **396.406 ms** including saved-index hashing. After model unload and GC, Java used bytes rose 3,936,896 → 4,686,528 (**749,632 bytes**), below the checked 32 MiB incremental opening bound. PSS was 90,182 → 91,592 KiB; RSS 177,904 → 179,448 KiB; swap 22,492 KiB unchanged. After queries: Java 5,465,312 bytes, PSS 66,083 KiB, RSS 155,976 KiB, swap 22,364 KiB. This is app-process memory with prior load/unload residue, not isolated SQLite allocation, a sampled import peak or phone acceptance. Large corpus data stays on disk. Host pack build took 9.870 seconds with peak RSS 329,964 KiB.

[Disk accounting](broad-reference/disk-accounting.json) separates 1,738,494,300 reused corpus-download bytes (1,866,834,008 total sealed bytes) from phone assets. The current APK + model + two small archives + broad archive + index total **675,807,423 bytes**. Import staging can additionally hold one 46,822,920-byte archive and 125,472,768-byte database; these become retained files after success. Host failed experiment/reproduction copies are not installed coverage. Emulator `du` records **762,634,240 allocated bytes** in all app files, including test fixtures; cache/code-cache each 8,192 bytes. Native APK entries are 5,597,736 ARM64 and 6,077,192 x86_64 uncompressed bytes; installer/native extraction/OS overhead is not included in the logical asset sum. This fixture is well below 50 GB even with these components, but it is not a measurement of arbitrary future libraries or physical <=12 GB device behavior.

Required standalone build passes with the exact final APK hash. `python3 tools/evaluation/verify_broad_reference.py` passes actual archive/database/content/rights/dedup checks, current source/APK/receipt bindings, Android counts/provenance/restart/rollback, frozen query behavior and reproducible bytes. Missing-license, missing-artifact and changed-run-artifact regressions reject. The script reports retrieval misses instead of converting a presence check into a quality pass. Existing small-index `tools/android-check.sh` passes eight retrieval/abstention/corruption/citation contracts. [Check logs](broad-reference/checks/) preserve results.

Earlier PRAGMA query-only and FTS read-only integrity failures remain under [failures](broad-reference/failures/). Validation now opens only the owned staged database writable for Android FTS integrity checking, verifies unchanged bytes afterward, and uses read-only connections for research. A prior passing UI run had a screenshot taken before the license transition finished; it is retained as a superseded evidence-capture defect. The final capture waits for the legal dialog to render. No historical failed identity or raw output was deleted.

## Concrete remaining work

Three task specifications were created, without dispatching or changing runner state; [public copies and exact queue receipts](broad-reference/follow-ups/receipt.json) are preserved:

1. **211-source-faithful-broad-edition**: recover immutable article/formula/unit/attribution fidelity, review semantic quotas and replace/exclude unresolved sources while retaining 1,000/10,000/eight/50 targets. Upstream article access or an alternate licensed route is needed for missing source content; rig implementation and source audit are available now.
2. **212-broad-evidence-answer-integration**: fix the recorded exact-title/paraphrase/diversity failures and test useful supported real production JNI against the reviewed edition with bounded context and exact cited excerpts. Rig work; no physical hardware dependency for screening.
3. **213-broad-candidate-release-validation**: refreeze dependency/data/index/APK identities and fresh offline installation after that integration. Existing release-v4 remains historical; its hashes cannot validate this changed candidate.

Independent source/rights criticism, clean-machine reproduction, owner signing/publication, physical Android/GrapheneOS, sustained phone resources and human usefulness remain open. There is achievable independent product work, so neither the release nor the full breadth objective is declared complete.
