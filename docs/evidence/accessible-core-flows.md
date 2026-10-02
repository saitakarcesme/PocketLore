# Accessible core-flow controls — task 450

The required build and status-bar check passed on source checkpoint `4c29fd5`, but a second independent screenshot review found low-contrast dark-reader navigation icons; its automated scope was incomplete. The earlier automated pass and independent visual finding remain historical evidence; the reconciliation is recorded separately below. No accessibility-compliance, physical comfort or product-acceptance claim follows.

## Scope and frozen protocol

CF-03 was used as a proposal, not as proof of product capability. The accepted 310/440 surfaces were retained. `docs/evidence/accessible-core/fixtures.json` was committed in `7dca54b` before changes: constructed public long-title, long-label, dated-source, missing-evidence and invalid-document fixtures. These are interface tests, not corpus additions, generated answers or held-out generalization. The frozen subject label has 81 characters; rejection is retained, and its first 80 characters exercise the existing maximum permitted label without changing the fixture bytes or runtime limit.

The four flows are Research composer/result/error; saved source reader/return; personal-document import/error; and manual comparison edit/source/export. The final matrix uses temporary Android font settings 1.0, 1.5 and 2.0, compact portrait width 360 dp and landscape width 640 dp on existing emulator-5560. Window height uses the existing display after bars/insets. Temporary font changes, Activity orientation and UiAutomation rotation are confined to the test; the system font preference is restored in the instrumentation finally block and checked again by the host finally block. Before/after font, rotation, auto-rotation and boot identities are captured. The host finally block restores preferences if a crashed instrumentation cannot do so. No reboot, clear/uninstall, other emulator or service change is involved.

## Targeted implementation

- Shared ReaderUi actions explicitly wrap instead of inheriting single-line/ellipsis behavior; full personal comparison subject labels remain visible and available as text-based accessible names. Navigation uses two columns at enlarged text in compact portrait and four in wide layouts.
- Personal-document controls use shared readable text roles, persistent field labels, 48 dp button minimums, polite status updates, colors and system/keyboard insets. Import/conversion/rights behavior is unchanged.
- Reader system insets now belong to a non-scrolling outer container. A captured failure showed the Close reader button half hidden under the top inset after restoring a reading position; the full-visible-control assertion was preserved.
- System-bar icon appearance is explicitly set through WindowInsetsController as well as the older flags. Transparent bars are evaluated against their actual backing surface, rather than assuming the color getter represents an opaque bar.
- Shared focused actions are explicitly revealed inside their scroll viewport, including nested comparison cards; competing animated focus scrolling is avoided on shared reader surfaces.
- Dynamically created Notebook export cancellation buttons receive the shared action style. Export/provider behavior is unchanged.
- The Research composer disables fullscreen IME extract mode, preserving the app controls in landscape rather than replacing them with an editor-only screen.

## Measurement definitions and limits

The test exercises actual production Activities, view layouts, source/store identities, empty-question error handling and bounded valid/invalid local imports. It does not submit a populated research request: the missing-evidence result is explicitly labeled a public UI fixture and is injected into the existing result renderer. NativePanel is manually unloaded before Research checks; there is no generation, recognition or quality measurement. Constructor model initialization may begin before unload; saved model files/selection are preserved.

Control checks use actual laid-out pixel bounds converted by current density, text layout ellipsis/height, full visible rectangles after scrolling, keyboard-navigation focus and accessible names. Screenshot and accessibility-node streams accompany every declared state. Text contrast uses actual TextView foreground colors against the known current production background colors, with WCAG relative-luminance arithmetic and a 4.5:1 threshold for the sampled normal text; this is not an exhaustive pixel/disabled-state/OS-dialog contrast audit. Light/dark reader content and status icon mode are sampled. Keyboard tests observe actual IME insets and keep the Research action reachable without dismissing the keyboard through a directional-key event. Keyboard-focus checks run separately with real DPAD input; this distinction is recorded per control. Source identity/reading position, editable question text, literal comparison bindings, notes and original Notebook records are retained.

The export check opens the actual system SAF picker and observes Back cancellation and return feedback; blocked-provider cancellation/retry remains the separate accepted 310/440 evidence and is not rerun here. The document fixtures are tiny local text/invalid JSON, not PDF/OCR/recognition or corpus stress. Only task-owned imported editions and Notebook/comparison fixtures are removed. Whole-device capacity, update peaks, unobserved provider usage and historical full-corpus receipts are not requalified.

## Preserved failures and harness corrections

All existing runs remain under `downloads/accessible-core/` and are bound by `accessible-core/original-artifacts.json`; `accessible-core/run-history.json` lists their actual outcomes. Initial attempts exposed the 81-character fixture boundary, cross-UID provider setup, a too-late Activity configuration override, focus assertions while in touch mode, and an opaque-status-bar assumption. Those are test failures, not successful qualification. The configuration crash left two marked source records; the explicit bounded recovery removed only those records and their comparison and recovered Notebook fingerprint `213990e010f2d6f2f51aa0334d05920f3f54028b93ad5a3fb44f96c8e9d96ced`. Its original rotation preference was restored and raw crash/recovery receipts retained.

The reader-close clipping failure was a concrete product defect, repaired by the outer inset container. A later landscape test correctly refused a landscape-width window still rendered on a portrait display; the harness now requires observed display rotation and records actual local font configuration before measuring controls. Additional retained failures cover focus-mode transitions, a landscape IME request before window focus, and nested comparison actions outside the visible scroll viewport. The latter persisted after removing competing test scroll requests and led to the shared focus-reveal fix. No failed receipt is relabeled as a pass.

## Initial passing matrix, before independent visual review

Initially tested source checkpoint **e8e638b**, run **20261002T044441Z-3fee2078**. Source/build-input manifest SHA-256: `9f7860be12066a75dc3da9a02547bea84206440310f0713f1237e9231249f818`. It records all tracked Android/tool input hashes, SDK jar hash, fixture hash and Gradle configuration (two workers, 2 GiB heap, not measured total process memory). The source map remained unchanged through the build/run and offline verification. `bash tools/android-build.sh` passed again after the matrix and reproduced the same production APK.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Production APK | 22,719,262 | `8761de36c94e1b5df2be0a7deb9ee7c0f4747573af65a5ce7c440e65eee93258` |
| Instrumentation APK | 439,969 | `041a9398f598c69aec0ab2162128d2742d242f877a6587e85a71a373b0dd6432` |

Both immediate installed and final package hashes match those built artifacts. Environment: **emulator-5560, API35, 4096-byte pages**. Boot ID before/after: `59ebd1a1-2fbf-4b25-aed7-2672c2d46604`. System font **1.0 → 1.0**, user rotation **0 → 0**, auto-rotation **1 → 1**, with no final-run host rescue required. Observed Activity font scales and display rotations are recorded in 30 configuration observations. Testing proceeds from 2.0 downward after the earlier local-override failure; all six frozen scale/layout combinations are required, and none is dropped.

The final receipt has **72 captured states** (12 per configuration), **150 control observations**, **30 foreground/background contrast samples**, and **1,645 successful assertions** including repeated line/bounds and lifecycle assertions; these are not 1,645 independent use cases. All sampled controls have at least 48 dp bounds, no text-layout ellipsis, fitting text height and full visible rectangles after scrolling. Keyboard-focus assertions run outside the IME-specific geometry check; the latter separately requires the keyboard to remain visible. Minimum sampled contrast is **7.2031:1**, above 4.5:1. No generated/retrieved answer quality is measured.

Per configuration the 12 captured states are Research composer, keyboard, empty-input error and labeled fixture result; source long-title and alternate theme; personal-document import and actual invalid-JSON error; comparison long action, edit dialog, export control and actual SAF picker. Additional asserted transitions include tiny successful text import and cleanup, source reopening at retained position, exact comparison source navigation, editable-question restoration, actual SAF Back cancellation and unchanged bindings. Save-dialog text entered/committed renaming, every alternative provider, full TalkBack traversal, every theme/disabled/hint contrast pair and every possible content length are not qualified.

The original 81-character label is deliberately rejected; the visible maximum-boundary fixture ends in `truncatio` because its frozen 80-character prefix excludes the final `n`, not because the button ellipsizes. The full 80-character action is present in layout and accessible text. Enlarged landscape keyboard and comparison screenshots were visually inspected: the research action remains above the keyboard, and the long rename label wraps completely. The viewport scrolls; all question/source text need not be simultaneously onscreen. Narrow test windows are centered with black margins, and display-wide OS bars are not claimed as an exhaustive pixel-level contrast qualification.

Original Notebook identity/note/bookmark fingerprint remains `213990e010f2d6f2f51aa0334d05920f3f54028b93ad5a3fb44f96c8e9d96ced`. Main/reader preferences restore exactly. Before/after model/selection/pack/optional-asset hashes match. Task-owned source records/comparison and imported editions are removed; source text, quote offsets and existing user records are unchanged.

App-private logical storage changed **3,274,406,765 → 3,285,164,986 bytes** (+10,758,221); allocated storage **3,208,384 → 3,219,832 KiB** (+11,448 KiB). This includes retained task screenshots/receipts and database/cache allocation. It is neither a feature-only allocation nor a continuously sampled peak or whole-device total; no 303/390 capacity claim is transplanted.

The committed packet contains actual decoded/raw instrumentation receipts, command exit codes, source/build/APK identity manifests, settings/storage observations, selected actual accessibility streams and all failure summaries/raw receipts. Original PNGs and all other node streams remain at their exact hashed paths; APKs/models/binaries are not staged. The checker verifies all 72 screenshot/node bindings, run/source/APK identity, retained hashes and restoration, and rejects actual copied evidence with a missing raw stream, corrupt decoded receipt, stale run ID or changed installed-test hash. Offline final cross-artifact verification also passed. Earlier partial and crashed runs remain failures; specifically the local-override attempt captured 48 valid states before refusing an unexpected font configuration, and does not replace the final six-configuration run.

Independent review of the frozen final source/evidence checkpoint is recorded separately; builder PASS is not acceptance.

## Open gates

Physical ARM64/GrapheneOS, TalkBack, human navigation/font comfort, broad rights, supported generated quality, matched comparisons and human release acceptance remain open. Automated bounds and contrast checks cannot establish accessibility compliance. Task 400 remains blocked and task 410's historical provenance is unchanged. This task adds no synthesis, automatic evidence assignment, model/corpus assets or parity/superiority claim.

## Independent visual review and reconciliation

The first review of `2a15a53` found white status icons over cream in portrait screenshots, despite passing requested appearance-mode checks. Its exact English conclusion is preserved in `accessible-core/independent-review-first.json`. The initial automated PASS does not qualify those rendered bars.

The test previously narrowed the app window, introducing OS letterboxing behavior. The revised layout constrains the content root to the same frozen 360/640 dp widths within a full-width window. Reader light/dark themes now also set the matching window background, preserving the backing surface beyond the scroll container. The revised check samples the actual status-bar screenshot: the clear central third must have the expected background, and contrasting rendered icon pixels must be present. It retains the full background fraction as an observation; icon occupancy is not counted as a background fault. This is bounded screenshot evidence, not a complete system-UI contrast audit.

Run `20261002T045331Z-65e24a72` failed the initial pixel-test occupancy assumption: only 88.98% of the entire status band was background because dark icons occupied the rest. The preserved screenshot shows dark icons, 5,595 pixels above 4.5:1 and maximum observed contrast 5.5554:1. The corrected sampling separates the clear center background from icon regions, rather than lowering the required glyph contrast. Settings and owned records were restored in that failed invocation.

## Status-reconciled candidate, before navigation review

Source checkpoint **4c29fd5**, run **20261002T045657Z-93b53e81**, source/build manifest SHA-256 **87523bb215a1ea5debd86968e7ae03a53e5fb755aa7656b20e3cb020effab264**. `bash tools/evaluation/check_accessible_core_flows.sh` passed, followed by a separate successful `bash tools/android-build.sh`; the latter reproduced the same production APK. Exact source maps are unchanged. Both immediate and final installed production/test hashes match the build. The revised packet is `accessible-core/status-reconciled-run/`; the original passing packet is not overwritten.

| Final artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Production APK | 22,719,262 | `70d0fd45dc5dc02e3fd81c85976bdf52756c30750f703202593f3ccdbeeed120` |
| Instrumentation APK | 441,913 | `0763840f94cd682832fb5401eba9e78452da906dedc044c6d19aeae399f46da6` |

The revised receipt contains **72 states**, **150 action observations**, **30 text contrasts**, **30 rendered status-bar samples**, and **1,708 successful assertions**, with the same six scale/layout combinations and four flows. Minimum sampled text contrast remains **7.2031:1**. Every central status background sample is 100% the expected color; every status sample contains at least 20 rendered pixels contrasting at 4.5:1 or greater, and the lowest maximum observed glyph contrast is **5.5554:1**. This detects the reviewed white-on-cream failure but does not establish contrast for every antialiased pixel, system dialog or icon. Builder visual inspection confirms dark icons in the two corresponding portrait reader/document states previously flagged by review. The constrained content width is recorded per Activity while the surrounding window now spans the display.

Environment remains **5560/API35/4096-byte pages**, boot ID `59ebd1a1-2fbf-4b25-aed7-2672c2d46604` unchanged; font **1.0 → 1.0**, user rotation **0 → 0**, auto-rotation **1 → 1**, without host rescue. Original Notebook fingerprint, preferences and model/selection/collection/optional-asset lists remain unchanged. Task-owned source/comparison/import fixtures were removed. Storage was **3,285,336,727 → 3,296,122,849 logical bytes** (+10,786,122) and **3,220,032 → 3,231,500 allocated KiB** (+11,468 KiB), including retained evidence/cache/SQLite allocations; this is not a continuous peak or whole-device budget.

Missing-stream, corrupt-receipt, stale-run and changed-installed-test negative controls pass; offline cross-artifact verification also passes. The exact originals, including screenshots and all accessibility streams, are hashed in the new packet's `original-artifacts.json`. No screenshot/APK/model payloads are committed. The first review and failed pixel-occupancy invocation remain separately preserved. Independent re-review is attached to the final frozen checkpoint; these bounded emulator results leave all physical, TalkBack, human comfort, provider, rights and quality gates above open.

## Navigation-bar review and bounded repair

The second independent review of `ef87bc0` confirmed identity/retention and status-bar repair but identified dark gray Android navigation icons on the dark reader background. Its exact conclusion is preserved in `accessible-core/independent-review-second.json`. The status-only pixel test did not cover that region; its PASS is not navigation contrast proof.

The reader now applies modern status/navigation appearance **after** legacy bar colors and visibility flags, so those calls cannot replace the final requested appearance. The test adds actual navigation-region pixel samples derived from navigation insets, including side bars in landscape. It requires rendered contrasting glyph pixels and the expected background, retaining measurements and screenshots. No global navigation mode or theme preference is changed.

The call-order repair failed in run `20261002T050511Z-a159716c`: the actual dark-reader navigation sample had zero pixels reaching 4.5:1 and maximum contrast **1.6478:1**. This failure remains preserved. The bounded final design retains light app chrome behind both system bars, with dark icons, while the scrollable reading surface and its text still follow the selected light/dark reading theme. It does not claim a whole-window night mode. Both status and navigation screenshot assertions retain the 4.5:1 threshold; content theme contrast is checked separately.
