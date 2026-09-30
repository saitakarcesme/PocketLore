# Native runtime evidence — task 010

Work in progress on LLMRig, 2026-09-30. Builder evidence, not acceptance.

Initial CPU ARM64 and x86_64 JNI compilation succeeded with NDK r27c and
CMake 3.22.1. Android packaging and runtime behavior are not yet validated.
Raw initial build log: ignored `downloads/runtime/build-initial.log`.

Two initial candidate model repository lookups returned HTTP 401 (the guessed
`ggml-org/SmolLM2-135M-Instruct-GGUF` and
`HuggingFaceTB/SmolLM2-135M-Instruct-GGUF` names). Neither was downloaded or used.
The available TensorBlock repository was inspected and its actual Q3_K_M file
and immutable revision pinned. Q4_K_M was advertised in its card but absent from
the current repository files; the actual Q3_K_M listing is authoritative here.

No private holdout read, no GPU inference, no physical hardware measurements.
