# Clean offline installation evidence — task 080

Both named checks passed on LLMRig on 2026-10-01: `bash tools/android-build.sh` and `bash tools/evaluation/check_offline.sh`. The check completed **two actual uninstall/fresh-install/local-import cycles** on the existing supervised AOSP x86_64 `emulator-5560`, without restarting the emulator or services. Physical Android and GrapheneOS gates remain open. This is an installation/offline-behavior result, not supported-answer quality acceptance.

[Installation instructions](../OFFLINE_INSTALL.md), [frozen development cases](offline-install/development-cases.md), [standalone build](offline-install/build.log), [full checker log](offline-install/check-first.log), [summary](offline-install/final/summary.json) and [phase journal](offline-install/final/phase.json) describe the work. Cases were committed before implementation in `c66df02`; the checker and test runner were checkpointed in `71617a0` with validation pending. No application implementation change was needed for this task; new work is the clean-install behavioral audit and documentation.

The complete run is `downloads/offline/run-20261001T014640Z`. Exact app/test APKs are archived there and their hashes were independently verified against the summary. Model weights, source packs and backup data remain in ignored paths. All copied public evidence files are hashed in [SHA256SUMS](offline-install/SHA256SUMS). No private holdout/context, runner source/state, global model preferences, unrelated packages or main branch were touched, and nothing was pushed.

## Artifacts and original-data preservation

| Artifact | Bytes | SHA-256 |
| --- | --- | --- |
| Debug app APK, ARM64 + x86_64 | 17,794,384 | `27f9d7824be8b843db7b7238c39c56893005c09f808267cf72e765c87fe0789b` |
| Offline instrumentation APK | 142,534 | `891158514240053f9df72a15b1cd512837fe5768fedebb73e3ca39cdd27c1d6e` |
| Qwen2.5-0.5B-Instruct Q4_K_M model | 491,400,032 | `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db` |
| 186-passage English reference pack | 159,327 | `567e9bbbaab896826809ec20f81ae1c4b3f421b011931edae0989d28cfce10ea` |

The model, pack and runtime pins/licenses are unchanged from their documented provisioning guides. Runtime identity is llama.cpp `bb4caa7540188872173c44d161602d9271386413`, CPU, two threads, context 2,048, one sequence, FP16 KV, one resident session. The check uses the saved 0.5B model, not the separate larger synthesis test model.

Before uninstalling, the original app's files/cache/code_cache were streamed to `original-app-data.tar` in the ignored run directory. The tar was readable, its paths were checked for absolute/traversal names, and its full hash was recorded. It is **2,421,530,112 bytes**, 48 members, SHA-256 `82d58eea098a5fd703d351b5f2257826701a950377ada043ff9524b8f13698d7`; see [backup identity](offline-install/final/backup-identity.json) and [original inventory](offline-install/final/original-files.txt). This preserves prior app-side test assets/results without putting them in Git. It is not an independently tested backup-restore workflow. Old app data was **not** silently restored during either fresh installation.

## Actual lifecycle results

Both fresh installations asserted that neither `files/model.gguf` nor `files/knowledge.plpack` existed. Each loaded the bundled starter, returned explicitly labeled extractive fallback without invoking a model, opened a source dialog, and passed the permission/socket/airplane checks. [Cycle 1 fresh report](offline-install/final/cycle-1-fresh-result.json) contains six assertions and took 908 ms including the test's Activity setup and source action; [cycle 2](offline-install/final/cycle-2-fresh-result.json) took 890 ms. These are one-run instrumentation elapsed times, not cold launch percentiles or phone performance.

In **both cycles**, the existing real SAF UI scripts selected the pinned local GGUF from Downloads, confirmed copying its exact size, checked the imported hash, restarted the process and observed the saved model reload. They entered an actual question and opened its USGS provenance dialog. Model results are preserved for [cycle 1](offline-install/final/cycle-1-model-ui/result.json) and [cycle 2](offline-install/final/cycle-2-model-ui/result.json), with XML and screenshots in those directories.

The first clean installation additionally ran the dedicated real-answer lifecycle instrumentation. Its [raw report](offline-install/final/cycle-1-loaded-result.json) passed 12 assertions in 124,231 ms, including the network controls, actual model invocation, unsupported-evidence abstention, cancellation, Activity recreation, inference reuse and a source-dialog action.

| Frozen public question | Actual route | Model tokens | Total answer ms |
| --- | --- | --- | --- |
| Compare evaporation and condensation | GENERATED | 62 | 26,729.053 |
| What is groundwater? | FALLBACK | 39 | 29,367.449 |
| quasar supernova | ABSTAINED, no model | 0 | 0.074 |
| Does evaporation cure diabetes? | ABSTAINED, no model | 0 | 4.801 |

These labels report the application's publication decisions. The generated comparison combines directions imprecisely and repeats a definition; it is not independently accepted source entailment or useful synthesis. The raw groundwater draft invents an “unobstructed flow” description and was withheld as fallback. Both raw drafts, actual prompts, reasons and visible text are preserved. No canned answer replaced JNI output, no question or model was tuned during this audit, and no quality threshold was relaxed in the existing answer/synthesis checks. The offline checker deliberately requires real invocation and honest routing, not a generated-success count.

After a real streamed token appeared, the test clicked **Cancel current operation** and observed a CANCELLED outcome with the draft discarded; acknowledgement took **50 ms** in this run. It also recreated the Activity during real generation, verified the previous draft did not survive, reloaded the saved model and invoked inference again. This is a tested lifecycle case, not evidence of all possible cancellation races, long-prefill latency or actual OS process-kill recovery.

In both cycles, SAF imported the real English pack, process restart retained its ID/hash, a payload-corrupted ZIP was rejected with the previous hash unchanged, and a Yosemite source dialog showed the imported NPS URL, date and attribution. See [cycle 1 pack results](offline-install/final/cycle-1-pack-ui/result.json), [cycle 2](offline-install/final/cycle-2-pack-ui/result.json), and the [visually inspected source dialog](offline-install/final/cycle-1-pack-ui/source-dialog.png). The check uses actual document-provider selection rather than copying the pack directly into app-private storage.

A separate [SAF model control](offline-install/final/corrupt-model-ui/result.json) cancelled an import confirmation, then selected an eight-byte invalid GGUF, confirmed it, observed **Import failed: Not a GGUF file**, verified the old model hash was unchanged and staging was removed, then restarted and reloaded the valid model. The [rejection screen](offline-install/final/corrupt-model-ui/rejected.png) is preserved and visually inspected. That screen also shows the existing memory-pressure unload message after the picker transition; the saved file survives, and explicit reload/restart is available. Confirmation cancellation here occurs before copying, not mid-copy. Mid-copy failure/cleanup was tested separately in task 070 and is not relabeled as a new UI result.

Both named checks completed without unexpected failure. Intentional corruption failures, rejected raw generation and prior task failures remain preserved; they are not hidden by the overall lifecycle PASS.

## Permission, dependency and offline audit

- The actual APK [permission dump](offline-install/final/permissions.txt) lists only the package and **no requested permissions**, including no INTERNET/network-state permissions. The [manifest tree](offline-install/manifest-tree.txt) also records `allowBackup=false`. No runtime permission grant was added by the test.
- The resolved app `debugRuntimeClasspath` reports **No dependencies** in the actual [Gradle report](offline-install/final/runtime-dependencies.txt). This excludes neither native code nor Android platform APIs; native llama.cpp is included and separately pinned. Google/Maven repositories are build-provisioning sources, not a requirement for Play Services during research. Gradle's unwritable analytics-settings warning is preserved and did not fail the offline build.
- The emulator package queries for [Google Play Services](offline-install/final/package-com.google.android.gms.txt) and [Play Store](offline-install/final/package-com.android.vending.txt) returned empty results. The application flow ran without them installed; this is stronger than merely finding no dependency name in source.
- [Source scanning](offline-install/source-network-audit.json) found no application Java references to the listed networking/client/Play Services/WebView APIs. This bounded scan is supplemental, not proof by itself. The [actual native build flags](offline-install/native-features.txt) disable servers, tools, examples, common library, OpenSSL, RPC, CUDA and Vulkan for both built ABIs; native inference uses CPU.
- Fresh and loaded instrumentation checked denied INTERNET permission and attempted a loopback socket **from the application UID**. Every probe failed with `java.net.SocketException: socket failed: EPERM (Operation not permitted)`. Connection refusal or timeout would fail this control. Loopback was used to avoid sending a research query or contacting an external host; this is permission-enforcement evidence, not packet capture.
- `airplane_mode_on=1`, `wifi_on=0` and `mobile_data=0` were verified before work, after each instrumentation phase and at the end of both cycles; those raw text records are in `offline-install/final/`. Screenshots show the airplane icon. A supplementary [final route query](offline-install/emulator-routes-after.txt) returned no routes. Airplane settings alone are not assumed to cover every emulator transport or prove physical RF behavior.

No research networking is enabled by the APK permissions, and the tested local flows completed with network access denied. Source URLs remain provenance text/inspection labels; the app did not open them. Imports used local Downloads documents while the emulator was offline. This audit does not establish that every third-party document provider behaves offline, or that provider/OS processes cannot have separate networking permissions. No packet capture, kernel tracing or testing of every platform IPC channel was performed. The permission denial, dependency audit and successful offline flows support the bounded claim above.

## Final state and open gates

The emulator is left on its **second fresh installation**, with the pinned 0.5B model and English reference pack imported locally, airplane mode enabled and Wi-Fi/mobile data disabled. [Final installed hashes](offline-install/final-installed-hashes.txt) match the pinned artifacts. Shared Downloads originals and the original app-data tar remain; previous app-private historical test fixtures were not restored. Re-running earlier resource/synthesis tests therefore requires their documented isolated fixture provisioning, rather than assuming stale app-private state survived uninstall.

Remaining gates: physical Android/GrapheneOS install and permissions, real-device radios and sustained performance, clean production signing/distribution, arbitrary provider behavior, actual backup restoration/OS death recovery, packet-level audit if required, and supported useful-answer acceptance. The workflow currently tests a debug APK with `run-as`/instrumentation and a pre-provisioned toolchain/cache; it is not a proof of an offline bootstrap from an empty build machine or a signed public release.
