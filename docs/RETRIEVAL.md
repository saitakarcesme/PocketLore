# Retrieval development evaluation

PocketLore ranks passages with an immutable in-memory inverted index. The index
stores precomputed BM25 contributions for normalized terms and visits only the
postings touched by a query. Body term frequency has weight 1; the document-wide
title has weight 0.3. BM25 uses k1=1.2 and b=0.75. Results sort by score, then stable
citation ID, and return at most four passages. Source text, dates and citation IDs
are unchanged by indexing.

Ranking uses limited English inflection folding and an explicit four-group
expansion list: dark/night/illumination, crack/fracture, underground/groundwater,
and ultraviolet/UV. Original query terms have weight 1 and expansion terms 0.7;
query keys are sorted for deterministic score accumulation. Some generic query
words are omitted only for ranking. The list is small, development-tuned and
inspectable in `ResearchEngine.java`. These are retrieval hints, not universal
synonym equivalences. Word-sense ambiguity and incomplete English morphology
remain limitations; there is no embedding model or semantic entailment checker.

Exact vocabulary coverage remains separate from this ranking normalization.
`missingTerms` still reports exact query terms absent from the original vocabulary.
`EvidencePrompt` still checks the first two, 400-character excerpts. A ranking
expansion does not count as evidence that a claim is supported or allow generation
past that existing gate. This conservative separation improves source discovery
but leaves many useful queries blocked from generation.

## Frozen public cases

`evaluation/retrieval/development.json` contains 30 development-only questions:
20 with source-ID judgments and ten with absent evidence. Cases include literal
wording, inflections, paraphrases, explicit distractors, comparisons, multiple
source documents, partial coverage, cross-document distractors and stale/current
requests. Judgments were authored by the builder after inspecting real passages
in the pinned task-030 pack; they are not independently reviewed gold labels.
Alternative IDs within a required evidence group allow multiple supporting
passages. Labels do not enumerate every potentially relevant passage.

The cases, acceptance floors, pack hash and baseline source hash were committed
in `753bcaa` before retrieval changes. The original eight public questions in
`evaluation/development.json` are unchanged. They are additionally executed and
preserved raw, but their model-authored general answer rubrics are not used as
retrieval relevance labels. The private holdout was not read or used.

## Reproduce

```sh
# Requires the exact task-030 pack in downloads/packs/english-reference.plpack.
# Provision using docs/KNOWLEDGE_PACKS.md if it is absent.
bash tools/android-build.sh
python3 tools/evaluation/evaluate_retrieval.py
```

Use the existing booted `emulator-5560` (override `ANDROID_SERIAL` only with an
emulator serial). The verifier does not start emulators, change services, fetch
data, run a GPU job or invoke a model. Builds use the existing offline toolchain.
`POCKETLORE_TOOLCHAIN` can select another compatible installed toolchain.
`--baseline-only` and `--host-only` are explicitly labeled diagnostics, not full
acceptance. Each run creates a unique ignored `downloads/evaluation/retrieval-*`
directory and preserves raw scores, IDs, coverage decisions and timing samples.

The verifier checks the frozen case, pilot and pack hashes. It retrieves the
baseline Java files from the pinned Git commit without switching branches, then
compiles both baseline and current production `ResearchEngine` with the same host
harness. There are three fresh JVM forks per version, each with a first sweep,
30 warmup sweeps and 50 timed sweeps of all 38 questions. Rotating query order
reduces fixed-position effects. Index timing excludes reading the TSV file but
includes parsing and construction. These are host timings with ordinary OS caches
and JIT behavior; they are not cold-storage or phone benchmarks.

Android instrumentation loads the real validated archive, builds the production
index, and verifies IDs, scores (tolerance 1e-8), candidate counts and lexical gate
decisions against the host for all 38 questions. It then runs 20 warmup and 30
timed sweeps. Its load timer includes archive parsing, integrity validation and
index construction, unlike the narrower host index timer. No Activity or model
inference is involved. The app's active pack and model are not replaced by this
instrumentation; fixtures are isolated under `files/retrieval-tests`.

The host behavioral contract also checks unknown-term zero-candidate lookup,
selective postings, case/repetition invariance, ranking expansion that does not
satisfy exact coverage, real source lookup, concurrent determinism and immutable
results. Frozen questions and required source groups must actually be retrieved;
file presence or the test runner merely starting cannot pass.

## Metrics and interpretation

- Group coverage@4: per-present-question fraction of required groups with at
  least one labeled source in the top four, macro-averaged over 20 questions.
- MRR@4: reciprocal rank of the first labeled relevant source, zero if absent,
  macro-averaged over the same 20 questions.
- Group coverage@2: additional diagnostic for the two-source prompt limit. This
  does not establish that the 400-character excerpts contain the needed facts.
- Explicit distractor hits: appearances of specifically labeled distractors in
  the top four. Other unjudged hits are not automatically treated as irrelevant.
- Absent-evidence blocking: whether the existing lexical/excerpt gate blocks
  generation for ten absent cases. This is not a semantic absence detector, and
  the supported-case blocking count is reported alongside it.
- Candidate passages: unique scored posting documents for the new index; the
  baseline examines all 186 passages even for absent queries. Candidate means are
  over the 30 scored cases. Query timing aggregates include all 38 questions.

Full acceptance requires the frozen coverage/MRR floors (0.8/0.65), no group or
MRR regression against the measured baseline, all absent cases blocked, an
improvement in group coverage or reduced passage examination, behavioral index
contracts and Android parity. Timings are measured but not a flaky wall-clock
pass threshold. Explicit distractor counts and supported-case blocking remain
reported tradeoffs, not hidden behind the aggregate pass result.

This corpus is only 186 US/history-heavy passages. Full development coverage is
not unseen-query accuracy, broad coverage, answer quality or physical acceptance.
The index has more construction work and extra postings memory; no peak RAM,
large-pack scaling, sustained thermal behavior or phone cold start was measured.
See [raw results and failure analysis](evidence/retrieval.md).
