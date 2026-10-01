# Local native inference runtime

PocketLore now builds a CPU-only JNI runtime into the Android APK. The existing
retrieval and source-inspection slice remains available without a model. A local
GGUF can be imported through Android's Storage Access Framework, then used to
answer through the main Answer offline action using up to two retrieved source excerpts.
Task 020 distinguishes generated answers, unverified partial drafts, extractive
fallback, abstention and cancellation; see [answer evidence](evidence/answer-integration.md).
No INTERNET permission, remote endpoint, GPU backend, or Play Services dependency
is introduced. The rig's model services are not used by the app or these checks.

## Immutable inputs and attribution

- llama.cpp tag `b10566`, commit `bb4caa7540188872173c44d161602d9271386413`,
  [upstream source](https://github.com/ggml-org/llama.cpp/tree/bb4caa7540188872173c44d161602d9271386413).
  `tools/runtime/pins.env` is the machine-readable pin. Build checks reject a
  different HEAD or any modified/untracked file in that source checkout.
- llama.cpp/ggml MIT license is packaged in
  `android/app/src/main/assets/licenses/llama.cpp.txt`; build verifies it matches
  the pinned source license. CPU libraries are statically linked into
  `libpocketlore.so`; C++ runtime is static too. Dynamic dependencies are Android's
  `libc`, `libm`, and `libdl` only. No upstream source changes were made.
- Integration-only model: `tensorblock/SmolLM2-135M-Instruct-GGUF`, revision
  `32db44d69cedb731dc0fc96f60e01a86c6f5919d`, file
  `SmolLM2-135M-Instruct-Q3_K_M.gguf`, 93,511,232 bytes, SHA-256
  `61c69fc5ce91982e26c625d43be5c3c7f0f774da22f4fa4e45c37a80a22ddad4`.
  [Pinned publisher card](https://huggingface.co/tensorblock/SmolLM2-135M-Instruct-GGUF/blob/32db44d69cedb731dc0fc96f60e01a86c6f5919d/README.md)
  declares Apache-2.0, TensorBlock quantization and an Unsloth derivative of
  HuggingFaceTB SmolLM2-135M-Instruct. The Apache text is included in the APK's
  license assets, but weights are not bundled. The card mentions compatibility
  with llama.cpp b4242; it does not supply an exact conversion commit, source
  weight revision or reproducible conversion command. This is a reproducibly
  fetched artifact, **not** an independently reproduced quantization.
- The upstream base model's inspected revision was
  `12fd25f77366fa6b3b4b768ec3050bf629380bac`, with Apache-2.0 declared in its
  metadata. That is provenance context, not a claim that the publisher converted
  exactly that revision. The base repository had no LICENSE file at that path
  (HTTP 404); the Apache license declaration and publisher card are preserved.

## Reproduce on LLMRig

Existing tooling is reused from `/home/isa/Android/atlas-toolchain`, or set
`POCKETLORE_TOOLCHAIN` to a compatible installation containing `jdk`, `sdk`,
`gradle-8.13`, `android-ndk-r27c`, and `cmake-3.22.1`. Required SDK packages are
Android platform/build-tools 35 and the AOSP API 35 x86_64 emulator image.

```bash
# Explicit network provisioning only; downloads and weights stay ignored.
bash tools/runtime/fetch.sh --model
# Also provision the existing water-science pack per docs/ANDROID.md if absent.
bash tools/android-build.sh
bash tools/android-check.sh
# On the managed rig, reuse the coordinator-supervised emulator-5560.
# After adb shell getprop sys.boot_completed is 1:
bash tools/runtime/verify-native.sh
```

`verify-native.sh` defaults to `emulator-5560`; override
`POCKETLORE_EMULATOR_SERIAL` for another explicitly selected x86_64 emulator.
It fails if the emulator, pinned model, source, toolchain or behavior is missing.
It does not fetch assets, silently fall back to a host test, or reuse an old
success report. It builds/installs the app and separate instrumentation APK,
checks both packaged ELF architectures and the bundled MIT license, verifies
model identity on host and emulator, disables the test emulator's Wi-Fi/mobile
data, and runs real JNI load/generation/error/cancellation tests. Results, raw
logs and hashes go into a unique ignored `downloads/runtime/verify-*` directory.
The script modifies only the selected emulator's PocketLore test installation
and test files; it leaves radio settings disabled for further offline checks.

The standalone test-AVD script writes only under `downloads/runtime/android-user`
and requires accessible `/dev/kvm`. It never edits an existing unrelated AVD.
An already running emulator must be reused, not launched again on the same port.

## Build and API behavior

`preBuild` calls `tools/runtime/build-native.sh`. Both `arm64-v8a` and `x86_64`
are compiled for Android API 28 using NDK r27c / Clang 18. CMake 3.22.1 uses
Release optimization, baseline ARMv8-A, no host-native tuning, and no x86
AVX/AVX2/FMA/F16C/BMI2 extensions. OpenMP, networking/common utilities, tools,
server, CUDA, Vulkan and RPC are disabled. Build parallelism defaults to four;
set `POCKETLORE_BUILD_JOBS` to adjust. Compile commands and caches remain under
`android/native-build/build/<abi>`; generated JNI libraries are stripped before
packaging. AGP may still report that it cannot locate its own strip tool; the
project's NDK strip step has already run. Source/build reproducibility is pinned;
byte-identical APK signing across different debug keystores is not promised.

`NativeRuntime` exposes create/load/generate/cancel/reset/close. Model loading and
generation run on a worker thread. Registry handles retain shared native ownership
through active calls, so concurrent cancellation or close cannot free an in-use
model. Per-session operations serialize. Cancellation is sticky until an explicit
idle reset, including cancellation before a queued call. Load uses the model
progress callback; decode uses the CPU abort callback and token-boundary checks.
Contexts and greedy samplers are released on success, failure, cancellation and
Java callback exceptions. Close is idempotent. No global model setting is changed.

Each request uses a fresh 2,048-token context, a 2,048-token batch / 128-token
microbatch, two CPU threads, zero GPU layers and greedy sampling. Output is capped
at 256 tokens; the integrated answer flow requests at most 256. Context overflow throws rather than truncating
tokenized input silently. JNI streams byte arrays; Java accumulates UTF-8 before
display. The raw `generate` API retains plain-completion behavior. The integrated
answer flow uses `generateChat`: separate system instructions and user evidence
are formatted with the loaded model's supported chat template. Special-token
parsing is enabled only for that formatted chat. Unsupported templates and context
overflow become labeled fallback; embedded chat-control markers are rejected.

Imports require a known size of 4 bytes to 2,048 MiB, available space for the copy
plus a 256 MiB reserve, a bounded streaming copy with SHA-256, a GGUF header, and a
successful native model load before atomic file promotion. The original document
remains. A failed import preserves the prior saved file, though a native load
failure after unloading it requires an app restart to reload that file. The
checksum identifies content; arbitrary imported files have no trusted expected
hash. The file picker requests local-only documents; the app itself has no
network permission. URI provider behavior is outside this app's implementation.
Activity recreation cancels old work; one process-wide serial worker prevents
staging-file races and cleans abandoned staging on next activity creation.

## Answer integration model and behavior

Task 020 separately pins the official Qwen/Qwen2.5-0.5B-Instruct-GGUF repository,
revision `9217f5db79a29953eb74d5343926648285ec7e67`, Q4_K_M file
`qwen2.5-0.5b-instruct-q4_k_m.gguf`, 491,400,032 bytes, SHA-256
`74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`.
The publisher is the Qwen team; the original Apache-2.0 license and attribution
are packaged under `assets/licenses/qwen2.5-Apache-2.0.txt` and
`answer-model-notice.txt`. Weights remain unbundled and ignored. Conversion was
provided by the publisher and not independently reproduced; fetching this exact
GGUF is pinned. See `tools/answers/model.env`.

```bash
bash tools/answers/fetch-model.sh  # Online provisioning, outside research
bash tools/android-build.sh
bash tools/android-smoke.sh       # Offline behavior checks on existing emulator
```

`tools/android-smoke.sh` requires real model output and at least one cited generated
answer on the frozen public cases. It also exercises a citation-rejected fallback,
unsupported abstention, cancellation, activity recreation, SAF import, hash
verification, saved-model reload and source inspection. Test artifacts live in
unique ignored `downloads/answers/smoke-*` directories. It does not download a model
or start an emulator. The instrumentation APK is selected explicitly using the
`pocketloreTestRunner` Gradle property; the default remains the native smoke runner.

Before generation, the answer controller refuses questions whose terms are absent
from the pack or the selected excerpts. This is a conservative lexical check,
not proof that a question is answerable. After generation it checks source IDs
against the excerpts, requires a citation in each sentence/line with prose, and
rejects empty, citation-only or output-capped drafts. It accepts cited IDs at the
start or end of a sentence; model output is not rewritten to fabricate citations.
Runtime failures or citation failures yield explicitly labeled retrieved passages;
unsupported requests abstain, and cancellation discards partial output. These are
integrity safeguards, not entailment or factual-correctness verification.

## Evidence and remaining limits

[Task 010 evidence](evidence/native-runtime.md) is a frozen historical record,
including its real emulator results and restart-time missing-KVM failure. The
coordinator subsequently restored the existing AVD through a supervised service;
`adb` access works without exposing KVM to the builder sandbox. That historical
failure is no longer a current hardware blocker. No services or sandbox policies
were changed by the builder. [Task 020 evidence](evidence/answer-integration.md)
records the resumed validation and the current answer-flow results.

The 135M smoke model and a user-only Qwen prompt failed citation checks; those
outputs remain preserved. Separating trusted system instructions produced a
cited, limited condensation answer, while an incompletely cited groundwater draft
fell back to passages. This is not useful-research acceptance or a model quality
benchmark. The development cases are public and were used during implementation;
no private holdout was read or tuned on. Physical Android/GrapheneOS, ARM64
execution, cold-cache latency, first useful content, p50/p95, thermal behavior,
arbitrary-GGUF memory bounds and complete installed-storage accounting remain
unmeasured. The 12 GB / 50 GB release gates remain open.

## Synthesis development update

Task 050 adds exact chat-token preflight, constrained claim decoding and an optional pinned synthesis model. See [synthesis implementation](SYNTHESIS.md) and [actual evidence](evidence/synthesis.md). Earlier measurements above remain historical; the enlarged context and import bound do not establish arbitrary-model memory safety or phone acceptance.

Task 070 enforces one resident session, explicit context/KV/compute limits, memory-pressure unload and explicit reload, plus staged-import storage recovery. See [resource policy](RESOURCES.md) and [measured resource evidence](evidence/resources.md); allocation-time and physical-device limits remain open.
