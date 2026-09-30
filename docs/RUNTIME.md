# Local native inference runtime

PocketLore now builds a CPU-only JNI runtime into the Android APK. The existing
retrieval and source-inspection slice remains available without a model. A local
GGUF can be imported through Android's Storage Access Framework, then used to
produce an explicitly unverified draft from up to two retrieved source excerpts.
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
# Only when no test emulator is running; foreground, isolated task AVD.
bash tools/runtime/start-emulator.sh
# In another shell, after sys.boot_completed is 1:
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

Each request uses a fresh 512-token context, a 512-token batch / 128-token
microbatch, two CPU threads, zero GPU layers and greedy sampling. Output is capped
at 256 tokens; the UI requests 96. Context overflow throws rather than truncating
tokenized input silently. JNI streams byte arrays; Java accumulates UTF-8 before
display. Prompts are plain completion text with special-token parsing disabled;
model chat templates are not applied in this first integration.

Imports require a known size of 4 bytes to 512 MiB, available space for the copy
plus a 32 MiB reserve, a bounded streaming copy with SHA-256, a GGUF header, and a
successful native model load before atomic file promotion. The original document
remains. A failed import preserves the prior saved file, though a native load
failure after unloading it requires an app restart to reload that file. The
checksum identifies content; arbitrary imported files have no trusted expected
hash. The file picker requests local-only documents; the app itself has no
network permission. URI provider behavior is outside this app's implementation.
Activity recreation cancels old work; one process-wide serial worker prevents
staging-file races and cleans abandoned staging on next activity creation.

## Evidence and remaining limits

See [task evidence](evidence/native-runtime.md). Earlier exact artifacts passed
real x86_64 emulator load/generation and 23 behavior checks; ARM64 has compilation
only. A later supervised restart removed `/dev/kvm` access, blocking the final
emulator rerun and full import UI validation. The latest APK still builds, and
its native library hashes are unchanged; that does not validate the changed Java
lifecycle behavior. No physical Android or GrapheneOS acceptance is claimed.

The smoke model produced repetitive uncited source drafts and an unsupported
claim in a simple completion. Integration is not useful-research acceptance.
Claim/source validation, chat templates, better models and frozen quality testing
remain future tasks. True cold-cache latency, first useful content, p50/p95,
thermal behavior, arbitrary-GGUF memory bounds and whole-install physical-device
accounting are unmeasured. The 12 GB / 50 GB gates remain open.
