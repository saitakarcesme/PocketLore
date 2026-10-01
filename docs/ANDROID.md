# Android starter slice

PocketLore 0.1 is a native Android application with a small installed water-science pack, BM25 passage retrieval, explicit coverage warnings and local source inspection. It has no network permission or Google Play Services dependency. It retrieves evidence rather than generating explanations. This is not yet a bounty-ready research assistant.

## Build and install

Requirements: Linux, JDK 17 or later compatible with Android Gradle Plugin 8.9.2, Gradle 8.13, Android SDK platform 35/build tools 35.0.0, and Python 3. The rig reuses `/home/isa/Android/atlas-toolchain`; set `POCKETLORE_TOOLCHAIN`, `JAVA_HOME`, `ANDROID_HOME` and `GRADLE_USER_HOME` to override paths. No changes to other projects are needed.

Acquire the small public source pages once, during installation:

```sh
python3 tools/android-knowledge-pack.py --cache /path/to/pocketlore-source-cache --download
```

This command extracts only eight selected USGS paragraphs, normalizes whitespace and verifies each against a committed SHA-256 in `android/knowledge-sources.json`. It refuses changed source text. It does not include images or third-party media. The generated TSV and cached HTML are datasets and stay out of Git. Retain the cache to reproduce the pack offline by running the command without `--download`. Packaging only uses the resulting local asset; the app never downloads it.

```sh
tools/android-check.sh
tools/android-build.sh
/path/to/android-sdk/platform-tools/adb -s DEVICE_SERIAL install -r android/app/build/outputs/apk/debug/app-debug.apk
```

The build script uses Gradle offline mode and existing cached dependencies by default. On a fresh developer machine, acquire SDK packages and run `POCKETLORE_GRADLE_ONLINE=1 tools/android-build.sh assembleDebug` once with network access. This is a development debug APK, signed with a local debug key; a stable release signing/install path is still open. Minimum Android is API 28; only API 35 emulator behavior has been exercised. No physical phone or GrapheneOS acceptance is claimed.

Open PocketLore, enter a question, and choose **Find evidence**. Try `Compare evaporation and condensation`. Scroll to **Inspect** to read a passage, its source URL, retrieval date and rights without opening a browser. Unmatched questions produce an explicit no-evidence response. Partial word coverage produces a warning, but this is not a calibrated answerability detector. Ranking is lexical English matching, with no stemming or semantic retrieval yet.

## Knowledge provenance

The manifest links to the [USGS copyright policy](https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits) and the source pages. USGS-authored text is in the U.S. public domain. Only selected textual paragraphs are included; page media and photographs are excluded. No USGS endorsement is implied. The source display accurately labels verbatim paragraphs with normalized whitespace.

## Bootstrap verification

The rig built the APK with Gradle 8.13 / AGP 8.9.2 using the installed toolchain and ran eight retrieval contract checks against the generated pack. An isolated AOSP API 35 x86_64 emulator installed and launched the app, queried the pack with Wi-Fi/mobile data disabled, and displayed source details. Raw logs, UI hierarchy captures, screenshots, package metadata and emulator memory evidence reside privately under `/home/isa/PocketLore-control/evidence/android`.

The UI's elapsed value measures only passage retrieval on the current execution environment. Emulator timing and memory are development diagnostics, never phone inference latency or a 12 GB hardware acceptance result. Broader coverage, inference, synthesis, travel/POI, pack import, larger indexes, model installation, physical hardware and clean offline release installation remain open.

Repeat the emulator smoke flow with `python3 tools/android-smoke.py --serial emulator-5560 --evidence /path/to/private/evidence`. The script only accepts emulator serials; it disables their Wi-Fi and mobile data and checks the installed package has no INTERNET permission.


## Task 010 native runtime update

The APK now also packages a pinned CPU llama.cpp JNI runtime for ARM64 and
x86_64. Optional local GGUF import and an unverified source-excerpt draft panel
are implemented. Before building, provision the pinned source with
`bash tools/runtime/fetch.sh`; add `--model` only for the integration smoke model.
See [runtime reproduction](RUNTIME.md) and [measured native evidence](evidence/native-runtime.md).
The earlier extractive-slice results above do not imply model answer quality or
final native UI acceptance. That task's historical rerun was blocked by hidden `/dev/kvm`; the coordinator later
restored the existing emulator through adb without changing the builder sandbox.


## Task 020 answer flow

The main action is now **Answer offline**. It retrieves evidence, abstains on
missing term coverage, and invokes the imported local model when appropriate.
Generated answers show their model-emitted source IDs; source buttons open the
verbatim passage, URL, acquisition date and rights without opening the network.
Citation or runtime failure displays **Extractive fallback — not a generated
answer**. Cancel discards the partial draft; a new question clears previous output.

The current behavioral acceptance command is `bash tools/android-smoke.sh`, after
`bash tools/answers/fetch-model.sh` provisions the separately pinned integration
model. Reuse the existing `emulator-5560`; do not restart a launcher inside the
managed builder sandbox. The older `tools/android-smoke.py` captures the former
extractive-only UI and is historical, not the current answer acceptance test.
See [answer integration evidence](evidence/answer-integration.md) for measured
results, preserved failures and the narrow limits of the citation checks.

## Task 030 knowledge import

**Import knowledge pack** selects a local `.plpack` through Android's document
picker. The app verifies hashes and provenance before atomically replacing the
active library, then reloads that library after restart. Corrupt imports preserve
the previous library. Source inspection now uses each passage's own agency,
dates and rights. See [pack reproduction and limits](KNOWLEDGE_PACKS.md).
`python3 tools/packs/verify_pack.py` exercises actual emulator import, corruption
rejection, retrieval, restart and source UI; it leaves the reference pack installed.

## Task 040 retrieval index

Source discovery now uses an immutable inverted index with limited English
inflection handling and auditable ranking expansions. Passage text and citation
IDs are unchanged; expansion does not relax the existing answer-coverage gate.
`python3 tools/evaluation/evaluate_retrieval.py` compares the frozen production
baseline with current code and checks real Android parity on the existing
emulator. See [retrieval reproduction](RETRIEVAL.md) and
[measured results and remaining failures](evidence/retrieval.md).

## Synthesis development update

The answer flow now budgets the exact model context, preserves source dates, checks linked claims and exposes final citation spans through the existing source inspector. Comparisons select evidence for each named aspect. Optional synthesis model imports are bounded at 2,048 MiB; actual inference is tested in an isolated emulator fixture, not a new default saved model. See [implementation](SYNTHESIS.md) and [evidence](evidence/synthesis.md) for quality failures and test limits.

For verified fresh installation, local model/pack import and uninstall/reinstall behavior, see [clean offline installation](OFFLINE_INSTALL.md) and its [emulator evidence](evidence/offline-install.md). The audit archives prior app data before uninstalling PocketLore and leaves a fresh imported installation; no physical or GrapheneOS acceptance is implied.
