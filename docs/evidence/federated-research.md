# Federated source research — API37 development evidence

Implementation `a3c108d` and run `run-20261002T132746Z-e27be3` exercise the admitted multi-collection source-brief path on existing emulator5564. Required Android build and `check_federated_research.sh` pass. This is a bounded development result, not canonical acceptance, generated reasoning, unseen generalization or superiority.

## Audit and implementation

The previous app already retained multiple packs and built a combined in-memory index; task481 had two active editions. The problem was not wholesale replacement by the last pack. Small-pack brief retrieval truncated its candidate list globally before collection-aware selection, offered no collection availability detail, and checked cancellation around rather than within lexical scoring.

The new brief path retrieves the bounded admitted index's matching candidates, partitions them by exact edition provenance, selects up to four diverse candidates per collection, and merges with shared deterministic relevance scores and citation-ID ties. The final candidate list remains four; the existing workspace keeps at most two quotes per subquestion and six subquestions. No question IDs or expected answers appear in product code. Collection availability reports candidate counts, explicitly not verified answers; zero-candidate selected collections remain visible. Existing Choose collections controls remain. Disabled collections are not indexed; their absence is a selection state, not a fabricated claim that their subject is unavailable globally.

Pack assembly now orders editions by hash for deterministic duplicate ownership. Existing snapshot/text/date/rights deduplication retains all edition provenance. A shared duplicate can report both collections while rendering once. Conflicting full citation identities fail closed. Local citation suffixes are namespaced by edition hash; exact source text, dates, rights and UTF16 quote offsets remain in the typed link and reader. Deleted-collection retrieval is tested in an invocation-owned isolated catalog; old saved source snapshots remain intentionally readable as historical snapshots, not live retrieval sources.

Cancellation is checked during lexical query/posting scoring, candidate grouping and merging, with retry after cancellation. Combined engines propagate checks between child calls. Synchronous disk providers remain cancellable only before/after their bounded call; this task does not establish interruption inside SQLite/native I/O. Browse-only bulk sources retain their existing source-review exclusion; no new broad-source or generated-answer permission is granted. Existing lexical relevance and availability heuristics are fallible and do not establish entailment or completeness.

## Frozen sources and new public development

`tools/evaluation/federated/development.json` pins source identities before the new questions. Sources are the already reviewed120-document edition (`61a5d472c8dd5445893f0d10565332d2dfea4e0e35557f6bd8c397dda5e8a135`) and accepted eight-document science supplement (`c69f31299553f4a1168eaa0400129fd5e41f21b4354248a0e2b97a87546ff274`). No download or source rewriting occurred. A small personal observing-notebook fixture is explicitly constructed test input, not external scientific authority or a real person's private data. Its original-byte identity and imported archive are preserved with user-supplied ownership/rights limitations.

Actual final selection retains four collections: seven-document reference,120-document reviewed edition, eight-document science supplement and one personal fixture. Counts are **135external source documents plus one constructed personal test document,167passages**; this is not new broad clearance for bulk data. The first real request has three subquestions and returns sources from reviewed, science and personal editions together. The baseline uses the **current controller restricted to the120-document edition**, not a separately rerun historical binary. It isolates collection availability rather than proving an old-code/new-code quality win.

| Public request | Single-edition quotations | Federated quotations |
| --- | ---: | ---: |
| Amateur astronomy; DNA; observing notebook | 3 | 4 |
| Earthquake causes; black hole | 1 | 2 |
| Magma/lava; acid | 1 | 2 |
| Chromosomes; chemical equilibrium | 1 | 3 |
| Observing notebook | 0 | 1 |
| Personal DNA result | 0 | 0 |
| Current observatory opening | 0 | 0 |
| Quantum taxi availability on Mars | 0 | 0 |

Counts alone are not usefulness scores. Raw baseline and final prose are retained for every request in both phases. Independent source inspection and code limitations are recorded separately in `federated/source-review.json` and `critic.txt`. In particular, chromosome selection can return packaging/etymology rather than the available introductory definition; additional excerpts do not establish completeness. No paraphrase, causal connection, multi-hop reasoning or generated synthesis is inferred by the renderer.

## Actual app behavior and preserved failures

New candidate APK SHA256 is `f14099efbb96f945b739fc88da7f1ecfba34a61f5d1a270faf052d3440d8035d` (22,735,646bytes); instrumentation APK is `41a2aebd2090b6772538492f547288600a6539c6a26605386af254820114954e` (466,878bytes). The run-owned APK copies, exact source manifest, installed/final hashes, command exits, raw decoded receipts and screenshots/accessibility records are bound in `federated/HANDOFF.json` and the run packet. All tested input bytes match committed implementationa3c108d. Native16KB artifact validation passes; no model inference was run.

Tests exercise actual science import confirmation/worker, personal conversion and library transactions, real research controls, citation navigation/Back and visible selection controls, plus production selection disable/restore, isolated remove/reload and cold selection persistence. Synthetic duplicate-ID/condition fixtures are labeled controls, not corpus facts. Source-reader behavior follows the actual environment: the notebook reached its existing200-record limit during testing. The final run uses the existing Read without saving path and verifies exact visible quote/citation bytes. It does not claim new source-history persistence; no user records were deleted to make tests pass.

Preserved failures include the initial asynchronous reader-entry race, an invocation that reported instrumentation success but lost its receipt across an **unsolicited emulator boot change**, and the full-notebook reader case before the existing fallback was exercised. The builder issued no reboot, wipe, clear-data or service command. The interrupted invocation remains FAIL; its missing receipt was not reconstructed. The subsequent run validates per-phase boot continuity and final state. Earlier successful intermediate runs are retained but do not replace final-candidate proof. No5560/5562or private holdout/independent-comparison access occurred.

Final boot ID `5a5b64be-c87e-45b5-b766-58f8d826fc83`, API37,16384-byte pages, font/rotation and resident model identities remained unchanged across the final run. Research selections and exact rendered outputs were identical after force-stop/cold reopening. The full notebook blocks new automatic saves; existing records remain intact, and source reading remains available without saving.

## Timing, memory, storage and limits

Eight distinct public requests were executed in each phase. Install-phase median request-to-result was 55.664 ms, nearest-rank p95 80.156 ms; restart median 61.212 ms, p95 111.944 ms. All individual timings are in federated/measurements.json. Only the first request in each phase is first-in-process; the rest are warm. These eight-case distributions are not repeated cold-load benchmarks, generation latency or phone performance. Timing excludes user reading/navigation and model load. End-phase PSS was 90,433 KiB and 88,590 KiB, not a continuous maximum.

App-private logical bytes changed from 626,169,905 to 628,605,040; allocated KiB changed from 619,648 to 622,144. Samples include retained task fixtures and isolated test copies; they exclude package/provider/whole-device ownership and are not continuous import peaks. Task420 admission budgets remain unchanged. Historical full-corpus303/390 receipts are not transferred to this subset.

The required checker verifies current source/APK/installed/transport/run/boot/settings bindings, UTF16quote identities, actual control assertions and cold output/catalog equality, with changed-artifact negative controls. Raw receipts for all invocations are included in the packet, not only passing summaries. Canonical review, independent unseen evaluation, physical ARM64/GrapheneOS12GBRAM, TalkBack/human usability, all-provider/update peaks, broad rights and generated-answer quality remain open. The next quality work should address source-paragraph completeness on newly frozen public diagnostics, not relabel this test set unseen or tune to private evaluation.

Independent review also found the initial condition fixture was compatible rather than contradictory. That weakness is preserved in source-review-initial.json. A separate pre-execution freeze, conflict-control.json, now specifies contradictory equally dated weather requirements; the final actual controller output retains both exact statements and typed citations without reconciling them. This constructed control is not a source fact or general conflict-detection claim.

The final readability adjustment places collection availability after quotations and abbreviates display hashes only; full identities remain in citations and source details. Synthetic contradictory snapshots now use the same date as their frozen text.
