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
