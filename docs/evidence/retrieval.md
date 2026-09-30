# Task 040: measured retrieval on frozen development cases

Builder evidence from LLMRig, with production Java execution on the host JVM and
the existing AOSP API 35 x86_64 emulator `emulator-5560`. **No physical Android or
GrapheneOS acceptance is claimed.** No private holdout was opened, and no runner,
service, branch or global model preference was changed. Nothing was pushed.

## Frozen inputs and actual checks

The 30-case pack-specific development suite was committed in `753bcaa` before
retrieval changes: 20 supported questions and ten absent-evidence questions.
Judgments identify required source groups, alternative passage IDs and selected
distractors. The builder inspected real source text to author these judgments;
they are not independently reviewed gold labels or an unseen test set. The eight
original public pilot questions remain unchanged and were run separately as raw,
unscored diagnostics. Their private holdout was not inspected.

| Input/artifact | SHA-256 or immutable identity |
| --- | --- |
| Frozen retrieval cases | `045270377a2cc1792cef27842147a770404eb3da32123aa9a702378a6313130c` |
| Real 186-passage knowledge pack | `567e9bbbaab896826809ec20f81ae1c4b3f421b011931edae0989d28cfce10ea` |
| Baseline Git commit | `9c85536946138e4d805b99ec3f9cbdfe836a49e0` |
| Baseline ResearchEngine.java | `525d3d46b17ab6dcd761c73d6bea9aed9df212fd9d3a9cf0b56e2640136c7cd5` |
| Final ResearchEngine.java | `0ef583b829eb0e75d46c525b5153afb3489cdf26f730d2373039c70e3ce8d4c3` |
| Unchanged EvidencePrompt.java, both versions | `8391e702cbe9bbaa51edffdab3223c556f363be297e49d5bb8ceb0e85bb0ec06` |
| Final debug APK | `df1502cd602c3a97a3eb84615c50dd3bf13de93f0f7872a7959593c65903263c` |
| Retrieval instrumentation APK | `a0dfc21c7c0e4d6d282bbdc616a8267767f6b0844a182db60f5848aacdf38bd3` |

Final measured run: `downloads/evaluation/retrieval-20260930T232453.743445Z`.
The full evaluation took 10.500 seconds including host compilation/execution,
Android test build/install and instrumentation. Both required commands passed:

- `bash tools/android-build.sh`: PASS, Gradle reported 5 seconds.
- `python3 tools/evaluation/evaluate_retrieval.py`: PASS, with actual relevance
  assertions, behavioral index checks and host/Android parity for all 38 questions.

The existing starter's eight retrieval/corruption/citation checks, 14 host answer
routing/cancellation checks, and original public pilot freeze check also passed.
The answer routing checks use a synthetic generator only to test control flow;
no model generation, new factual corpus or answer-quality measurement is claimed.
Raw logs and all timing samples are in [final/](retrieval/final/).

## Measured change

The production retriever now precomputes BM25 posting contributions, visits only
query-related postings and caches normalized term frequencies. Limited inflection
folding and four explicit ranking expansion groups improve paraphrase discovery.
Body text has more influence than a document-wide title. Original text, stable
citations and exact-word answer coverage are preserved. See [implementation and
reproduction details](../RETRIEVAL.md).

The table uses the final same-run baseline/candidate comparison. Quality metrics
are identical across three JVM forks. Timing values are medians of the three
per-fork statistics, not confidence intervals or physical-device results.

| Metric | Baseline | Final |
| --- | ---: | ---: |
| Required-group coverage@4, 20 supported questions | 0.900 | 1.000 |
| Required-group coverage@2 | 0.875 | 0.975 |
| MRR@4, labeled relevant IDs | 0.875 | 0.975 |
| Explicit labeled distractor hits in top four | 1 | 2 |
| Absent cases blocked by existing generation gate | 10/10 | 10/10 |
| Supported cases also blocked by that gate | 17/20 | 17/20 |
| Candidate passages examined, mean over 30 scored cases | 186 | 21.533 |
| Host index construction, ms | 30.961 | 40.276 |
| Host warm-query p50, ms | 0.122754 | 0.018656 |
| Host warm-query p95, ms | 0.419295 | 0.060075 |

Host Java was 17.0.20.1. Each version had three fresh JVM forks, 30 warmup sweeps
and 50 timed sweeps per fork, rotating the order of all 38 queries. Each raw case
also contains first-sweep latency; this is not an OS cold-cache measurement.
Host index time includes parsing the already-read TSV and constructing the
retriever, but excludes file reading. Query time includes ranking and building
the existing evidence display text. Empty and absent queries are included in the
38-query timing mixture; the small corpus and query mix constrain interpretation.
The roughly 6.6-fold host p50 difference is local to this experiment.

Android validated and loaded the real archive and built its index in **157.717 ms**.
This includes archive decoding and integrity validation, unlike the host index
measurement. After 20 warmup sweeps, 30 timed sweeps over all 38 queries produced
**0.062368 ms p50** and **0.155818 ms p95**. All source IDs, scores within 1e-8,
candidate counts and lexical generation-block decisions matched the host.
These are emulator measurements; no model load or inference is in these timings.
Peak RAM, index serialization, large-corpus scaling and thermal behavior were not
measured. The extra postings cache costs construction work and memory.

## Failure analysis and preserved experiments

The original baseline raw results are retained in [baseline-frozen/](retrieval/baseline-frozen/).
They miss the required bedrock passage for “How do cracks in rock store underground
water?” and the illumination passage for “What should I carry to see in the dark
on a hike?”. Exact-word scoring favored related water paragraphs and generic
hiking/carry passages instead. Both required sources rank first in the final
retriever; no labels or questions were changed after seeing results.

The first indexed candidate used expansion weight 0.4. Its raw results are retained
in [candidate-1/](retrieval/candidate-1/): coverage@4 reached 1.0, but illumination
only reached rank four and MRR was 0.9125. The final weight 0.7 is explicitly
**development-tuned**, not an unseen validation choice. A single conservative
ranking list is used for all queries, not per-question routing or source-ID boosts.
The original candidate's lower ranks and distractors remain visible in its files.

Failures and limitations remain in the final result:

- The urban flood question also retrieves an Ellicott City paragraph with surface
  percentages that does not itself explain faster flooding. The Yosemite Valley
  camping question still includes the distinct Tuolumne camping paragraph. Thus
  the explicit distractor count rose from one to two; all retrieval metrics did
  not improve together. Both are lower-ranked than the required evidence.
- For the aquifer-recharge versus surface-runoff comparison, runoff first appears
  at rank four. The prompt still takes only two sources, so its selected evidence
  misses that source group. The rank-one artificial-recharge paragraph is not
  included in the frozen relevant-ID alternatives; labels are non-exhaustive and
  were not broadened after tuning to raise the score.
- Seven of ten absent questions still retrieve lexical matches. Generation is
  blocked by the separate vocabulary/excerpt gate, not by semantic proof that no
  answer exists. That same gate blocks 17 of 20 supported cases, including useful
  paraphrases. Reporting absent blocking alone would hide this substantial false
  abstention problem. Both versions also block all eight original pilot questions.
- Scores are relevance ranks, not confidence. Exact-word coverage can be shared
  by unrelated passages, and expansion can introduce word-sense errors. Neither
  retrieval coverage nor a citation ID verifies factual entailment, current travel
  conditions or the legal status of a historical provision.

Per-case before/after IDs, required-group hits, explicit distractors and missing
terms are in [failure-analysis.json](retrieval/final/failure-analysis.json).
No hidden failure was converted into a success flag: the final PASS means the
stated development floors, non-regression checks, absence-gate cases, reduced
scanning/improved coverage, behavior contracts and Android parity passed. It does
not mean all returned passages were relevant, all supported questions could be
answered, or independent acceptance was obtained.

## Release implications

The fixed pack has 186 US/history-heavy passages, and the new judgments were
written with that pack in view. This is a development regression suite. Next
independent work includes review of the judgments, source selection that covers
multiple question aspects, safer semantic coverage/abstention, larger licensed
packs and scale/resource testing. Phone and GrapheneOS acceptance, independent
useful-answer evaluation and competitive comparison remain open. No private
holdout tuning, external provider access or physical measurements are implied.
