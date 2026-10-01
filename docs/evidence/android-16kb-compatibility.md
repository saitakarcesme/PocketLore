# Android17 native16KB compatibility — task305

Both required commands pass on LLMRig: `bash tools/android-build.sh` and `bash tools/evaluation/check_android_16kb.sh`. Actual Android17 API37 JNI load, bounded generation, cancellation/reuse, close/reload and native SQLite query succeed on emulator-5564 **without page-size compatibility mode**. ARM64 binaries are rebuilt and inspected but not executed on physical hardware.

## Root cause and fix

The preserved refined UI APK `3873ba23b6cda8268ec77ced1362a2e3230751d09f7ae111cfecb1795ece364e` contains four native binaries whose LOAD alignment is4096, including both supported ABIs. Its ZIP entries already pass16KB alignment. The new CMake target flags for both inference and index libraries are `-Wl,-z,max-page-size=16384` and `-Wl,-z,common-page-size=16384`. They follow the [official Android16KB guide](https://developer.android.com/guide/practices/page-sizes) for the existing NDK r27 toolchain. No runtime source, model, dependency pin, corpus or answer policy changed.

Every actual packaged ARM64/x86_64 LOAD segment now has alignment16384 and matching virtual/file offset congruence. Every GNU_RELRO end is divisible by16384. Both libraries in both ABIs are uncompressed and their APK data offsets are divisible by16384. Existing finalization already uses `zipalign -P 16`; no misleading packaging-only workaround or warning suppression was added. Raw program headers, original failures and rebuilt headers are in [artifact evidence](android-16kb/).

The artifact checker parses ELF64 program headers and ZIP local data offsets. Discriminating tests reject the original actual APK, a real ELF mutated to4KB LOAD alignment, an incorrectly ended RELRO region, a missing library, misaligned ZIP data and compressed libraries. These failures are independent of source flags or claimed test counters.

## Exact candidate identities and UI preservation

The assigned checkout starts at44eda1a and predates the separate refined UI candidate. Its rebuilt APK is `e765280475f9c0d5ee274ab23bab581f03192f45bd218a8070f98e49246261a3`; it was tested first, with that older UI clearly recorded. It is not represented as the refined candidate.

To preserve the exact supplied UI, `tools/runtime/repack-16kb-candidate.py` verifies the original APK hash, replaces only the four newly built native libraries, aligns and signs with the existing development key. Refined output: `downloads/android-16kb/refined-ui-16kb.apk`,15,706,130 bytes, SHA256 `9ce430ec0dcf9c4cb5fa537d9b3bcc2cdf197fe59b4121aee54fefa0a7079e92`. All DEX, manifest, resources and assets remain byte-identical to the supplied refined APK; only four libraries and signature entries differ. This native-only development overlay is not a UI source merge or final release. The original coordinator APK remains untouched.

The required check builds its instrumentation from current source, reproduces this overlay and tests it by default. `POCKETLORE_16KB_APK` can explicitly select the checkout APK. Serial5564 is fixed locally in this test; no canonical emulator defaults change. A per-test file lock prevents duplicate task305 invocations. Emulators5560/5562 and all services remain untouched; scrcpy remains visible. No global compatibility properties, manifest compatibility override, wipe or reboot was used.

## Actual API37 evidence

Identity: `google/sdk_gphone16k_x86_64/emu64xa16k:17/CP41.260828.004.A7/16296984:userdebug/dev-keys`. Kernel `getconf PAGE_SIZE` and the application process's libc `sysconf(_SC_PAGESIZE)` both report16384. Package-manager state changes from `pageSizeCompat=4` on the old unaligned candidate to `pageSizeCompat=0` after install. Both JNI libraries load and execute in that process; this is stronger evidence than merely dismissing the dialog. The final launch has no compatibility dialog in the captured UI hierarchy and inspected screenshot.

The actual production/demo baseline is Qwen2.5 0.5B Q4_K_M,491,400,032 bytes, SHA256 `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`. It is verified again inside the app. Test storage is `files/page-size-test/model.gguf`; saved user assets and model selection are not replaced. Runtime identity remains llama.cpp `bb4caa7540188872173c44d161602d9271386413`, CPU2 threads, context2048 and existing admission limits. Native index identity is preserved in the raw result. No selected4B Android qualification is implied.

One bounded24-token-cap chat request per run uses system prompt `Reply concisely in English.` and user prompt `Say hello in a short sentence.` Each returns9 tokens: `Hello! How can I assist you today?`. This is actual model output, not a canned answer or a source-support demonstration. The test first cancels generation, resets, generates, then closes and reloads. A platform-created small SQLite fixture is queried through the actual native index library; it is a mechanics fixture, not a factual corpus.

| Run | Load ms | First token ms | Generation total ms | Sampled peak PSS KiB |
|---|---:|---:|---:|---:|
| Checkout APK |403.424|1646.193|2219.403|576090|
| Refined overlay first run |532.748|1550.346|2147.482|107861|
| Required check, refined overlay |435.995|1435.602|2012.886|108166|

Load time spans native load only; generation starts before `generateChat` and includes templating/prefill through return; first-token time ends at the first callback. PSS is sampled with Android Debug.MemoryInfo every100ms during instrumentation, including load/reload. Samples are not exhaustive peaks, native allocation totals or phone RAM estimates. These few sequential runs use warmed filesystem state and are not cold/warm percentile or thermal benchmarks. The initial and later PSS values are retained without averaging or relabeling. Raw maps, resource counters, prompts, output, package state, identities and all timings are committed under the three separate run directories. APK/model binaries remain ignored. [Receipt](android-16kb/receipt.json) hashes current source, APKs and evidence.

## Limits and next release work

This closes the measured API37 x86_64 native alignment/load incompatibility for these exact binaries. It does not establish physical ARM64/GrapheneOS behavior, broad answer quality, source rights, selected4B memory qualification or full-corpus installation on5564. No prior API35 receipt is relabeled. The app still compiles/targets its existing API35 settings while running on API37; SDK migration is not part of this fix.

Next integration step: apply these two CMake changes through the ordinary source integration into the refined UI lane, rebuild there and bind the resulting candidate's APK/DEX/native identities to release/distribution evidence. The overlay permits immediate testing while avoiding an unreviewed UI source merge. Production signing, clean-machine reproduction, independent unseen evaluation and physical/human acceptance remain separate gates. No publication, push, main advancement or orchestration/state edits occurred.
