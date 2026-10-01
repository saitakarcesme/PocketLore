# Development candidate: build, install and demonstrate

This is a development debug candidate, not an accepted product, production-signed release or bounty submission. [Task202 evidence](evidence/multi-pack-release-revalidation.md) and [release-v4 manifest](evidence/release-v4/manifest.json) identify the tested APK and both packs; [release gaps](RELEASE_GAPS.md) remain open. Historical release-v1/v2/v3 identities and failures remain preserved and must not be relabeled as this candidate.

## Provision once, then build offline

Use the installed LLMRig toolchain at `/home/isa/Android/atlas-toolchain`, or an equivalent layout selected by `POCKETLORE_TOOLCHAIN`: Temurin JDK 17.0.20.1+1, Gradle 8.13, AGP 8.9.2, SDK platform 35/build-tools 35.0.0, NDK r27c and CMake 3.22.1. Python 3 standard-library tooling and cached Gradle dependencies are required. Initial provisioning requires network; research/inference does not.

```sh
bash tools/runtime/fetch.sh
bash tools/answers/fetch-model.sh
python3 tools/android-knowledge-pack.py --cache downloads/starter-source-cache --download
python3 tools/packs/build_pack.py --download
python3 tools/packs/build_science.py --download
python3 tools/packs/build_travel.py --fetch --install
# If Gradle dependencies are not yet cached:
POCKETLORE_GRADLE_ONLINE=1 bash tools/android-build.sh
```

Downloads must stay in ignored paths. Live pages can change: retain pinned caches; changed bytes must fail instead of silently refreshing locks. The production/demo model is Qwen2.5-0.5B-Instruct Q4_K_M (491,400,032 bytes, SHA `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`). Optional Qwen3 evaluation is not deployment. See [notices](../THIRD_PARTY_NOTICES) and [distribution inventory](distribution-inventory.json) for licenses, immutable revisions, native static inputs and build dependencies.

```sh
python3 tools/android-knowledge-pack.py --cache downloads/starter-source-cache
python3 tools/packs/build_pack.py
python3 tools/packs/build_science.py
bash tools/android-build.sh
bash tools/verify-release.sh
```

The final APK is `android/app/build/outputs/apk/debug/app-debug.apk`, SHA `934147a471c948ea77de51d89663759a2925351c382f5412287535017e67a1f5`, 11,921,193 bytes. API 28 minimum; CPU JNI for ARM64 and x86_64. Actual execution here is API 35 x86_64 emulator only. The manifest pins **all APK entries**, including every DEX, native library, packaged asset, manifest and signature entry, plus full signed APK and external asset hashes. It also binds the refreshed distribution inventory, build recipe source hashes, signer and actual fresh-demo records.

The build uses an ignored project-local development keystore (`downloads/android-debug/debug.keystore`). Keep it locally to reproduce signed bytes; never commit or publish it. A different signing key changes bytes and cannot update an installation signed with the old key. No production key is generated. The scoped finalizer uses pinned D8 without optional incremental class-checksum metadata, normalized ZIP ordering/timestamps, alignment and signing. The verifier executes two forced builds and requires exact full APK equality; this is same-rig/toolchain/key reproduction, not a clean-machine result.

The default release verifier is nondestructive **evidence replay**: exact artifact/source/inventory hashes, permissions and dependency/notice checks, repeated reference/science builds, host retrieval behavior, fresh-demo receipt validation and negative mutations. It does not uninstall or rerun emulator inference. Frozen manifests cannot be overwritten; a later changed candidate needs a new evidence version and actual matching demo, preserving old failures.

## Install and import locally

Use the existing isolated emulator. Do not launch or restart services.

```sh
ADB=/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb
"$ADB" -s emulator-5560 install -r android/app/build/outputs/apk/debug/app-debug.apk
"$ADB" -s emulator-5560 push downloads/answers/model/qwen2.5-0.5b-instruct-q4_k_m.gguf /sdcard/Download/
"$ADB" -s emulator-5560 push downloads/packs/english-reference.plpack /sdcard/Download/
"$ADB" -s emulator-5560 push downloads/science/science-supplement-2026-10-01-v1.plpack /sdcard/Download/
```

Turn airplane mode on and Wi-Fi/mobile data off. In PocketLore, choose **Import local GGUF**, select the local model and confirm its copy size. Wait for **Local model ready**. Use **Import knowledge pack** separately for reference and science. Both remain installed; **Choose collections** selects the searched editions. Expect two active collections, 18 distinct documents and 210 passages. Disable science and Apply: 186 reference passages remain searchable. Restart and verify that selection persists; re-enable science and restart again to restore 210. Imported model and pack hashes remain unchanged across these operations.

The reference archive is 159,327 bytes, SHA `567e9bbbaab896826809ec20f81ae1c4b3f421b011931edae0989d28cfce10ea`; science is 31,183 bytes, SHA `c69f31299553f4a1168eaa0400129fd5e41f21b4354248a0e2b97a87546ff274`. Older pack notices describe single-pack replacement; the app explicitly labels those historical notices and retains collections. Keep space for original Downloads, app copies, import staging and the 256 MiB reserve. Combined catalog admission is bounded; individual-pack admission does not imply arbitrary combined capacity. No physical 12 GB budget claim follows.

## Actual offline demo

1. Start from local saved artifacts with airplane mode shown; verify both active collections and model readiness.
2. Ask **What is magma?** Wait for the actual output and show its route. In the fresh measured run, the production model generated the cited USGS underground/surface definition. Never substitute that text for a new run's actual answer.
3. Inspect the science source dialog, including full edition ID, text, URL, date, rights and source/passage hashes. URLs are provenance labels, not research-time network requests.
4. Disable science, restart the app, and check that magma/lava evidence is excluded. Re-enable it, restart, and check combined evidence again.
5. Explain the current limitation: comparison and multi-source drafts can be incomplete, unsupported or withheld. Source buttons and formatted citations are not support/usefulness proof. The task201 cancellation/reload evidence is separate from this fresh-install demonstration.
6. The travel slice contains 25 bounded central DC POIs. Disclose dated availability, stale hours and unavailable routing; do not promise current conditions.

For a **new destructive project-fixture-only fresh demo**, run `python3 tools/release/multi-pack/fresh.py` on the idle existing emulator. It archives PocketLore fixture app data under ignored `downloads/release-multi-pack/`, uninstalls only PocketLore and its test package, proves empty saved assets, performs actual SAF model and two-pack imports, exercises selection persistence in distinct processes, runs real JNI twice and inspects sources. It leaves both collections enabled; app model loads on next launch. No archived user data is restored or published. This is one new fresh installation; old two-cycle/corruption/cancellation experiments remain historical evidence, not rerun claims.

For physical hardware, use its explicit authorized serial and a separately reviewed install workflow; no physical device is attached here. Production signing/upgrade ownership, independent clean-machine reproduction, full terms review before redistributing build tools, physical Android/GrapheneOS, sustained phone resources/thermals, independent useful-research review and human acceptance remain open. No public artifact upload, bounty submission or main advancement is performed.
