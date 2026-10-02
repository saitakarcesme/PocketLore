# Accessible core-flow controls — task 450

The bounded emulator matrix and required build pass on the exact candidate below; no accessibility-compliance, physical comfort or product-acceptance claim follows.

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

## Exact final run and measurements

Final tested source checkpoint **e8e638b**, run **20261002T044441Z-3fee2078**. Source/build-input manifest SHA-256: `9f7860be12066a75dc3da9a02547bea84206440310f0713f1237e9231249f818`. It records all tracked Android/tool input hashes, SDK jar hash, fixture hash and Gradle configuration (two workers, 2 GiB heap, not measured total process memory). The source map remained unchanged through the build/run and offline verification. `bash tools/android-build.sh` passed again after the matrix and reproduced the same production APK.

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
