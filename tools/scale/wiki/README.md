# Offline English encyclopedia staging tools

All bulk inputs and generated editions live in the private wiki lane, outside Git. The checked-in source and evidence are English. This pipeline does not use a GPU, per-record LLM calls, article-by-article API crawling or bulk embeddings. It does not modify the canonical checkout or supervisor state.

## Current producer freeze

The final semantic producer policy is checkpoint `1da3eb7`: shared zlib6 blocks, guarded lean source supplements, structured infoboxes, positional contentless FTS5 with `reader_stopwords_v1`, and the budget-adapted 1,250,000-full priority freeze. The other 5,248,498 eligible identities are explicitly lead-tier. The original 2–3M full target was reduced after complete-shard measurements exceeded the provisional 22 GB installed budget. Actual final inventory, not this estimate, controls budget acceptance.

On LLMRig, `python.sh` reuses the installed CPython/Arrow cache, constrains affinity to CPUs 6 and 12, and disables library thread fan-out. The final builder disables auxiliary SQLite sort workers. Arrow output batches contain 64 rows and assert at most 2 GiB; whole-process memory is measured separately. At most two builder processes run. SQLite and compressed blocks remain disk-backed; source files are never overwritten.

```sh
tools/scale/wiki/python.sh tools/scale/wiki/bulk_build.py \
  /home/isa/PocketLore-control/scale-workers/wiki \
  --priority /home/isa/PocketLore-control/scale-workers/wiki/priority-1250000.sqlite \
  --edition edition-v7 --format v3 --supplement lean \
  --compression-level 6 --index-policy reader_stopwords_v1 \
  --start 0 --end 15 --workers 2
```

A dispatcher lock and per-shard writer locks prevent competing writers. Source/priority/configuration identities must match before reuse. Incomplete shards resume SQLite-committed row and block offsets; uncommitted block tails are preserved before truncation. Completed shards are reused only with matching source, priority, schema, index and compression policy. Resume with the exact producer hashes stored by that shard; never silently reuse an edition under changed semantics. A documented resource-only cache adaptation changes future child starts to 768 MiB; the first two already-loaded builders retain 256 MiB and their original hashes. Execution receipts retain commands, dispatch commit, driver hash, exit status and elapsed time. A failed child is not blindly retried. There are exactly 15 source shards, not an endless dispatch loop.

The separate redirect database is derived from pinned primary bulk dumps. Its canonical ID/title mapping is unchanged by the smaller full tier. A new schema-2 normalization replaces repeated shard filenames with integer references; every one of the 10,100,398 reconstructed tuples was checked against the preserved parent. The final selected alias database is 403,890,176 bytes. Root provenance binds the source inventory, priority parent, adaptation, alias pins and exact selected schema/hash.

## Validation and sealing

After all shards complete, run `verify_edition.py`, `audit_installed.py`, the original `evaluate.py` 80-query suite and the separately frozen 16-query low-count tail suite. The original expectations and misses stay unchanged. Evaluation emits per-query receipts before its final summary so a failure does not erase completed cases. `test_contract.py` exercises actual-source math, units, notices, malformed supplements, aliases and corruption against the preserved receipt fixtures.

`seal.py` hashes the explicit installed file set and binds the acquired input receipts. Its manifest includes its own byte length but not a circular self hash; the final handoff binds the manifest hash externally. `check_seal.py` independently checks fresh installed-file hashes and the exact byte total. The valid/corrupted fixture evidence is preserved. Do not seal an unfinished edition or overwrite a sealed inventory.

`freeze_inputs.py` freshly checks all pinned corpus and auxiliary input hashes and preserves explicit prototype, failure and source-fixture artifacts. After final checks and all workers stop, `freeze_evidence.py` hashes the completed edition's execution logs, evaluation case receipts and final check results. Both refuse to replace a final inventory. Their explicit file sets exclude supervisor state, private conversations and holdout data.

The final handoff belongs at `/home/isa/PocketLore-control/scale-workers/wiki/HANDOFF.json` and must bind the final private Git commit, artifact inventory, source/reader contracts, checks, failures and limits. A private incremental Git bundle can carry these commits without changing canonical Git metadata. `git.sh` always addresses the isolated `checkpoint.git`; never substitute global `--last` or operate on supervisor state.

## Limits that remain explicit

The actual format and decoding rules are in `docs/evidence/scale/wiki/ANDROID_READER_SCHEMA.md`; source provenance is in `SOURCE_CONTRACT.md`. Existing PocketLore FTS4 imports need an Android adapter and FTS5 support. Host staging, lexical title recall with uncontrolled OS cache, sampled source fidelity and LLM criticism do not establish physical Android/GrapheneOS acceptance, useful generated synthesis, distribution rights or competitive superiority. Pageview aggregation dates are unknown, aliases are newer than article text, and attribution templates can remain unexpanded. Missing facts remain unknown.
