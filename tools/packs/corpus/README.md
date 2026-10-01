# Licensed English corpus staging

This pipeline prepares source text and passages for PocketLore; it does not establish model-answer quality, Android acceptance, or bounty acceptance. Run on LLMRig in the isolated acquisition worktree. No GPU, app service, emulator, main worktree, or holdout access is needed.

## Reproduction

Use an existing Python environment with PyArrow (the recorded run used Python 3.12.14 and PyArrow 25.0.1). The remaining dependencies are Python's standard library.

```bash
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2
python tools/corpus/acquire.py /absolute/private/staging/candidates --rules tools/corpus/selection-v4.json
python tools/corpus/curate.py /absolute/private/staging/candidates /absolute/private/staging/final --policy tools/corpus/curation-v1.json
python tools/corpus/validate.py /absolute/private/staging/final
python tools/corpus/test_validation.py /absolute/private/staging/final
python tools/corpus/manifest.py /absolute/private/staging/final
python tools/corpus/freeze.py /absolute/private/staging/final
```

Acquisition and full validation each restrict their process to two available CPUs and 2 GiB virtual address space. HTTP uses one connection at a time, two attempts per URL, a 45-second socket timeout, and a 600 MiB per-file ceiling. Five immutable upstream shards total 1,738,494,300 bytes. Do not run several acquisition/validation processes concurrently if a combined two-core budget is required. The validator streams upstream batches but retains selected documents in memory. Actual peak RSS and elapsed acquisition time appear in `counts.json`.

The rules are copied to `selection-v1.json` inside each stage for a stable artifact name; the embedded `version` identifies the policy. Selection and deduplication rules are frozen before processing. Version 2 expands only the acquisition population from one shard to three; classification, minimum passage length, quotas, and deduplication remain unchanged. Version 3 adds explicit entertainment, sports and chronology exclusions and requires practical-reference title matches while excluding institutions and abstract/legal titles, following inspection of false matches in version 2; all preliminary outputs are preserved. Version 4 retains those stricter rules and expands the bound to five shards after version 3 still lacked practical-reference coverage. The first snapshot is retained as partial evidence. No holdout is used. The source snapshot is historical (November 2023); it is unsuitable for current schedules, immigration requirements, prices, or other live facts.

The full extracted source is stored unmodified in `sources.jsonl`, with SHA256 over its UTF-8 bytes. Each chunk is a contiguous, nonoverlapping substring identified by Python Unicode character offsets and its own exact UTF-8 SHA256. Chunk records repeat license and attribution metadata. Final curation stops passage extraction before trailing See also, References, Bibliography, Further reading or External links headings while retaining the complete source text; documents with fewer than ten remaining body chunks are excluded. Six identified practical-reference mismatches are excluded by a separately frozen policy, with no quota refilling. Global passage deduplication normalizes Unicode with NFKC, case and whitespace; document deduplication checks page IDs, source URLs and normalized whole-text hashes. This is exact normalized deduplication, not near-duplicate detection. Remainders shorter than 80 words are not counted. Body chunks can still include lists and headings; paragraph-level semantic quality has not been independently accepted. Chunks contain 80–160 whitespace-separated words and can cut sentences. There is no generated factual text.

Area assignment counts distinct regex terms in the title and the first 600 characters, assigning exactly one area. Some biographies, institutions and historical transport articles qualify; practical reference includes agriculture, food and construction. These are reproducible rule-based coverage counts, not a human topical-relevance or usability evaluation. `topic_scores` and the complete source support inspection. This is a bounded, ordered sample, not a representative Wikipedia sample.

## Rights and attribution

The primary [Wikimedia terms, section 7](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use), effective June 7, 2023, and [dump licensing information](https://dumps.wikimedia.org/legal.html) specify CC BY-SA 4.0 text reuse. The November 2023 dataset card instead declares CC BY-SA 3.0/GFDL; the pipeline preserves that declaration but uses the applicable Wikimedia CC BY-SA 4.0 obligations, not CC0 or an unqualified permissive license. Original primary pages, dataset card and receipts are preserved privately with exact hashes.

Redistribution must retain article identity, contributor credit, article/history URLs, [CC BY-SA 4.0 license](https://creativecommons.org/licenses/by-sa/4.0/), and the modification notice; distribute adapted text under the same or a compatible license and do not impose additional restrictions. License text is staged for offline packaging. The attribution method uses article URLs, as permitted in section 7, with explicit contributor-history references. The dataset supplies no article revision IDs, revision times or author lists: these remain null, rather than pretending the dump date is an edit timestamp. The pinned dataset Git revision and shard hash identify the actual extracted source bytes.

Only text is acquired; no media licenses are inferred. The dump notice warns about third-party quotations, imported material and possible infringements. Explicit imported-text or fair-use markers trigger rejection for manual review. This filter cannot prove that all third-party exceptions or attribution notices survived upstream plain-text extraction. Preserve the full source and metadata; distribution review for source-specific exceptions remains open. `missing_rights: 0` means all required metadata fields passed validation, not an individual copyright clearance for every sentence.

## Outputs and failure handling

Private staging holds `sources.jsonl`, `chunks.jsonl`, `decisions.jsonl`, frozen selection, receipts, raw pinned shards, primary rights pages, count and validation reports, and test logs. Keep all bulk data outside Git; commit only tools, selection pins and small evidence reports. Receipts capture attempts, failures, timestamps, selected HTTP headers, exact hashes and byte counts. A failed download leaves `.part` bytes and a failure receipt; retry count is bounded. An already completed download is reused and pinned shard hashes are checked.

An advisory writer lock in the parent staging directory prevents concurrent acquisition into the same snapshot. The tool refuses to overwrite an existing source JSONL. If processing was interrupted, retain the incomplete files as failure evidence and use a new staging directory with hardlinked verified raw downloads. No automatic destructive recovery occurs. A stage with completed validation can be frozen with `freeze.py`; its artifact inventory is content-addressed and the handoff records its hash. Keep later review notes outside the sealed snapshot. File permissions deter accidental modification; hashes, not filesystem permissions, are the integrity authority.

Mutation tests operate on copies of genuine staged records and verify missing-rights rejection, duplicate documents and chunks, corruption, wrong topics, fabricated revision metadata and lost chunk attribution. Their fixtures are never counted in coverage.

## Isolated Git handoff

The attached worktree Git metadata was mounted read-only. Commits are stored in `/home/isa/PocketLore-control/corpus-acquisition/branch.git`, an independent bare copy made with `--no-hardlinks`; the main repository was not edited. Use the repository path, branch and commit in `HANDOFF.json` for review/import. No merge or push is performed.
