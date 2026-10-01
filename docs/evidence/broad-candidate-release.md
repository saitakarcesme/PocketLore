# Task213 repair: release-v5 development candidate

The previous audit-only checkpoint `16d6bd2` did not satisfy this task. Its failing release log, inventory and deferred report remain preserved, including [the pre-repair report](release-v5-history/broad-candidate-release-before-repair.md). This repair freezes and exercises the **actual current development candidate**, with reference, science and reviewed broad editions. It does not promote the host-only4B model or close the approved full-scale/final-product replan.

## Exact identity and checks

APK SHA-256: `3d804882ea576fb5ebdd29144a88fa8002c99efbd97c45323928a7c8a1d2e98f`,15,669,266 bytes. Application source and production model/admission are unchanged from task300; only tools, documentation and inventory changed. [release-v5 manifest](release-v5/manifest.json) pins every APK entry, DEX, both ABI inference/index libraries, assets, signature, source files, model/packs and raw demonstration evidence. No DEX identity is omitted. The debug signer remains the installed development signer; no production key was created.

The [distribution inventory](../distribution-inventory.json) records123 resolved build dependencies,13 llama/static link inputs and10 SQLite-index link inputs per ABI, installed tooling/full notice identities, production/optional model roles and data provenance. SQLite3.53.4's public-domain notice is byte-matched in the APK. Its pinned source and separate library do not replace platform SQLite. Existing task300 notices already describe this component; no new runtime dependency was added here. The previous inventory is [preserved verbatim](release-v5-history/distribution-inventory-before.json). Unknown build-tool redistribution terms, independent reproduction and production signing decisions remain open.

The new release checker retains forced byte-identical rebuilds, exact APK/source/evidence/inventory checks, signer/permission/runtime-dependency audits, deterministic reference/science rebuilds, host behavior and distribution regressions. It adds three-edition fresh-install assertions, real generated citation navigation, source/license inspection, rollback/resource assertions, six damaged-demo regressions and actual changed/missing receipt checks through the same hash validator. The existing distribution checks mutate actual copied native/build/notice artifacts as well. Historical release-v4 tools/evidence and task210 failed/evaluation-only editions remain intact; `tools/verify-release.sh` now selects the explicitly versioned v5 checker.

[Freeze verification](release-v5-checks/freeze.log), [required Android build](release-v5-checks/android-build.log) and [required plain release check](release-v5-checks/release-check.log) preserve outcomes. These are rig development-candidate checks, not publication, product acceptance or independent clean-machine reproduction.

## Fresh offline installation, not restored app data

The [protocol](../../tools/release/broad/protocol.json) was committed at `861eacd` before execution. The test archived only PocketLore's known fixture files/cache/code_cache into ignored rig storage:3,371,854,336 bytes, SHA `43a22b5dc4c3c0fe03c4ee0ccde52526d9957f9b5b5994da8558d2d45d77f213`. Safe archive paths were checked before uninstalling only the app and its test package. No archived data was restored, unrelated user data removed, service/emulator restarted, branch switched or main advanced. The prior task300 bulk collections remain in that preserved host archive; they are not counted as currently installed.

Fresh installation asserted no saved model and an empty imported catalog. Actual local DocumentsUI/SAF import then installed the pinned model, reference, science and reviewed broad archives. The model also reloaded after a process restart. [Summary](release-v5/summary.json) and `model-ui`, `reference-ui`, `science-ui`, `broad-ui` receipts include real controls, XML/screenshots and hashes. The run recovered from failed UI automation without repeating the uninstall or restoring data. Failed clipped-row selection, stale picker task, disabled import-button timing and early license-dialog inspection are preserved under the run's failed directories; fixes were in the test harness, not application behavior or answer wording.

| Asset | Bytes | SHA-256 |
|---|---:|---|
| Production Qwen2.5 0.5B GGUF |491,400,032|`74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`|
| Reference archive |159,327|`567e9bbbaab896826809ec20f81ae1c4b3f421b011931edae0989d28cfce10ea`|
| Science archive |31,183|`c69f31299553f4a1168eaa0400129fd5e41f21b4354248a0e2b97a87546ff274`|
| Reviewed broad rendered-v2 archive |46,339,444|`b8d18801b099402205938979ab2bb44ee9a316f06f030aab789cf93ba3605012`|
| Reviewed broad SQLite index |121,401,344|`9009b19de43f851a815d1797779a94ab47077cc2fc5b3dfe70fc4bdf9a097386`|

The final active catalog has3 editions,1,113 distinct documents and40,891 passages. Actual collection controls disabled the broad edition, a distinct process verified only the two small packs/210 passages and no broad source IDs, then re-enabled it. Another distinct process verified all3 active editions and40,891 passages. Mode counts describe state at each mode's end: `combined` ends disabled, `disabled` ends re-enabled, `enabled` ends fully active. [Combined](release-v5/combined.json), [disabled](release-v5/disabled.json), [enabled](release-v5/enabled.json).

Airplane mode1, Wi-Fi0 and mobile data0 persisted. The APK requests no permissions, the runtime classpath has no dependencies, and Play Services/Play Store packages are absent. This is offline emulator evidence, not physical-radio or packet-capture certification.

## Real generated citation navigation and source inspection

Both actual production JNI runs generated18 tokens:

> [S1] Headlamps are the recommended light source because they are hands-free.

The production controller rendered citation `p567e9bbbaab896826809ec20f81ae1c4b3f421b011931edae0989d28cfce10ea_essentials-e772a5a729be28b9`. The test clicked the actual `ClickableSpan` obtained from the displayed answer TextView before unloading the model; the resulting visible dialog contained that exact citation and NPS excerpt. This was not supplemental source-button substitution, captured-draft playback, a null generator or fallback counted as generation.

**Builder source assessment:** the single claim is supported and complete for the fixed narrow headlamp question because the actual cited NPS excerpt states the hands-free reason. It closely repeats source wording. It does not establish broad synthesis, general source entailment, selected4B quality or unseen generalization; independent source/human assessment remains separate. The raw prompt retains irrelevant Constitution evidence as an observed retrieval limitation.

Separate model-unloaded searches inspected science and broad source buttons, including the Acid passage, edition namespace, article revision, original URL, rights, contributor/history links and source/passage hashes. These rows remain labelled FALLBACK with `invoked=false`. The actual offline CC BY-SA4.0 license dialog was opened and its legal text captured. Seven dialogs per combined/enabled run are retained; the builder visually inspected the [Acid screenshot](release-v5/enabled-3-combined-0.png). Original formula/footnote text is visible as source content, not fabricated citation IDs.

## Rollback and measured resources

[Rollback evidence](release-v5/rollback.json) exercised a corrupted real reference archive, cancellation before copying and during broad copying, then valid duplicate-broad retry in the same process. Every failed import retained the exact catalog and model hashes and removed staging. Duplicate retry succeeded without changing either. Durations939/934/933/1508ms include post-operation model/catalog hashing; they are **not isolated cancellation latency**. Full replacement with a different broad edition remains unsupported/unmeasured; duplicate retry is not presented as an upgrade test.

| Measurement | Observed emulator value |
|---|---:|
| Logical APK + model +3 archives + broad index |675,000,596 bytes|
| Actual app files before/after rollback, including test evidence |662,689,964 bytes each|
| Sampled import archive/index staging allocation |167,751,680 bytes|
| Duplicate-retry staging logical peak |46,339,444 bytes|
| Duplicate-retry sampled app-files peak |709,029,408 bytes|
| Logical cache at rollback |0 bytes; final directory allocation8KiB|
| Final app files filesystem allocation |647,292KiB|
| Final package allocation |15,332KiB|
| Canonical external SAF input copies |537,929,986 bytes|
| Full emulator `/data` used/free after run |1,477,668 /4,462,264KiB|

[Storage observations](release-v5-checks/storage.json), [import samples](release-v5/import-storage-samples.jsonl) and rollback JSON preserve definitions. Import samples use allocated bytes approximately every0.5s; duplicate-retry sampling targets5ms and measures logical staging bytes. They can miss shorter peaks. A conservative sum of measured app files, APK, canonical SAF inputs and another full sampled import stage is1,384,040,896 bytes, below50GB for **this bounded selection**; it double-counts some retained incoming content intentionally. Whole-emulator filesystem usage also includes other system/fixture files. The3.37GB backup remains on the rig, not installed. No full41GB bulk inventory or full-scale update fit is inferred.

Cold-process Activity/catalog/saved-model readiness took2298 and2379ms, with opening PSS604,585 and604,445KiB. These include UI setup and model readiness; they are not isolated index-opening or fully cold storage timings. First-token/controller-total measurements were24,280.223/26,308.817ms and23,985.608/25,834.085ms, excluding initial retrieval/model load. End PSS77,569/73,733KiB follows deliberate model unloading for source inspection. Rollback-only process sampled PSS63,041KiB, without a loaded model. Raw process RSS/high-water/swap are retained. These are x86_64 emulator observations with OS caches, not percentiles, physical-phone RAM, thermal or OOM acceptance.

## Reproduce and interpret this freeze

Use the installed rig toolchain and pinned assets. `python3 tools/release/broad/fresh.py` creates a new ignored run, archives only project fixture app data, uninstalls/reinstalls, imports via local SAF and executes the protocol. Its `--resume <run>` option reuses recorded successful imports and the proven fresh state; failures remain separate. The rollback instrumentation is built through the same `source.gradle` with runner `org.pocketlore.app.ReleaseRollbackInstrumentation`; its result is retained as `rollback.json`. `observe_imports.py <run>` observes storage without changing application state.

`bash tools/verify-release.sh --freeze <completed run>` refuses to overwrite a manifest and freezes only after the behavior assertions pass. Normal validation uses `bash tools/android-build.sh` and `bash tools/verify-release.sh`. The latter replays immutable actual-device receipts and runs real build/host/integrity regressions; it explicitly does not pretend to launch another fresh emulator experiment during replay.

The approved final-scale replan remains open: selected4B Android qualification, task300 bulk/right-safe useful answers, full inventory/update45GB target/50GB hard limit and independent unseen comparison are not closed by release-v5. Existing301/302 and answer-architecture work remain the concrete follow-ups; no duplicate task or dispatch was created. Clean-machine reproduction, production signing/key ownership, physical Android/GrapheneOS and human acceptance stay separate. No private holdout, production key, service change, publication, push or main advancement occurred.
