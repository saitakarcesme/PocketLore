# Task340: optional offline OCR and speech input

Implemented a real local recognition path, with no automatic asset download or cloud/platform speech recognizer. Required build and behavioral check pass on the final debug candidate; these are bounded emulator results, not physical-device or product acceptance. Recognition supplies editable question input, never generated-answer success or source support.

## Candidate and implementation

Final APK SHA-256 **2ad38d240ad4264627d3c1319c032dc88731a63332c48b4f6102b1a67cb213d1**, **22,637,269 bytes**. [Exact APK/DEX/native/license identities](attachments/race-fix/artifacts.json), [device receipt](attachments/race-fix/receipt.json), and [instructions](../ATTACHMENTS.md) pin the concrete result. ARM64 and x86_64 libraries compile locally on LLMRig; only x86_64 API35 executes in this task. Both native ELF LOAD segments and APK entries pass 16 KB alignment checks; new API37 runtime loading remains separate from task305's older binaries.

The separate attachment Activity leaves Saved/history/bookmarks/reader/export ownership intact. It installs optional pinned assets atomically, handles local image/WAV selection and runtime microphone permission, performs bounded local recognition, exposes editable text plus a provenance receipt, and returns reviewed text to the research question without automatically submitting it. Cancelling clears pending/completed recognized text, interrupts the owning job, and closes capture; leaving the Activity cancels active work. Startup cancellation is checked after asset verification and atomically with microphone start. Native model initialization and Android bitmap decode are not immediately interruptible; input and thread bounds remain explicit.

| Component | Immutable identity | Rights / role |
|---|---|---|
| Tesseract 5.5.3 | db0ec62f81b0737fbbe184d8fea40af5738f8eef | Apache-2.0; local English OCR |
| Leptonica 1.85.0 | 63aef18d98432b8582a1565e241f7bd2ee9cc8d9 | BSD-style; static image support |
| whisper.cpp 1.7.6 / ggml | a8d002cfd879315632a579e73f0148d06959de36 | MIT; CPU-only local speech |
| eng.traineddata | 7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2 | Apache-2.0; 4,113,088 bytes |
| ggml-tiny.en.bin | 921e4cf8686fdd993dcd081a5da5b6c365bfde1162e72b08d75ac75289920b1f | MIT; 77,704,715 bytes |

[Source archive pins](../../tools/attachments/sources.json) and [model revision/URL pins](../../tools/attachments/models.json) are verified before build/use. Full notices, including installed NDK cpu-features, are in APK assets. Optional weights total **81,817,803 bytes**, are not bundled, and do not change the production research-model pin (SHA74a4da8c… Qwen2.5 0.5B). Tesseract runs without OpenMP; speech uses two CPU threads, greedy English decoding, at most64 tokens and no retries. Inputs are at most4 MiB/four million image pixels or15 seconds of16 kHz mono PCM. A per-process lock serializes native recognition. Internal static ggml symbols are hidden to prevent accidental research-runtime symbol interposition.

The preview includes original URI/input hash, recognized text hash and exact recognized-string UTF-16 range, engine/model identity, and a personal-rights disclaimer. No OCR bounding boxes, original-image character offsets, saved microphone archive or public redistribution rights are invented. Editing receives a separate reviewed-text hash. OCR is text recognition, not image reasoning.

The supplied source-backed competitor matrix was inspected at its actual `repo/output` location and hash-checked against the handoff; the requested top-level output directory was absent. [Receipt](attachments/competitor-receipt.json) preserves the static research limitation/acquisition notice. No competitor code or branding was copied.

## Frozen controls and actual results

[Original protocol](attachments/protocol.md) and [fixture pins](attachments/fixtures.json) precede validation. Rendered and rotated signs are constructed controls, not photos. The later [photo supplement](attachments/photo-supplement.json) was separately frozen before its first inference: Dmitry Novoklimov's real 2008 STOP-sign photograph, [Commons revision1215001130](https://commons.wikimedia.org/w/index.php?title=File:Red_octagonal_stop_sign.jpg&oldid=1215001130), CC0-1.0, resized once as a whole frame without crop/recognition tuning. Original and derivative hashes are retained. The historical JFK WAV comes from the pinned whisper.cpp source tree; it is an ignored test artifact, not a bundled asset or new microphone recording.

Final [raw outputs, timing and memory samples](attachments/race-fix/results.json), [UI screenshot](attachments/race-fix/preview.png), and [checker log](attachments/check-race-fix.log) record **57 passing assertions** on emulator-5560:

| Input/action | Actual result | End-to-end time |
|---|---|---:|
| Rendered English sign | `OFFLINE LIBRARY` / `Review every word.` |54.20 ms |
| Rotated sign | Same two lines |44.40 ms |
| Blank image | Empty text |25.61 ms |
| Real STOP photo | **Empty text: retained OCR accuracy failure** |87.88 ms |
| Historical speech sample | Actual local transcription preserved below |5,073.40 ms |
| Silence | Empty text; energy gate |159.74 ms |
| Deterministic noise | Empty text after real decoder |4,694.80 ms |
| OCR retry after cancellation | Correct sign text |44.91 ms |
| Cancel during native OCR | IOException, job released |4.04 ms |
| Cancel during native speech | IOException, job released |20.37 ms |
| Home/background during real AudioRecord capture | Capture released, no usable result |481.20 ms |

Actual speech output: “And so my fellow Americans ask not what your country can do for you ask what you can do for your country.” Punctuation is imperfect; no edited transcript is scored as engine output. The test grants real RECORD_AUDIO permission and opens AudioRecord, then backgrounds the Activity; this establishes capture/lifecycle behavior, **not physical acoustic recognition accuracy**. Permission denial tests combine actual revoked app permission with an explicit denial-callback injection. File selection tests deliver local Android URIs to the actual Activity; they do not claim a manual picker walkthrough.

The check also rejects absent/changed assets, malformed image/audio, oversized image dimensions, pre-cancelled work and cancelled/corrupt asset installation while retaining prior assets. A queued cancellation before model verification completes never starts the microphone; native cancellation is exercised only after the actual decode phase begins, followed by retry. Completed-preview cancellation disables submission. All recognized text remains editable and requires explicit review. The current app manifest has RECORD_AUDIO but no INTERNET, and APK DEX contains no GMS package. Local-provider intent requests local files; arbitrary external provider implementations are not qualified by this test.

Recognition timing is monotonic elapsed time around the production engine, including asset integrity verification, native load, decode and result receipt creation; it is not a model-only throughput or cross-backend speed claim. Cancellation latency starts at the test's signal/Home action and ends at released work. Memory sampling every50 ms reached **258,663 KiB PSS** on5560; it may miss shorter peaks and does not establish OS OOM safety or phone RAM/thermal behavior.

## Updated full-catalog resource/reader evidence

The final APK and both optional assets were installed on existing emulator-5562 alongside **all31 retained bulk shards**, the existing small collections and saved research model. [Current receipt](attachments/budget-current/receipt.json), [raw reader/recognition results](attachments/budget-current/budget.json), [guest memory](attachments/budget-current/guest-memory.txt), and [filesystem observation](attachments/budget-current/df-after.txt) are new measurements for this APK, not relabeled task303 results. Bulk catalog, small-pack catalog and saved-model hashes match before/after.

| Current measured item | Bytes / observation |
|---|---:|
| App logical files including model/corpus, optional assets and task fixtures |41,701,225,756 |
| App allocated files |41,704,140,800 |
| Installed application plus test code |23,040,000 |
| Installed total including test code |**41,727,180,800** |
| Sampled optional-asset replacement peak, allocated app files |41,859,518,464 |
| Above peak plus installed code |**41,882,558,464** |
| Whole guest `/data` used, including non-app files |42,018,381,824 |
| Optional OCR + speech weights |81,817,803 |

The replacement run retained old installed weights while local incoming weight files and staging coexisted. Incoming test model files were deleted only after successful installation; no corpus was recopied or deleted. A single replacement may stage up to77,704,715 additional bytes; a retained local input copy is another77,704,715 bytes. ResourceStorage also requires256 MiB free reserve. Current installed and measured optional-update paths fit45 GB target/50 GB hard limit with this baseline model. The sampling interval was20 ms, so the observed peak is not a mathematical bound on arbitrary providers or future updates. Full bulk-shard replacement and APK-install transient peaks were **not** remeasured for this revision; old303 receipts remain historical, and final candidate update qualification stays open.

Real shared readers still inspect Acid and find30 capped restaurant candidates around Mexico City across the full retained collections. Current timings are272 ms and10.48 seconds respectively; the latter remains a usability limitation. OCR and speech execute in the same test process after these readers, with real speech5.27 seconds and sampled peak **251,143 KiB PSS**. Bulk rights remain browse-only; source IDs are not a count of distinct real venues, and retrieval/recognition is not supported generated-answer quality. Research-model and collection hashes are unchanged; optional recognition weights are separate from research-model selection.

## Checks, failures and next gates

- `bash tools/android-build.sh`: **PASS**, [final required log](attachments/android-build-race-fix.log).
- `bash tools/evaluation/check_attachments.sh`: **PASS**,57 actual assertions plus host hash/alignment/permission checks; [receipt](attachments/race-fix/receipt.json).
- `python3 tools/evaluation/attachments/budget.py`: **PASS**, actual full-catalog reader/recognition coexistence and optional replacement measurement; [log](attachments/budget-race-fix.log).

Native build failures (cpu-features export, generated header and static link resolution) remain in the attachments evidence directory. One source-build launcher failed after it was edited while running; the corrected build was rerun without that practice. The first lifecycle test revoked permission inside its own process, causing Android's expected permission-revocation process kill; the next test driver waited incorrectly for creation while reordering an existing Activity and was stopped. Both failed attempts remain logged. The successful driver revokes only after result collection and waits for actual foreground UI and preview content. The earlier screenshot captured a stale transition frame; the final screenshot waits for rendering and asserts displayed retry text.

Independent review found background capture, retained cancelled preview, then a pre-start cancellation race; each was repaired with discriminating tests. [Final independent criticism](attachments/independent-review-final.txt) confirms the bounded fixes and retains limitations. This is supplementary independent code/evidence review, not canonical runner acceptance or human approval.

Next concrete product work is a separately frozen photo-quality improvement using real document photos and difficult signs, without turning OCR into image reasoning or erasing this STOP failure. Physical microphone acoustics/permission lifecycle, ARM64 and API37 JNI execution, GrapheneOS, long-session resource behavior, final release/distribution identities and final whole-candidate update measurements remain open. No multilingual, image-reasoning, competitive or product-acceptance claim follows. No private holdout, orchestration, service, global model preference, production-model pin, push or main change occurred.
