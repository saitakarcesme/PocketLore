# Clean offline installation and reproducible check

The tested artifact is a debug APK for ARM64 and x86_64. It needs Android API 28 or later and no Google Play Services. Emulator checks establish neither physical Android/GrapheneOS acceptance nor useful-answer quality. Exact tested hashes and results are in [offline installation evidence](evidence/offline-install.md).

## Prepare artifacts while online

Reuse the pinned Android/JDK/Gradle/NDK toolchain in the Android/runtime guides. Provision llama.cpp and the model using the documented immutable source/model pins; fetch the licensed knowledge and travel source caches using their existing scripts. Only provisioning requires network. Do not fetch models during research.

The clean-install check expects these local artifacts:

- `android/app/build/outputs/apk/debug/app-debug.apk`, built by `bash tools/android-build.sh` using Gradle offline mode.
- `downloads/answers/model/qwen2.5-0.5b-instruct-q4_k_m.gguf`: 491,400,032 bytes; SHA-256 `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`. Provision using `tools/answers/fetch-model.sh`; its pin and license are documented in `tools/answers/model.env` and the runtime guide.
- `downloads/packs/english-reference.plpack`: 159,327 bytes; SHA-256 `567e9bbbaab896826809ec20f81ae1c4b3f421b011931edae0989d28cfce10ea`. Reproduce with `python3 tools/packs/build_pack.py` from the pinned source cache.
- The generated bundled DC travel catalog, reproduced offline during the build from the source cache provisioned by `python3 tools/packs/build_travel.py --fetch --install`.

Licenses and source attribution are bundled. Model/pack original files remain in local Downloads after import; copying them into app storage requires additional space plus a 256 MiB reserve. Have enough space for the app data archive and import overlap. A cached build succeeding is not proof that an unprovisioned toolchain can build without initial network access.

## User flow after installing the APK

1. Enable airplane mode and turn Wi-Fi/mobile data off. USB adb can provision the emulator without app research networking.
2. Open PocketLore. A fresh install has the bundled starter/travel data but no saved local model or imported research pack. Questions can show labeled extractive evidence fallback.
3. Choose **Import local GGUF**, select the local GGUF in Android's document picker, and confirm the stated copy size. Wait for **Local model ready**. Restarting the app reloads the saved model.
4. Choose **Import knowledge pack**, select the local `.plpack`, and wait for the pack ID and 186-passage status. Ask about installed sources and use **Inspect** buttons for dates, provenance and source text. Source URLs are labels, not opened web pages.
5. **Cancel inference or import** discards pending generated text. **Cancel pack import** cancels pack staging. After a memory-pressure unload, use **Reload saved model** explicitly. Missing evidence abstains; failed support checks produce labeled fallback rather than a verified generated answer.
6. Uninstalling PocketLore removes app-private copied models/packs and results. Reinstalling does not restore them (`allowBackup=false`); import again from retained local originals. This check does not erase shared Downloads.

## Automated rig check

```sh
bash tools/android-build.sh
bash tools/evaluation/check_offline.sh
```

The second command is intentionally scoped to **PocketLore on existing emulator-5560**. It archives the app's existing files/cache/code_cache into an ignored tar, verifies the archive, then uninstalls/reinstalls PocketLore and its test APK twice. No other package is uninstalled and no emulator or service is launched. It leaves the second fresh installation with locally imported assets and airplane mode on, Wi-Fi/mobile data off. Old app data remains archived; it is not restored automatically. Do not run it concurrently with other work on this emulator.

The checker uses the real document picker for both model and pack, verifies installed hashes, tests corrupt assets and cancelled import confirmation, and exercises real JNI output, live cancellation and Activity recreation. It captures GENERATED/FALLBACK/ABSTAINED routes without treating offline model invocation as answer-quality acceptance. It also tests absent INTERNET permission and a denied loopback socket attempt from the application UID; lack of a listening server is not accepted as permission denial.

Raw logs, UI XML, screenshots, model outputs, exact APK copies and original app-data backups are under `downloads/offline/run-*`. The phase journal describes the last completed stage, so inspect it and preserved outputs after an interrupted run before choosing a new run. Previous run directories are never overwritten. A failure stops the check with available evidence intact. Archive tar contents are app data, not public release artifacts; do not put backups or model weights in Git. Physical hardware, GrapheneOS, packet-level auditing and supported-answer quality remain separate gates.
