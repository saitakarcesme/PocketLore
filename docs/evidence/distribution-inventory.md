# Distribution inventory: task 180

This task produces a machine-readable inventory and passing behavioral checks on LLMRig. It does **not** declare the candidate ready for distribution or accepted as a product. No production key was generated/read, no artifacts were published, and no emulator or service was launched/restarted.

## Inventory coverage

[docs/distribution-inventory.json](../distribution-inventory.json) records exact SHA-256 values, byte sizes, versions/revisions, source locations, declared terms and remaining gaps. Paths use PROJECT, TOOLCHAIN and HOST roots; the verifier resolves these on the provisioned rig without reading credentials or private control context.

- Both ARM64 and x86_64 packaged JNI libraries, plus **13 native link inputs per ABI**: project bridge object, llama, ggml, ggml-base, ggml-cpu, compiler builtins, atomic support, libc++ linker script, libc++ static, libc++abi, unwind and CRT start/end objects.
- Actual compiler-driver link expansions and ELF dynamic dependencies. The latter are platform libm.so, libdl.so and libc.so, not bundled libraries. Archive inputs can have unused members removed by section garbage collection; the inventory does not claim every archive member survives linking.
- **123 resolved Gradle build-classpath artifacts**, with coordinates, actual artifact hashes, POM/parent-POM hashes, local license declarations and embedded plain-text notice-entry hashes where present. The independently exported application debug runtime classpath is empty. Build-classpath dependencies are not presented as APK libraries.
- Installed JDK (Temurin 17.0.20.1+1), Gradle 8.13, NDK r27c (Clang 18.0.3 in the captured driver trace), CMake 3.22.1, SDK API 35/build-tools 35.0.0, platform/command-line tools and emulator/system-image metadata, artifacts and notices. Source-properties/release metadata is retained. Host Python, Make and Bash executable versions/hashes are separate; host OS shared-library/license closure is not audited.
- Four optional models: SmolLM2-135M Q3_K_M, Qwen2.5-0.5B Q4_K_M demo, Qwen2.5-1.5B Q4_K_M and Qwen3-1.7B Q8_0. Each has an immutable publisher revision, actual full-file hash, source URL and local Apache-2.0 license-file hash. Weights are not bundled; publisher quantization was not independently reproduced.
- The bundled starter and regional POI source locks, separate English reference/science pack manifests and asset hashes. Original attribution, rights URLs, dates and content pins are retained rather than replaced by a repository-wide license.
- The exact current build recipes and native notice pins, plus every APK native/asset member hash. This is a dependency/attribution inventory, not an exhaustive whole-OS SBOM or vulnerability audit.

The [raw Gradle resolution](distribution-inventory/resolved.json), [runtime-classpath report](distribution-inventory/runtime-classpath.log), [ARM64 link trace](distribution-inventory/link-arm64-v8a.txt), [x86_64 link trace](distribution-inventory/link-x86_64.txt) and ELF reports preserve primary local evidence. No network dependency resolution was needed; the wrapper uses the existing offline cache.

## Native notice repair

The previous task-170 APK omitted installed NDK aggregate notices; [before-notices.json](distribution-inventory/before-notices.json) records its exact hash and missing entries. The finalizer now inserts the unmodified NDK toolchain and sysroot notices under assets/licenses, using [exact notice pins](../../tools/distribution/native-notices.lock.json). Missing or changed installed text fails the build instead of generating a replacement license.

The complete aggregate texts preserve LLVM Apache-2.0-with-exceptions and legacy/component terms without incorrectly declaring that every NDK input has one blanket license. These broad notices include material outside the linked subset; their presence does not mean every covered component is shipped. Existing llama.cpp/ggml MIT and model/data notices remain unchanged. No application Java/C++ source changed in this task.

Final APK: **11,904,809 bytes**, SHA-256 **8d6aef5b9ab8898c6b5c9668236b67752cc17d61e53030620811d1367aef9f64**. The previous APK was 11,773,557 bytes; compressed notice packaging adds 131,252 bytes. It remains normally debug-signed; [signature verification](distribution-inventory/signature.txt) records the public certificate. This task is not a new lifecycle, JNI-quality or physical-device acceptance run. The packaging change requires a later release freeze and exact-artifact release validation.

## Behavioral verification and preserved findings

The public [five mutation cases](../../tools/distribution/regressions.json) were committed as d7ff95e before implementation. The check re-resolves the current local build classpath, recomputes actual file hashes, matches exact APK payload/notice bytes and native source-library identity, and checks component coverage. It never refreshes the frozen inventory automatically.

All five mutations are rejected using isolated copies, without modifying installed tools:

1. Removing a required notice gives its exact missing path.
2. Flipping one byte in a packaged native-library copy produces a hash mismatch.
3. Flipping one byte in a resolved build-artifact copy produces a hash mismatch.
4. Removing a native component row fails the explicit coverage requirement.
5. Marking distribution ready while inventory gates remain open fails.

[Verification results](distribution-inventory/verification.json) record the actual unique file count, inventory hash and rejection reasons. Both named commands exit 0: [bash tools/android-build.sh](distribution-inventory/build.log) and [bash tools/evaluation/check_distribution_inventory.sh](distribution-inventory/check-final.log). The check's resolution invocation also re-verifies/finalizes the same APK; no prior inference or lifecycle workload was repeated.

Two implementation findings remain preserved. The initial Python capture draft had a conditional-expression syntax error; [raw failure](distribution-inventory/initial-syntax-failure.log) is retained. Checkpoint f660cc0 captured six falsely missing POM declarations because those POMs lacked XML namespaces. The parser now supports both forms and retains license comments, including kXML package-specific scope. All 123 artifacts have local declarations; this is not a legal-clearance statement. Binary LICENSE.class entries are excluded from the plain-text notice count.

## Remaining terms and owner decisions

**64 build-only artifacts have no detected embedded plain-text notice**; their exact coordinates and POM-declared terms are listed in the inventory gap section. This does not mean no license exists, nor that a POM URL supplies all redistribution obligations. Full-text/notice review remains necessary if those tools are redistributed. No build-tool bundle is produced or authorized here.

Installed toolchain notices and SDK package metadata are hash-verified, but they do not establish permission to redistribute an SDK/NDK/JDK/Gradle/host-OS bundle. SDK terms, component alternatives, host-tool dependencies and actual delivery contents require a distribution-specific review. Native aggregate notices are now packaged; further per-object legal attribution review is not claimed.

Independent clean-machine reproduction still needs a separately provisioned machine/operator and access to the pinned tool/source artifacts. Same-rig offline build and hash checks cannot substitute. Production key custody, production signing, release channels and publication/submission remain owner decisions; the existing debug credential is not a production key. No credentials were collected or printed.

A later candidate freeze and exact-artifact release validation remain concrete independent rig work after this packaging change. Physical Android/GrapheneOS, performance/thermal behavior, unseen independent quality and human acceptance remain open as recorded in RELEASE_GAPS.md. No task queue, orchestration/state, unrelated services, branches or main were changed, and nothing was pushed.

## Reproduce or deliberately refresh

With the provisioned local cache and downloaded licensed assets:

    bash tools/android-build.sh
    bash tools/evaluation/check_distribution_inventory.sh

The machine inventory is a committed snapshot. To deliberately recapture after reviewed changes, first run the check's Gradle resolution command (or the checker, which may honestly fail on drift), then:

    python3 tools/distribution/inventory.py

Review and commit that changed inventory before treating verification as current. Recapture is not automatic approval of new terms, dependencies or binaries. Original failure records and historical release manifests must remain unchanged.
