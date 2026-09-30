# Findings

- Bootstrap: the origin is configured as git@github.com:saitakarcesme/PocketLore.git on main. No physical Android device is provided.
- Two RTX 3090 GPUs report 24 GB each. One local GPU job at a time is the initial policy. Model-list availability alone is not generation evidence.
- Installed Codex CLI is 0.158.0; explicit exec/resume help has been inspected. Existing authentication and default model are retained.
- Prior atlas notes show successful Android plumbing can coexist with unusable answers. Useful grounded output needs its own evidence.
- User linger is enabled. The shell lacks user bus environment variables; the service installer must provide the existing /run/user UID bus path.
- Baseline `aa075238571338f79df990fe4c28ffc3d14b6bf9` matched origin main and passed independent baseline-scope review. The accepted tag covers repository setup only.
- Actual local `qwen3.8:27b` generation produced 8 development and 8 private holdout cases. The first response failed structured validation and was preserved; the adjusted response passed structural checks in 32.366 seconds on the rig. These are model-authored pilot rubrics, not factual gold or phone measurements.
- Separate builder, continuity and clean critic chats were registered. Explicit-ID continuity resumption succeeded; archive coverage is 28 visible records, not an assertion of unavailable history.

- Task 010 built CPU ARM64 and x86_64 JNI against llama.cpp `bb4caa7540188872173c44d161602d9271386413`, with licenses and pinned fetch/build steps. A 93,511,232-byte SmolLM2 Q3_K_M GGUF loaded and generated on the rig's AOSP x86_64 emulator; 23 behavior checks and retrieval UI smoke passed for their recorded APK. This does not establish useful cited synthesis: the source draft repeated itself and omitted citations.
- After the supervised restart, the sandbox no longer exposes `/dev/kvm`; the test emulator is absent and the final native verification exits 1. The latest APK builds and its native hashes match the tested libraries, but subsequent Java lifecycle changes and the complete import/restart UI path remain unvalidated. Physical Android/GrapheneOS, cold-cache latency, sustained resources and whole-install acceptance remain open. Exact measurements, artifact hashes and failures are in `docs/evidence/native-runtime.md`.
