# Native runtime evidence — task 010

Builder result on LLMRig, September 30–October 1, 2026: CPU ARM64 and x86_64 JNI
libraries and an Android APK build successfully. A real small GGUF loaded and
generated through JNI on an AOSP x86_64 emulator. The tested artifact passed 23
behavior checks and the existing retrieval UI smoke. **The final emulator rerun
is blocked after the supervised restart removed `/dev/kvm` from the sandbox.**
The latest Java lifecycle changes compile but are not emulator/UI-validated.
This is not independent review, physical-device acceptance, or useful-research
acceptance. No private holdout was read and no GPU inference was run.

## Implemented scope

- Immutable llama.cpp `bb4caa7540188872173c44d161602d9271386413` (b10566), CPU-only
  ARM64 Android API 28 and x86_64 Android API 28 builds, packaged MIT notice.
- JNI session ownership, local model load, tokenization, streamed UTF-8 byte
  output, fresh bounded contexts, greedy sampling, cancellation, reset and close.
- Optional local-only Storage Access Framework model import with size/storage
  guards, SHA-256, staged copy, native GGUF validation and atomic promotion.
- Experimental source-excerpt draft panel alongside inspectable retrieval sources.
  It marks output unverified. No network permission or Play Services dependency.
- Explicit online fetch, offline build, isolated emulator startup, and a behavioral
  verification script. Reproduction and API constraints are in [RUNTIME.md](../RUNTIME.md).

## Exact inputs and artifacts

The small model is `tensorblock/SmolLM2-135M-Instruct-GGUF` revision
`32db44d69cedb731dc0fc96f60e01a86c6f5919d`, Q3_K_M, **93,511,232 bytes**.
Its downloaded bytes and emulator-side bytes both matched SHA-256
`61c69fc5ce91982e26c625d43be5c3c7f0f774da22f4fa4e45c37a80a22ddad4`.
The [publisher metadata](native-runtime/model-metadata.json) and
[pinned model card](native-runtime/model-card.md) are preserved. The declared
license is Apache-2.0, with upstream HuggingFaceTB → Unsloth → TensorBlock lineage.
Exact conversion/source-weight revisions were not supplied by the publisher;
quantization was not independently reproduced. This smoke model is not a selected
research model. Weights remain in ignored `downloads/runtime`, never in Git.

| Artifact | SHA-256 | Interpretation |
| --- | --- | --- |
| Tested APK | `0045f4dc90e5c8d6dfdc8992021a866651f8e2621df62357023d1416c1bda7e9` | 23 JNI checks and retrieval UI smoke passed; source captured by checkpoint `2ded792` |
| Tested instrumentation APK | `8f9eda5f832b72ba01a967c184fc03e24ecac722848294898946b0bc291f6ce4` | Actual native behavior tests, not a product feature |
| Latest APK | `b8394281c7af37302bf05fc1002adc9d96877cb5e52d5521dc4768d436ad2f56` | Build passed; final emulator/UI rerun blocked |
| ARM64 JNI | `782af532ba2cd193dfdcbbf1111fded5309af422e6db008c68583fe69306bb0e` | Compiled, not executed on ARM64 |
| x86_64 JNI | `8cac124e8c88f2e0da9066f8679793edd23fb2ae557606c0919b077df56decd2` | Executed on emulator; unchanged in latest APK |

[Final artifact sizes and hashes](native-runtime/final-artifacts.json) also cover
the source pack. The latest APK differs because of Java lifecycle handling and
fresh packaging. Native hashes match the tested libraries exactly; this does not
validate the changed Java behavior. [Representative compiler commands](native-runtime/compiler-commands.json)
record NDK r27c / Clang 18.0.3, CMake 3.22.1, Release `-O3`, baseline ARMv8-A,
and baseline x86_64 without AVX/AVX2/FMA/F16C/BMI2. Both libraries depend dynamically
only on Android libc, libm and libdl. No CUDA/Vulkan/OpenMP/RPC backend was built.

## Actual measurements — emulator only

Environment: rig Intel Core i5-14400F, 16 logical CPUs, 32,638,484 KiB host RAM.
Isolated AOSP Android 15/API 35 x86_64 emulator, fingerprint
`Android/sdk_phone64_x86_64/emu64x:15/AE3A.240806.019/12368160:userdebug/test-keys`.
The test AVD had two virtual CPUs. Requested 2,048 MiB RAM was automatically raised
by the emulator to **2,560 MiB** (recorded in its log/config). This is not a phone
resource result. Wi-Fi and mobile data were disabled; packaged permissions contain
no INTERNET permission. No packet-capture audit or physical GrapheneOS run occurred.

Native runtime identity returned by the library:
`llama.cpp bb4caa7540188872173c44d161602d9271386413; CPU; context=512; threads=2; greedy`.
Each generation uses a fresh 512-token context, batch 512, microbatch 128, two CPU
threads, zero GPU layers and greedy sampling. The model is mmap-loaded.

Latest successful emulator trace:
[native-runtime/emulator-23-checks.json](native-runtime/emulator-23-checks.json).

| Measurement | Observed value | Definition |
| --- | --- | --- |
| First successful model load | 56.456 ms | JNI load call; model file was already read for hashing, so **not cold-cache**; corrupt/missing-model tests ran first |
| Short prompt first token, runs 0 / 1 | 71.605 / 116.502 ms | From generate call to first Java token callback; includes context creation and prefill |
| Short prompt total, runs 0 / 1 | 612.041 / 581.787 ms | 24 emitted tokens each; complete capped request |
| Throughput, runs 0 / 1 | 39.213 / 41.252 tokens/s | Emitted token count divided by full request duration, including prefill |
| Source-excerpt request | 96 tokens in 3,348.469 ms | Same prompt builder as UI; stopped at output cap |
| Cancellation return | 0.695 ms | From other-thread cancel call until generate returned -1; synchronized at first token callback, **not worst-case decode cancellation latency** |
| Process high-water RSS | 247,808 KiB | `/proc/self/status` VmHWM, whole app/instrumentation process over this test lifetime |
| Sampled peak PSS | 149,297 KiB | Android Debug.MemoryInfo every 50 ms through tests; sampling can miss peaks and adds overhead |
| RSS after close | 143,084 KiB | VmRSS near test end; not a long-session leak test |

An [earlier 22-check run](native-runtime/emulator-first-22-checks.json) measured
55.561 ms load and 53.845 / 58.263 tokens/s on the short prompt. Both traces are
preserved rather than selecting the faster result. Two repetitions are not enough
for p50/p95, thermal or sustained-use claims. True cold-cache latency and time to
first *useful* content were not measured. Post-instrumentation `dumpsys meminfo`
found no running process, so it is not used as a peak-memory measurement.

Short prompt: `The capital of France is`. Both greedy repetitions emitted:

> Paris. Paris is the political, cultural, and economic center of the world. It is the largest city in the European

This contains an unsupported sweeping claim and ends at the 24-token cap. It is
real generation evidence, not a factual-quality pass.

The source prompt used actual installed USGS passages `[water-02]` and
`[water-01]` and asked to compare evaporation and condensation. The model produced
a basic liquid↔gas distinction, then repeated the question/answer several times
until the 96-token cap, **without the requested citations**. The exact prompt and
full output are in the JSON. No claim/source validator or quality scoring was
performed; supported useful synthesis remains open.

## Checks and limitations

`bash tools/android-build.sh`: **PASS** on the final source, [raw log](native-runtime/final-build.log).
`bash tools/android-check.sh`: **PASS**, eight retrieval/abstention/corruption/citation
contracts, [output](native-runtime/retrieval-contract-check.txt).

`bash tools/runtime/verify-native.sh`: **PASS earlier, currently BLOCKED/exit 1**.
The successful [raw run](native-runtime/emulator-verify.log) executes assertions
for real load, nonempty real generation, deterministic reuse, actual source-prompt
generation, missing/corrupt weights, generation without a model, context overflow,
invalid output limit, callback exception cleanup, reset while busy, cross-thread
cancellation, cancellation before generation/load, reuse after cancel, close during
generation, closed handles, and bounded import success/failures (low storage,
truncation, excess bytes, cancellation and wrong magic). Import low-space behavior
uses an injected available-byte value; no actual disk-full experiment was run.

The existing retrieval UI smoke passed installation, knowledge-pack load, comparison
retrieval, source provenance dialog, unsupported-query abstention and no INTERNET
permission ([result](native-runtime/retrieval-ui-result.json)). Manual native UI
inspection reached the local file picker and found the test GGUF in Downloads.
**It did not complete import, draft interaction, cancellation UI or restart/reload
validation before the supervised restart.** Those remain explicit gaps.

Final Java changes serialize model imports/cleanup across activity recreation,
remove abandoned staging, and fix source-panel wording. They compile but require
an emulator rerun and lifecycle UI tests. The exact external dependency is an
accessible `/dev/kvm` plus a running API 35 x86_64 test emulator (or equivalent
coordinator-provided emulator access). `/dev/kvm` is absent in the resumed sandbox;
[launch failure](native-runtime/resumed-kvm-failure.log) and
[verification failure](native-runtime/resumed-verify-failure.log) are preserved.
No permissions, unrelated services or runner state were changed to work around it.

## Storage accounting

Final APK: **11,713,687 bytes**. Native entries: ARM64 5,585,624 bytes, x86_64
6,064,328 bytes (both included in that APK). Smoke model: 93,511,232 bytes.
APK + one model is **105,224,919 bytes**, a component subtotal, **not** total installed
footprint. The tested incremental APK was 104,894,723 bytes because incremental ZIP
packaging retained unused space from the earlier unstripped native libraries. The
latest APK was freshly packaged after preserving the prior generated APK in the
ignored runtime cache; no source reset or evidence deletion was performed.

The test app's `du` reported 91,348 KiB under files, including the smoke GGUF and
small test artifacts ([raw listing](native-runtime/emulator-app-files.txt)). ADB
also staged a 93,511,232-byte source GGUF in emulator Downloads for the incomplete
UI import test. Production import duplicates the selected original; a replacement
can temporarily retain old model + new staging + source original. Include these,
APK/ART files, packs, caches, test APK if installed and installation temporaries in
any future whole-install measurement. Their simultaneous peak has not been measured.
The 12 GB device-RAM and 50 GB total-installed-assets release gates remain open.

## Preserved failed attempts and checkpoints

- Two guessed model repository names (`ggml-org/SmolLM2-135M-Instruct-GGUF` and
  `HuggingFaceTB/SmolLM2-135M-Instruct-GGUF`) returned HTTP 401; neither was used.
  The actual TensorBlock Q3_K_M listing supplied the accepted pin. Q4_K_M was
  advertised in its card but was absent from its repository files.
- Initial supplied emulator disappeared: [failed verification](native-runtime/initial-missing-emulator.log).
- Installed avdmanager failed on the image's absent devices.xml:
  [creation log](native-runtime/avd-create-failure.log),
  [launch log](native-runtime/avd-launch-failure.log). A separate minimal task AVD
  then booted from the existing image; no prior project's AVD was modified.
- First retrieval UI smoke could not reach the source button. Its y=2080 swipe was
  outside the fresh AVD's 1920-pixel display. The failed hierarchy/screenshots remain
  in ignored `downloads/runtime/ui-retrieval-initial`; [failure record](native-runtime/retrieval-ui-failure.txt)
  is committed. The same smoke passed after display override to 1080×2400 and source
  buttons were placed before the optional native panel.
- `f142b5e`: compiled JNI/import implementation, honestly marked execution unvalidated.
- `2ded792`: 23 passing emulator behavior checks and preserved limitations.
- Final evidence checkpoint: current branch only; no push, branch switch or main
  advancement. Independent criticism and acceptance remain the coordinator's next
  steps; this builder did not dispatch or modify orchestration.

Committed evidence files are checksummed in
[native-runtime/SHA256SUMS](native-runtime/SHA256SUMS). Full earlier logs, test AVD,
model and build outputs remain in ignored `downloads/runtime` and Android build
directories on the rig. No model weights, build binaries or private context were
added to Git.
