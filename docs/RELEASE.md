# Development candidate: build, install and demonstrate

This is an unsigned-for-production development workflow on LLMRig. The resulting APK is signed with a project-local Android debug certificate, not a stable release key. `tools/android-build.sh` creates the standard development key once at ignored `downloads/android-debug/debug.keystore` and selects it with a scoped Gradle init script. It does not change home-directory or global signing configuration. Retain that ignored key locally to reproduce signed bytes; never commit it. A new key changes APK bytes and cannot update an installation signed by a different key. It is not accepted for bounty submission. [Candidate evidence](evidence/release-preparation.md) and the [release gaps](RELEASE_GAPS.md) identify the exact tested bytes and open gates.

## Provision once with network access

Reuse the installed toolchain at `/home/isa/Android/atlas-toolchain`, or set `POCKETLORE_TOOLCHAIN` to an equivalent layout: Temurin JDK 17, Gradle 8.13, AGP 8.9.2, SDK platform 35/build-tools 35.0.0, NDK r27c and CMake 3.22.1. Python 3 standard-library tooling is used. Compatible cached Gradle/SDK dependencies are required; a fresh machine needs initial downloads. Do not change unrelated projects or global settings.

```sh
bash tools/runtime/fetch.sh
bash tools/answers/fetch-model.sh
python3 tools/android-knowledge-pack.py --cache downloads/starter-source-cache --download
python3 tools/packs/build_pack.py --download
python3 tools/packs/build_travel.py --fetch --install
# Only if Gradle dependencies are not yet cached:
POCKETLORE_GRADLE_ONLINE=1 bash tools/android-build.sh
```

Runtime/model pins are immutable revisions; text blocks and travel revisions are pinned in the source locks. Upstream web pages can change or disappear: retain the original source cache to reproduce a release. Changed content must fail rather than silently refresh pins. The runtime fetch does not include model weights unless requested; the answer-model command above selects the demo's Qwen2.5-0.5B GGUF. Weights and source caches stay under ignored `downloads/` paths. See [notices](../THIRD_PARTY_NOTICES) and [pack provenance](KNOWLEDGE_PACKS.md).

## Offline build and candidate verification

Current evidence: normal and forced builds succeed, but the forced rebuild changes DEX checksum metadata and APK hash. The exact frozen-identity verifier therefore currently fails. This is an unresolved reproducibility gate, not permission to refresh the manifest or claim the rebuilt bytes were freshly tested. See the evidence report for both hashes.

```sh
python3 tools/android-knowledge-pack.py --cache downloads/starter-source-cache
python3 tools/packs/build_pack.py
bash tools/android-build.sh
bash tools/verify-release.sh
```

The APK is `android/app/build/outputs/apk/debug/app-debug.apk`. It supports ARM64 and x86_64, Android API 28 or later; only API 35 x86_64 emulator execution has been measured. The manifest at `docs/evidence/release-v2/manifest.json` records exact demo artifact identities, build-tool versions, native revision, packaged asset/library hashes and source-lock hashes. An independently signed APK will have different bytes; do not silently replace the frozen candidate manifest to conceal this difference.

The verifier requires the frozen demo APK/model/pack and source cache. It checks their hashes, actual APK permissions/ABIs/license entries and Gradle runtime dependencies; rebuilds the pack twice; executes retrieval behavior tests; and validates the fresh-demo evidence with negative tests. Its default is evidence replay, not another emulator uninstall or independent quality evaluation. For the initial freeze after review of raw results, use `python3 tools/release/verify.py --freeze downloads/offline/run-TIMESTAMP`. An existing manifest cannot be overwritten by this command; explicitly version a new evidence directory and update the verifier for a later candidate. Keep previous evidence versions and preserve ignored failed runs. Never use this command to turn a failing run into a pass.

## Install local artifacts

On the existing test emulator (do not launch a second emulator):

```sh
ADB=/home/isa/Android/atlas-toolchain/sdk/platform-tools/adb
"$ADB" -s emulator-5560 install -r android/app/build/outputs/apk/debug/app-debug.apk
"$ADB" -s emulator-5560 push downloads/answers/model/qwen2.5-0.5b-instruct-q4_k_m.gguf /sdcard/Download/
"$ADB" -s emulator-5560 push downloads/packs/english-reference.plpack /sdcard/Download/
```

For a future physical device use its explicit serial after obtaining access; the commands are instructions, not hardware acceptance. Enable airplane mode and turn Wi-Fi/mobile data off. Open PocketLore, choose **Import local GGUF**, select the model in Downloads, confirm the local copy and wait for **Local model ready**. Choose **Import knowledge pack** and select the `.plpack`; wait for 186 passages. Restart the app and confirm both reload. Keep sufficient space for original Downloads, imported copies, temporary staging and the 256 MiB reserve. See the [resource accounting](evidence/resources.md); a small model does not prove the 12 GB device budget under sustained use.

## Live offline demo, with no substituted answers

1. Show airplane mode, the installed pack and model identities. On a fresh install show the explicit no-model fallback before importing the model.
2. Ask `Compare evaporation and condensation`. Wait for the actual output; show whether its route is generated or fallback. Do not paste or script an expected answer into the UI. Inspect a cited source and its date/rights.
3. Ask `What is groundwater?`. If support checking withholds the draft, show the fallback label. This is a product limitation, not a successful explanation.
4. Ask `Does evaporation cure diabetes?` to demonstrate missing-evidence abstention. It is a development safety case, not a medical evaluation.
5. Start another question, wait for generation, then cancel. Restart/recreate the app and show that partial text is discarded and saved assets remain available.
6. Open the travel slice, inspect a DC monument's recorded source date and coordinates, and show stale-hours/unavailable-routing disclosure. Do not claim a live route or current opening status.

The deterministic automated fresh demo uses the bundled eight-passage starter for its inference phase, then imports the 186-passage pack and checks its source UI; manual questions after larger-pack import can produce different outputs. No fixed response is a success oracle. Preserve raw drafts, published routes and failures.

For a new two-cycle clean-install demonstration, run `bash tools/evaluation/check_offline.sh` on the idle existing emulator. This archives PocketLore app data, uninstalls/reinstalls only PocketLore and its test package twice, drives the real local document picker, tests corrupted imports, executes real model answers and cancellation, and leaves a fresh offline imported app. Backups and screenshots remain under `downloads/offline/run-*`; never publish app-data archives. See [offline installation details](OFFLINE_INSTALL.md). Do not run concurrent emulator tests.

## Distribution and acceptance boundaries

Do not distribute the local debug key, model weights without their model terms, private evaluation inputs, app-data backups or private control files. A public signed release, upgrade/key continuity, independent clean-machine reproduction, broader useful-answer review, external rival comparisons, unseen evaluation, physical Android/GrapheneOS testing, sustained resource/thermal measurements and any public demo/submission require separate work. No bounty submission is made by these scripts.
