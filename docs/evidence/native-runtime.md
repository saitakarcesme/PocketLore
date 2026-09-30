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

Checkpoint update: 23 behavioral checks passed on the isolated AOSP API 35
x86_64 emulator in `downloads/runtime/verify-20260930T220529-38282/`.
The actual source prompt generated a repetitive uncited answer. Native integration
passes this smoke check; useful cited synthesis does not pass quality acceptance.

The originally supplied emulator exited before execution. The first verification
failed with `device 'emulator-5560' not found`, preserved in
`downloads/runtime/verify-20260930T220150-35885/`. A separate PocketLore AVD was
created under ignored downloads using the installed AOSP image. The installed
avdmanager could not load the image's absent devices.xml; its failed creation log
and emulator launch log are preserved. A minimal standalone AVD config then booted.

An initial retrieval UI smoke failed to find the source button; its y=2080 swipe
was outside the fresh AVD's 1920-pixel display. The failed UI hierarchy and failure
record are preserved in `downloads/runtime/ui-retrieval-initial/`. With a
1080x2400 display override and source buttons placed before the optional generation
panel, the same retrieval smoke passed in `downloads/runtime/ui-retrieval-second/`.
Full native import UI validation remains in progress at this checkpoint.
