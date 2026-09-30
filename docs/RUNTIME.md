# Local native inference integration plan

Current APK: no native inference library or model weights. Retrieval and source inspection run locally in Java. No remote endpoint is used by the product. The rig's local model service is a development worker, not an Android runtime.

## Pinned candidate

The first integration candidate is [llama.cpp](https://github.com/ggml-org/llama.cpp), MIT licensed, tag `b10566`, exact commit `bb4caa7540188872173c44d161602d9271386413`. The commit was resolved from the upstream tag with `git ls-remote` on 2026-09-30. Pin this commit rather than following master. This pin is a reproducible integration starting point, not a claim of compatibility with any proposed model architecture. Keep the source checkout and native build outputs outside Git; preserve the upstream MIT notice when packaging binaries.

Toolchain target: existing Android NDK r27c and CMake 3.22.1. Build CPU `arm64-v8a` for real phones and `x86_64` for emulator smoke tests. Follow the [upstream Android build guidance](https://github.com/ggml-org/llama.cpp/blob/bb4caa7540188872173c44d161602d9271386413/docs/android.md) and verify available CMake options at this commit before adopting flags. The initial CPU build should disable host-native tuning and optional networking; avoid instruction-set assumptions beyond the target device. Vulkan can be a later measured alternative, not an initial requirement.

## Next implementation task

1. Fetch and verify the pinned tree, inspect native API/build flags, build both ABIs and record compiler commands/library hashes.
2. Implement a narrow JNI session API: open a user-selected local GGUF, tokenize, evaluate evidence-grounded prompts, stream generated tokens, cancel safely and release model/context resources. Generation runs off the UI thread. Do not add network permissions.
3. Import via Android's Storage Access Framework with file size/hash checks. Keep weights in app-private storage or retain an explicit local document grant. Show required storage before duplication. Weight downloads happen before offline use.
4. Choose a small openly licensed GGUF as an integration test only, recording upstream model revision, conversion/quantization provenance, weight SHA-256 and license. Do not imply a small smoke model meets the research bar. Select the eventual phone model after measurements and quality evaluation.
5. Measure cold load, first token, tokens/second, total response time, peak RSS/PSS, context length and installed assets. Label rig/emulator results separately. No physical-device measurements are possible until hardware is attached.
6. Preserve source references through prompting, explicitly separate supported claims from unsupported inference, and test cancellation, corrupt weights, low storage and context overflow. Free-form generation alone is not source grounding.

Acceptance requires an actual Android local generation trace plus ARM64 compilation; real-device resource/latency acceptance stays open. The 12 GB RAM and 50 GB installed-assets limits include model, KV cache, app, index, packs, import staging and temporary copies, not merely the quantized weight file. A frontier-plus-web comparison must use frozen cases, actual outputs and comparable scoring; no superiority claim follows from integration success.

Entry points today: `tools/android-check.sh`, `tools/android-build.sh`, and `tools/android-knowledge-pack.py`. These provide regression checks for retrieval while the native work proceeds.
