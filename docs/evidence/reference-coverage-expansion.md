# Reference coverage expansion — in progress, not accepted

Task 480 preserves accepted task 470 at `a0cba18` as an immutable historical seven-document candidate. This edition is separate; no unseen or historical holdout inputs are used. No task-480 device access has occurred: the required exclusive emulator-5564 lease is pending.

## Frozen source selection

`tools/packs/reference-expansion/selection.json` selects 140 distinct existing Wikipedia article identities across 20 subject families before writing new public development questions. Its SHA-256 is `21dab3107d7267b7a4ec79eeba32d7677cff087ecc5a354746a65779086bc29a`. Exact prior HTML/revision bytes are reused without redownloading. Selection is neither a rights disposition nor installed coverage. At least 100 admitted distinct documents and 20 meaningful families remain required.

The approach retains complete bounded paragraphs, original HTML, revision and contributor links, publisher license/terms, acquisition records and an explicit transformation ledger. It excludes unresolved third-party quotations and warned content. Independent per-source review must precede admission. New source briefs remain labeled exact excerpts, never generated-answer successes. No model selection changes are planned.

## Implementation and verification plan

Add shared offline license records and source-text span binding to the existing pack format, preserving old pack compatibility and admission limits. A full license repeated per document would exceed the current 2 MiB manifest bound at this size; shared license references avoid that duplication. Verify complete paragraph mappings, UTF-16 boundaries, unique document identities and rollback on corrupt or missing source/rights metadata. Integrate through the existing catalog, not topic-specific runtime rules.

Freeze public development questions after source selection and before retrieval changes. Exercise general retrieval, mixed-topic/multipart requests, false premises and absent/private/current information. Source-level builder assessments and independent inspection are distinct from unseen generalization.

The new candidate must bind build inputs, APKs, installed state, corpus, settings, model selection and device receipts under a new freeze ID. Original task-460/470 evidence must remain unchanged. Storage sampling must distinguish the new subset from historical full inventories and include staging/rollback/provider copies where observable.

## Open gates

Source dispositions, admitted counts, implementation, development tests, required checks, independent criticism and new candidate/device evidence are not yet complete. Exclusive modern5564 ownership is required before device work. Physical Android/GrapheneOS, full-capacity modern Android, TalkBack, generated quality, broad rights clearance, independent unseen/matched comparison and human acceptance remain open. No competitive claim follows from this task.

## First implementation checkpoint

The schema-2 importer now carries complete selected source text, shared offline licenses, rights-review and source-packet identities, and contiguous exact paragraph bindings. It rejects missing identities, duplicate source identities, source-text hash mismatch, missing/changed licenses, unadmitted rights, fractional offsets, shifted paragraphs, trailing unbound text and split Unicode surrogate ranges. Existing schema-1 packs remain readable; this is integrity validation, not cryptographic proof of publisher authenticity.

The initial Android build passed on LLMRig (`downloads/reference-expansion/build-initial.log`), producing APK SHA-256 `993f5932b80c8d77820252353c14517b04b5ab7d52d1037c73b06dc1177b6d9a`. This is compilation only, not device validation. Gradle is configured for two workers and a 2 GiB heap; no total-process memory claim is made.

The original extraction packet is frozen at SHA-256 `abbb800f0c837f401cb9c9d0f3ccf836e191c9f06d797917ef7678833ee392bc` in `downloads/reference-expansion/source-packet.json`. It contains 140 candidates and 1,095 candidate paragraphs, not admitted coverage. Independent source review is explicitly narrower: inspect first-paragraph admission plus source-wide rights/context; later paragraphs remain excluded. Discovered missing attribution notices, formula/list lead-ins and misplaced topic content must remain recorded, not promoted by hash matching.

The new public development protocol contains 53 questions across the selected families, paraphrases, four multipart requests, six unavailable-evidence controls and three misleading premises. `tools/evaluation/reference-expansion/development.json` SHA-256: `7ffc25a4adfcd04a19ec09dd37e23efa0c2c42ede53115986771aeb06d76d20d`. Questions were frozen after source selection and before retrieval changes or execution. Excluding an expected source records a miss, not permission to rewrite the expectation. These builder-visible cases establish no unseen generalization.

## Independent source disposition and fixed host result

Source review admits **120 distinct documents, one complete selected paragraph each, across all20families**. Thirteen candidates need further evidence and seven are excluded; no later paragraphs are admitted. Exact decisions and source-specific warnings/credits are in `reference-coverage-expansion/source-review.json` (SHA-256 `987d9b904c49afaf42f7529a1ba3b1a94dd713c0764ea6a529c494e4dea0f568`). The reviewer inspected original context, not only checksums. Imported CC BY notices missing from the preliminary extractor are preserved as findings; unresolved affected candidates are not promoted. Original HTML/footer and revision links remain source authority, not this report.

The deterministic pack is **501,453bytes**, SHA-256 `61a5d472c8dd5445893f0d10565332d2dfea4e0e35557f6bd8c397dda5e8a135`. Shared license storage avoids repeating the20,138-byte legal text in every indexed passage, preserves the current metadata/admission limits and restores complete legal text in the source reader. Quotes bind the shared legal text as well as text/provenance. No retrieval ranking, question-routing table or model selection was changed.

`source-artifacts.json` pins312original/derived/rights/acquisition artifacts; the140reused original HTML responses total73,824,999bytes. These bytes already existed and were neither redownloaded nor duplicated into the app/Git.132per-document metadata files derive byte-for-byte from receipted original batch responses; eight are standalone responses. Derivation is explicit, not a fabricated per-document HTTP receipt. Full contributor histories are not newly captured; exact history links and source-specific attribution dispositions remain a limitation, not a claim of exhaustive legal clearance.

The fixed host run `downloads/reference-expansion/host-20261002T120622Z-88748f` exercised the actual Java source-brief controller over the new edition alone. Independent inspection found **35useful source briefs/53public development cases**, **six appropriate absent outcomes**, **12nonabsent failures**, and **zero unsupported attributed claims**.43quoted routes and54verified quotation occurrences are not the usefulness count. Failures include absent reviewed block-cipher material, admitted-source lexical misses, incomplete food-preservation substitutes, irrelevant extra quotes and partial multipart coverage. The complete outputs and case-level review are retained in `host-run/` and `host-source-assessment.json`; no failed question or source obligation was rewritten.

Host observations: Java child maximumRSS93,568KiB, index open20.118ms, one-pass per-question p50=1.469ms and nearest-rank p95=7.433ms (53different questions in oneJVM). These are **not Android, physical phone, cold-process, first-token or generated-answer measurements**. Source reconstruction rejects missing/changed originals, shifted original offsets, missing/denied review and changed license bytes; host auditing rejects missing/changed output and changed assessment bindings. These checks do not substitute for device behavior or unseen evaluation.

## Current checks and preserved failures

The plain required Android build passes, and production plus new instrumentation compile. Current APK SHA-256 is `21a6efc62c73f28871619bb4806f264a4dbd1c9e663a9256506972ab353341f5`; the compiled testAPK is `b8ab30b9c9096ed356c15c7dda4307723f13c8370173997d86563cdb941a2721`. No task480 APK has been installed.

Both current required behavioral checks remain **FAIL/incomplete** because fresh leased-device evidence is unavailable. The old general-research checker correctly rejected changed build inputs; that failed invocation remains preserved. The wrapper now audits the new candidate explicitly, retains the>=12useful-current-Android-brief gate, and leaves historical460/470 records unchanged. `--historical-460` is for the historical candidate in its matching checkout, not permission to relabel its receipts as current.

Preserved failures include a Gradle invocation with a relative init-script path (resolved under `android/`, then corrected to the exact absolute path), a host launcher unavailable `/usr/bin/time` failure before Java execution (replaced by isolated child `getrusage`, without repeating generated inference), and both incomplete behavioral checks. Original failed launch directory/compile files remain; the launch exception was observed in tool output, not reconstructed as a new raw receipt. Build/check logs and command exits are copied into `verification/` with original paths and hashes.

## Unresolved device dependency and continuation

A **new exclusive coordinator lease for emulator5564 has not been received**. No device commands, protected5560/5562access, service changes, inference, recognition or new bulk downloads occurred. The compiled task-specific instrumentation/driver is unexecuted: it covers real Activity/provider import, source navigation/Back, export cancellation/retry, archive roundtrip, corrupt/rights/identity/offset rejection, retained catalog and cold reopening. Its actual success, accessibility/screenshots, latency and cleanup are unproven until run.

The new HANDOFF is intentionally `incomplete`, not a runnable installed freeze for evaluation. Next: provide the exclusive5564lease, run the bounded new candidate, inspect actual Android outputs, finish before/during/after logical/allocated/package/provider/staging/rollback/reservation measurements and exact retained model/settings/corpus/APK bindings, then obtain supervised criticism. Actual active counts remain unknown;120documents describes the built edition, not installed app coverage. Sampled storage must not be described as a continuous peak. Historical303/390full inventories,400blocked and410historical provenance limitations are unchanged.

No model/selection change, generated success, physical12GBRAM qualification, GrapheneOS, TalkBack/human comfort, broad rights clearance, new unseen generalization or matched-rival superiority is established. This checkpoint is substantive but **not builder completion or task acceptance**.

The final host compilation is bound to exact implementation checkpoint `a1c628f7033918908d3a2fffda640a892cc4a66e` by `build-bound/source-inputs.json` (SHA-256 `0e178b2ad8339b20070aad35092cecbfdfb28ed69f057d61812eecd162ff98bc`), with unchanged inputs before/after compilation and preserved binary copies outside Git. Production/test APK hashes remain as above. All six native payload hashes match the saved470APK byte-for-byte; this is archive retention, not new runtime compatibility evidence. The production model pin file is unchanged (SHA-256 `2d932887a64251c6561f4082739136be2a204728c8acd8fb7a1a0eff69526d97`). Host scratch storage is separately sampled in `build-bound/host-storage.json`; all task480 Android storage/peak fields remain explicitly unknown.

## Repair-1: recovered implementation and stricter unexecuted collector

Recovered the four useful task480 commits onto the repair checkpoint branch without switching branches or changing accepted470. The frozen selection, source packet, independent dispositions, edition, public development cases and historical host outputs are unchanged. The reported critic blocker remains unresolved: no fresh exclusive5564lease has been received, so no device command or installation was attempted. The older runtime state is not a lease.

The collector now preserves run-owned production/instrumentation APK copies, checks retention of the resident page-size model fixture, and samples provider storage before/staged/after. Instrumentation now waits for initial Library loading before the import action. A bounded re-import of the same edition samples the actual production pack reservation during a real64KiB partial write, independently traverses app/package files with device/inode deduplication, and checks reservation release and exact catalog retention. The verifier recomputes logical/allocated totals and compares the independent covered-byte observation to the production meter. The existing pack reservation conservatively includes two256MiB database allowances plus17MiB filesystem/verification headroom in addition to archive bytes; this is a reservation, not a measured allocation or continuous peak. These new device assertions are compiled but **unexecuted**.

Repair receipts are in `reference-coverage-expansion/repair-1/receipt.json`. The initial instrumentation compile failed on an ambiguous Java Path import; the corrected compile passed. The initial synthetic validator positive fixture had an incorrect declared byte sum; its failure is preserved, and the corrected fixture passes alongside six negative mutations. Synthetic receipt checks validate collector logic only. Required `tools/android-build.sh` passed; both required behavioral scripts exited1 at the explicit incomplete-handoff gate. No historical run or host test was substituted for new Android evidence. The earlier statement that synthetic tests passed was corrected after reading their saved failure log.

The HANDOFF remains intentionally incomplete and retains its historical build binding. It must not be described as a new installed freeze. The next dependent step remains a coordinator-issued exclusive5564lease, actual bounded execution, source inspection of the resulting Android outputs, measured storage/retention, and supervised review. All prior physical, rights, generated-quality, unseen-evaluation and release gaps remain open.

## Repair-2 recovery: external device ownership remains unresolved

Recovered the complete tree of failed checkpoint `a65c424cf664ed236cb9823f24aede13f4266bb9` onto the current repair-2 checkpoint branch; the recovered tree matched exactly before this task-ID update. The collector now recognizes a coordinator-issued exclusive lease naming repair-2, while retaining serial, exclusivity and expiry checks. Python compilation of the changed collector passed; this is not a device test.

The authorized modern-android runtime state still describes the historical APK `3873ba23b6cda8268ec77ced1362a2e3230751d09f7ae111cfecb1795ece364e` and contains no new exclusive lease. An explicit lease was requested; none has been received. No Android commands were issued. The unchanged behavioral failure was not rerun, and no host matrix or source acquisition was repeated. Prior build and failing behavioral receipts remain historical, not fresh repair-2 results. Required installation, storage, source-output and current-candidate behavior remain unverified, and the HANDOFF remains incomplete. The next action requires actual exclusive5564ownership, not another collector-only or documentation-only repair.

## Strategy-change checkpoint

See `480-expand-reviewed-reference-coverage-20261002a-strategy-change.md` for the required failure analysis and execution design written before this change. Recovered the prior implementation and improved failed-transport receipt acquisition: preserve partial output and command identity, attempt actual phase retrieval, then fail on unsuccessful transport. Four local subprocess tests pass; no Android behavior follows from them. Exact test receipt is in `reference-coverage-expansion/strategy-change/receipt.json`.

The new exclusive5564lease is still absent. No device commands or repeated matrix/check attempts occurred. The expanded edition remains uninstalled by this task, the HANDOFF remains incomplete, and all required device/quality/storage review gates remain unresolved. A subsequent ownership grant is necessary to proceed; another host-only repair cannot establish completion.
