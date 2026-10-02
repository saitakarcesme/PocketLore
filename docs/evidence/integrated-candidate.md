# Integrated candidate regression — repair1

The required build and **fresh, non-reused seven-lane integrated check pass** on APK `9c71a32dbc2deac3d650c6849a335379bd2b005c1516437c613bcd0fcff7dd70` (22,702,878 bytes). This repairs validation/evidence handling; production application, model, corpus and answer policy are unchanged. Physical/device-quality/release acceptance remains open.

## Failed checkpoint and bounded repair

Checkpoint205901c previously reported passing builder runs, but the subsequent required run `downloads/integrated-candidate/20261002T013440Z` failed in the specialist lane. Its `adb am instrument` command returned nonzero with empty stdout. The prior checker asserted immediately, omitted return-code metadata, and did not collect the device report on failure. The original cause is **unknown**; no timeout, OOM, service or hardware cause is inferred.

The actual failed lane bytes, wrapper traceback and subsequently recovered device report are preserved in `integrated-candidate/repair1-failure/`. That recovered report says PASS but has no run ID: it is diagnostic only and cannot establish success for the failed invocation. The prior builder report is retained verbatim as `integrated-candidate/initial-builder-report.md`; its results remain historical, not a substitute for the failed required run.

Changes:

- Specialist commands now preserve stdout, exit code, elapsed duration and timeout metadata. Instrumentation failure triggers a diagnostic device-report capture, then still fails the check.
- Every specialist install/restart report carries a unique invocation ID. Both phases must match the receipt ID, exact pack hash and PASS status, and the transport must return0 with `INSTRUMENTATION_CODE: -1`. The aggregate also requires this binding; old unbound receipts cannot satisfy the current gate.
- Three host behavioral regressions execute a genuinely failing empty-output child command, a bounded timeout, and stale/missing report identity controls. A fresh successful device report is also mutated to require rejection of changed/missing run IDs and changed pack identity. No failed command is converted into success by recovering a JSON report.

These are evaluator/instrumentation changes only. Accepted UI, personal documents, recognition, model management, travel source rights, preview cache and specialist content remain unchanged. Original task390 readiness fixes and all historical failures were recovered on the existing checkpoint branch without reset, switch, push, main or orchestration changes.

## Current required execution

Commands actually completed:

```
bash tools/android-build.sh
bash tools/evaluation/check_integrated_candidate.sh
```

Current raw run: `/home/isa/Projects/PocketLore/downloads/integrated-candidate/20261002T014344Z`. **No `--reuse` option was used and no lane is marked reused.** Text/raw JSON receipts are committed under `integrated-candidate/repair1-passing/`; the complete raw directory retains screenshots with hashes in its manifest. No APK, model or binary input payload is committed. `repair1-SHA256SUMS` pins the new text evidence. Read-only verification is available with:

```
bash tools/evaluation/check_integrated_candidate.sh downloads/integrated-candidate/20261002T014344Z
```

All lanes rebuilt/installed the same application identity. The seven lanes cover:

| Lane | Current behavior |
|---|---|
| UI,5560 | Default/large font, keyboard/Back/edit restoration, notebook/source reading, blocked export cancellation and retry, cold restart |
| Documents,5560 | Real Library import→return→search, source offsets/ownership, format/error/cancellation, export/reimport and restart; model explicitly unloaded and `invokedModel=false` |
| Recognition,5560 | Real local OCR/WAV, editable result delivered to question through Activity return, no automatic research submission or source-evidence relabeling |
| Models,5560 | Provider import, optional model load, baseline reselection and real native-load failure recovery; generation disabled and no live generation context |
| Nearby,5560 | Existing diverse-place controls and exactly three reviewed six-field GeoNames cards, inspections/exports and corruption exclusions |
| Cache,5562 | Full existing31-shard catalog, actual28,440,308-byte raw block, cache eviction/cancellation/integrity and unchanged lexical ordering |
| Specialist,5562 | Eight real pinned documents, exact hashes/rights/formulas/offsets, combined search, eight source inspections, rollback/export/selection/restart and new run binding |

The specialist ID is `run-20261002T014854Z`; actual install instrumentation returned0 in5.853s and restart returned0 in2.847s. Both completion markers and fresh report IDs match. The three host receipt regressions passed inside that lane. Changed/missing raw reports and incorrect APK identity still fail the aggregate's disposable-copy controls.

The complete check took approximately**338 seconds** from timestamped run creation to final manifest (filesystem timing, not a performance benchmark). Supervising execution needs enough wall time for this measured serial suite. No runner/service timeout or configuration was inspected or changed; this duration does not establish the original failure's cause. Gradle remains configured for2 workers/2GiB heap, not claimed as measured whole-build peak RAM.

## Current resources and identities

Both ABI native LOAD/RELRO and APK16KB alignment pass for the actual APK. Execution is API35 x86_64 on existing5560/5562 only;5564 was untouched. Current model and pack/bulk catalog hashes match before/after. Baseline remains Qwen2.5 0.5B SHA74a4da8c…a9db;5560 uses the retained-object selection pointer and5562 the supported legacy `model.gguf` path. Full recognition hashes and exact source/collection pins are in current receipts. Optional1.5B is a load fixture on5560, not a promoted full-corpus model; the native failure uses the existing post-identity helper with a truncated fixture, not a claim that corrupt bytes pass normal checksum admission.

Current full5562 readings:

- Final logical app tree: **41,703,187,589 bytes**; plus APK: **41,725,890,467 bytes**.
- Final allocated app tree: **41,705,947,136 bytes**; plus allocated installed package: **41,728,667,648 bytes**.
- Largest sampled allocated app+package+test-provider footprint: **41,757,052,928 bytes**.103 complete logical/allocated samples per emulator; no reuse of previous sampling records.
- Actual oversized reader: **3175.11ms cold**, **1.52/1.46ms warm**, with28,440,308 temporary bytes cold and0 warm. Specialist reader openings: **144,74,71,11,34,30,39,40ms**.

These current observations are below45GB target/50GB hard cap for this installed configuration. Samples are periodic, not continuous peaks; no full-shard replacement, simultaneous generated-model/KV/reader envelope, physical thermal performance or modern5564 capacity is inferred. Unchanged corpus pins are retained, not a new full41GB rehash or source-rights clearance. Subset5560 sampled allocated peak including package/provider was4,388,093,952 bytes; it is not substituted for full-corpus storage.

## Review and remaining gates

The actual competitor source matrix was inspected in task390; its static evidence/acquisition/snapshot limitations remain, with no matched comparison or superiority claim. No model generation, new research inference, downloads, corpus expansion, private holdout access, global preferences or unrelated services were used in this repair. Existing bounded local recognition checks ran serially; the protected inference process was untouched.

The cause of the historical transport failure remains unproven, and forced termination can prevent diagnostic collection itself. Current required checks pass independently of that historical report. Physical Android/GrapheneOS, ARM64/current API37 runtime qualification, combined generation resources, full update peaks, unseen quality/generalization, bulk rights, matched comparisons, clean reproduction, signing ownership and human/external release acceptance remain open. Independent review of checkpoint `58b228e9385d134abf59f480684574d3806e8b71` found no bounded repair blocker; its exact English result is preserved in [repair1-independent-review.json](integrated-candidate/repair1-independent-review.json). This is independent agent criticism, not canonical runner review, human acceptance or release approval. Work stops after this bounded validation.
