# Manual evidence comparison — task 440

The bounded manual workspace passes the recorded Android development checks. This is extractive organization of user-selected quotations, not synthesis, generated-answer success, independently supported comparison conclusions, or product acceptance. CF-08 is not satisfied and task 302 remains blocked.

## Product and binding contract

In Saved, select two SOURCE snapshots and choose **Compare selected (2)**. Saved research records cannot be selected as source evidence. Name the two subjects, add up to six named dimensions, then choose literal text using Android's text selection in each source snapshot. Every cell starts Unknown. Labels and notes are explicitly personal input, and every quotation is labeled manual/extractive with relevance unverified. Nothing assigns quotations or decides a verdict automatically. Stacked subject cards keep the grid usable on a narrow screen.

Rename/reorder dimensions, swap subjects, replace/clear quotations, save a separate personal note, and reopen through **Notebook actions → Open saved comparisons**. Source links reopen the exact saved snapshot with its identity checked. Export comparison uses the existing cancellable SAF writer; Share comparison uses the existing plain-text sharing path. Text retains identities, literal quotes, provenance and explicit Unknown gaps. Share chooser delivery was not independently exercised in this task; actual SAF retry bytes were.

`ComparisonStore` is additive: existing Notebook records are not migrated or rewritten. At most 32 comparison files of 64 KiB each are stored in `files/manual-comparisons`; labels are at most 80 characters, notes 2,000 characters and quotations 1,200 UTF-16 units. Atomic staged writes reserve `ResourceStorage.stagePeak(131072)` through the accepted task-420 contract, fsync, replace, and release on exit. This does not extend reservation enforcement to provider-owned output or every existing Notebook/cache write.

Snapshot SHA-256 covers the encoded array of record ID, creation date, kind, title, question, body and provenance. Mutable personal notes/bookmarks are excluded. Each cell binds that snapshot hash and exact half-open UTF-16 offsets **in the saved snapshot body**, not claimed original corpus byte offsets. Surrogate splits are rejected. Deletion/change, corrupt text/hash or stale offsets produce an explicit Unknown gap, never a displayed stale quotation. Original snapshot provenance is retained verbatim. A reference is not a copied perpetual source: deleting the original snapshot intentionally makes its cells unavailable.

## Frozen development inputs and exact run

Three constructed public development comparisons were committed in `f9c83f0` before implementation: water conditions, dated travel statements, and Unicode/formula notation. They are test snapshots, not added corpus facts, source-rights clearance or evidence of factual comparison usefulness. Their exact JSON SHA-256 is `210225f3530e44141bc6ed8c180ad13c822ce870d9628194fc093b646fe695d3`.

Final tested source checkpoint: `aefcac1` (full commit and per-file hashes in `evidence-comparison/verified-run/source-inputs.json`). Source/build manifest SHA-256: `259a8ff75de6e919c0a37b219f9c871409be6a12f00f14925680f764e621ab74`. The source map was captured before build and verified unchanged afterward. Build configuration was two Gradle workers and 2 GiB heap; this is not a measured total-process memory peak.

Run `20261002T040237Z-b938bfb3` used **emulator-5560, API 35, 4096-byte pages**, no other device. Boot ID remained `59ebd1a1-2fbf-4b25-aed7-2672c2d46604`; font scale remained 1.0. Production and instrumentation APKs were installed with replacement, without clearing data or uninstalling, and their installed hashes matched immediately and at the end:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Production APK | 22,719,262 | `ebb1aab49eb9e4b55f1c8e0ec60c38368f877d0b6132acbdc935b15ba84ccd9e` |
| Instrumentation APK | 431,945 | `7b634f10fd4290939116f4b0d4fdfe1435e2a2e95ab7349c747769d96765cf3b` |

`bash tools/android-build.sh` passed (preserved `required-build.log`); the fresh behavioral checker also built this exact app/test pair and passed. Its first phase contains 67 successful assertions and its process-cold phase 25. Android transport exited zero and decoded raw instrumentation receipts match the JSON reports. Offline cross-artifact verification of the final run passed after capture.

The actual UI checks cover Saved creation, native text-selection confirmation, source-reader identity, note saving, Activity recreation, dimension reorder and subject swap, clearing to Unknown, saved-comparison discovery after process death, and exact export. Three still-populated store comparisons retain their literal bindings across process death; a fourth UI comparison retains its cleared Unknown state. Some setup mutations use actual Activity/store methods rather than keyboard automation; this is not exhaustive manual usability testing.

Negative behavior includes research-record rejection, corrupt JSON, changed literal/hash, shifted offsets, missing source, split Unicode character and seventh-dimension refusal. The receipt validator rejects missing cold evidence, corrupt receipt bytes, stale run identity and changed installed-test identity. These are bounded development regressions, not hidden evaluation.

A deliberately blocked test destination was cancelled in **42 ms** and a same-process retry wrote exactly the exported comparison bytes. The blocking transport stress payload is explicitly test-only text, not evidence. Picker cancellation was also checked. Provider-specific refusal to close and partial destination cleanup remain platform limitations; these results do not establish cancellation bounds for every document provider.

## Retention, size and evidence packet

The measured saved UI comparison was **641 bytes**. App-private logical bytes changed from **3,248,686,551 to 3,249,278,283** (+591,732); allocated usage changed from **3,181,124 to 3,181,776 KiB** (+652 KiB). These samples include task screenshots, exports, raw reports and SQLite allocation, not just comparison storage and not a continuous peak or whole-device budget. Fixture comparisons and source records were deleted only after checking invocation ownership. Existing Notebook records retained exact identities, notes and bookmarks, with fingerprint `213990e010f2d6f2f51aa0334d05920f3f54028b93ad5a3fb44f96c8e9d96ced`. Existing model/selection/pack/optional-asset file hashes were unchanged.

The bounded committed packet is in `evidence-comparison/verified-run/`: actual raw instrumentation streams, decoded receipts, command exit records, source/build manifest, installed identities, storage observations, export, accessibility trees and negative controls. `original-artifacts.json` records exact original paths, sizes and hashes, including screenshots and all prior failed runs. Original files remain in `downloads/evidence-comparison/`; PNG/APK/model binaries are not committed. The manual-grid screenshot was visually inspected: English controls, literal/extractive warning, source title/hash, and scrollable subject cards are present. Long test labels truncate on rename buttons while remaining visible in the cards. Accessibility-node evidence records clickable controls; TalkBack behavior was not observed.

## Preserved failures

- Initial instrumentation build failed because `Files.readString` was unavailable in the Android compilation surface; the raw log is preserved and the implementation uses `readAllBytes`.
- `20261002T035445Z-6b4792ec` failed before quote confirmation because the accessibility root was unavailable. Its owned fixtures were removed in a separate identity-bound cleanup receipt, preserving original Notebook data.
- `20261002T035721Z-a690b4d7` selected instructional text rather than the clickable confirmation button and failed the saved-quote assertion. Automatic owned-fixture cleanup succeeded. The selector now requires an actual clickable Button.
- `20261002T035924Z-8dc3c728` passed, but its cleared UI comparison alone did not prove populated quote retention across process death. The final run adds that discriminating check; the earlier receipt remains intact.

Failed runs lack a complete successful-run after-state inventory and are not recast as passes. No old inference matrix, model execution, recognition, download, corpus expansion or emulator restart was performed.

## Remaining gates

This feature preserves manually selected text; it does not certify relevance, completeness, truth, redistribution rights or generated support. Full provenance can enlarge exported text and remains subject to the inherited bounded exporter. Provider-owned bytes, crash-orphan staging recovery, continuous update peaks, complete current corpus accounting, physical ARM64/GrapheneOS, 12 GB phone qualification, TalkBack/human usability and release approval remain open. Bulk rights, generated research quality and matched independent comparison remain open. Task 400 stays blocked and task 410's historical instrumentation provenance remains incomplete; this API35 run changes neither finding.

Independent criticism reviewed checkpoint `4c70173` and the original run, finding no bounded-feature blocker; its exact English conclusion and artifact binding are in `evidence-comparison/independent-review.json`. This is independent LLM criticism, not human or release acceptance.
